import textwrap
from collections.abc import Callable, Iterable, Iterator, Sequence
from functools import partial
from re import sub
from typing import Any, Literal, Protocol, TypeVar

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import Directive
from docutils.parsers.rst import Parser as RstParser
from docutils.statemachine import StringList
from docutils.utils import new_document
from jinja2 import Environment, PackageLoader
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import SphinxError
from sphinx.ext.autosummary import autosummary_table, extract_summary
from sphinx.util import logging, rst
from sphinx.util.docutils import switch_source_input

from sphinx_js import ir

from .analyzer_utils import dotted_path
from .ir import (
    Attribute,
    Class,
    DescriptionName,
    DescriptionText,
    Exc,
    Function,
    Interface,
    Module,
    Param,
    Pathname,
    Return,
    TopLevel,
    Type,
    TypeAlias,
    TypeParam,
    TypeXRef,
    TypeXRefInternal,
)
from .jsdoc import Analyzer as JsAnalyzer
from .parsers import PathVisitor
from .suffix_tree import SuffixAmbiguous, SuffixNotFound
from .typedoc import Analyzer as TsAnalyzer

Analyzer = TsAnalyzer | JsAnalyzer

logger = logging.getLogger(__name__)


def sort_attributes_first_then_by_path(obj: TopLevel) -> Any:
    """Return a sort key for IR objects."""
    match obj:
        case Attribute(_):
            idx = 0
        case Function(_):
            idx = 1
        case Class(_) | Interface(_):
            idx = 2

    return idx, obj.path.segments


def _members_to_include_inner(
    members: Iterable[TopLevel],
    include: list[str],
) -> list[TopLevel]:
    """Return the members that should be included (before excludes and
    access specifiers are taken into account).

    This will either be the ones explicitly listed after the
    ``:members:`` option, in that order; all members of the class; or
    listed members with remaining ones inserted at the placeholder "*".

    """
    if not include:
        # Specifying none means listing all.
        return sorted(members, key=sort_attributes_first_then_by_path)
    included_set = set(include)

    # If the special name * is included in the list, include all other
    # members, in sorted order.
    if "*" in included_set:
        star_index = include.index("*")
        sorted_not_included_members = sorted(
            (m for m in members if m.name not in included_set),
            key=sort_attributes_first_then_by_path,
        )
        not_included = [m.name for m in sorted_not_included_members]
        include = include[:star_index] + not_included + include[star_index + 1 :]
        included_set.update(not_included)

    # Even if there are 2 members with the same short name (e.g. a
    # static member and an instance one), keep them both. This
    # prefiltering step should make the below sort less horrible, even
    # though I'm calling index().
    included_members = [m for m in members if m.name in included_set]
    # sort()'s stability should keep same-named members in the order
    # JSDoc spits them out in.
    included_members.sort(key=lambda m: include.index(m.name))
    return included_members


def members_to_include(
    members: Iterable[TopLevel],
    include: list[str],
    exclude: list[str],
    should_include_private: bool,
) -> Iterator[TopLevel]:
    for member in _members_to_include_inner(members, include):
        if member.name in exclude:
            continue
        if not should_include_private and getattr(member, "is_private", False):
            continue
        yield member


def unwrapped(text: str) -> str:
    """Return the text with line wrapping removed."""
    return sub(r"[ \t]*[\r\n]+[ \t]*", " ", text)


def render_description(description: ir.Description) -> str:
    """Construct a single comment string from a fancy object."""
    if isinstance(description, str):
        return description
    content = []
    prev = ""
    for s in description:
        if isinstance(s, DescriptionName):
            prev = s.text
            content.append(prev + "\n")
            continue
        if isinstance(s, DescriptionText):
            prev = s.text
            content.append(prev)
            continue
        # code
        if s.code.startswith("```") and s.code.count("\n") >= 1:
            # A code pen
            first_line, rest = s.code.split("\n", 1)
            rest = rest.removesuffix("```")
            code_type = first_line.removeprefix("```")
            start = f".. code-block:: {code_type}\n\n"
            codeblock = textwrap.indent(rest, " " * 4)
            end = "\n\n"
            content.append("\n" + start + codeblock + end)
            continue

        if s.code.startswith("``"):
            # Sphinx-style escaped, leave it alone.
            content.append(s.code)
            continue
        if prev.endswith(":"):
            # A sphinx role, leave it alone
            content.append(s.code)
            continue

        if prev.endswith(" ") and not s.code.endswith(">`"):
            # Used single uptick with code, put double upticks
            content.append(f"`{s.code}`")
            continue
        content.append(s.code)
    return "".join(content)


R = TypeVar("R", bound="Renderer")


class HasDepPath(Protocol):
    deppath: str | None


class Renderer:
    _type_xref_formatter: Callable[[TypeXRef], str]
    # We turn the <span class="sphinx_js-type"> in the analyzer tests because it
    # makes a big mess.
    _add_span: bool
    _partial_path: list[str]
    _explicit_formal_params: str
    _content: list[str] | StringList
    _options: dict[str, Any]

    def _parse_path(self, arg: str) -> None:
        # content, arguments, options, app: all need to be accessible to
        # template_vars, so we bring them in on construction and stow them away
        # on the instance so calls to template_vars don't need to concern
        # themselves with what it needs.
        (
            self._partial_path,
            self._explicit_formal_params,
        ) = PathVisitor().parse(arg)

    def __init__(
        self,
        directive: Directive,
        app: Sphinx,
        arguments: list[str],
        content: list[str] | StringList | None = None,
        options: dict[str, Any] | None = None,
    ):
        self._add_span = True
        # Fix crash when calling eval_rst with CommonMarkParser:
        if not hasattr(directive.state.document.settings, "tab_width"):
            directive.state.document.settings.tab_width = 8

        self._directive = directive
        self._app = app
        self._set_type_xref_formatter(app.config.ts_type_xref_formatter)
        self._parse_path(arguments[0])
        self._content = content or StringList()
        self._options = options or {}

    @classmethod
    def from_directive(cls: type[R], directive: Directive, app: Sphinx) -> R:
        """Return one of these whose state is all derived from a directive.

        This is suitable for top-level calls but not for when a renderer is
        being called from a different renderer, lest content and such from the
        outer directive be duplicated in the inner directive.

        :arg directive: The associated Sphinx directive
        :arg app: The Sphinx global app object. Some methods need this.

        """
        return cls(
            directive,
            app,
            arguments=directive.arguments,
            content=directive.content,
            options=directive.options,
        )

    def _set_type_xref_formatter(
        self, formatter: Callable[[Config, TypeXRef], str] | None
    ) -> None:
        if formatter:
            self._type_xref_formatter = partial(formatter, self._app.config)
            return

        def default_type_xref_formatter(xref: TypeXRef) -> str:
            return xref.name

        self._type_xref_formatter = default_type_xref_formatter

    def get_object(self) -> HasDepPath:
        raise NotImplementedError

    def dependencies(self) -> set[str]:
        """Return a set of path(s) to the file(s) that the IR object
        rendered by this renderer is from.  Each path is absolute or
        relative to `root_for_relative_js_paths`.

        """
        try:
            obj = self.get_object()
            if obj.deppath:
                return set([obj.deppath])
        except SphinxError as exc:
            logger.exception("Exception while retrieving paths for IR object: %s" % exc)
        return set([])

    def rst_nodes(self) -> list[Node]:
        raise NotImplementedError


class JsRenderer(Renderer):
    """Abstract superclass for renderers of various sphinx-js directives

    Provides an inversion-of-control framework for rendering and bridges us
    from the hidden, closed-over JsDirective subclasses to top-level classes
    that can see and use each other. Handles parsing of a single, all-consuming
    argument that consists of a JS/TS entity reference and an optional formal
    parameter list.

    """

    _renderer_type: Literal["function", "class", "attribute"]
    _template: str

    def _template_vars(self, name: str, obj: TopLevel) -> dict[str, Any]:
        raise NotImplementedError

    def lookup_object(
        self,
        partial_path: list[str],
        renderer_type: Literal["function", "class", "attribute"] = "attribute",
    ) -> TopLevel:
        try:
            analyzer: Analyzer = (
                self._app._sphinxjs_analyzer  # type:ignore[attr-defined]
            )
            obj = analyzer.get_object(partial_path, renderer_type)
            return obj
        except SuffixNotFound as exc:
            raise SphinxError(
                'No documentation was found for object "%s" or any path ending with that.'
                % "".join(exc.segments)
            )
        except SuffixAmbiguous as exc:
            raise SphinxError(
                'More than one object matches the path suffix "{}". Candidate paths have these segments in front: {}'.format(
                    "".join(exc.segments), exc.next_possible_keys
                )
            )

    def get_object(self) -> TopLevel:
        """Return the IR object rendered by this renderer."""
        return self.lookup_object(self._partial_path, self._renderer_type)

    def rst_nodes(self) -> list[Node]:
        """Render into RST nodes a thing shaped like a function, having a name
        and arguments.

        Fill in args, docstrings, and info fields from stored JSDoc output.

        """
        obj = self.get_object()
        rst = self.rst(
            self._partial_path, obj, use_short_name="short-name" in self._options
        )

        # Parse the RST into docutils nodes with a fresh doc, and return
        # them.
        #
        # Not sure if passing the settings from the "real" doc is the right
        # thing to do here:
        doc = new_document(
            f"{obj.filename}:{obj.path}({obj.line})",
            settings=self._directive.state.document.settings,
        )
        RstParser().parse(rst, doc)
        return doc.children

    def rst_for(self, obj: TopLevel) -> str:
        renderer_class: type
        match obj:
            case Attribute(_) | TypeAlias(_):
                renderer_class = AutoAttributeRenderer
            case Function(_):
                renderer_class = AutoFunctionRenderer
            case Class(_) | Interface(_):
                renderer_class = AutoClassRenderer
            case _:
                raise RuntimeError("This shouldn't happen...")
        renderer = renderer_class(
            self._directive, self._app, arguments=["dummy"], options={"members": ["*"]}
        )
        return renderer.rst([obj.name], obj, use_short_name=False)

    def rst(
        self, partial_path: list[str], obj: TopLevel, use_short_name: bool = False
    ) -> str:
        """Return rendered RST about an entity with the given name and IR
        object."""
        dotted_name = partial_path[-1] if use_short_name else dotted_path(partial_path)

        # Render to RST using Jinja:
        env = Environment(loader=PackageLoader("sphinx_js", "templates"))
        template = env.get_template(self._template)
        result = template.render(**self._template_vars(dotted_name, obj))
        result = result.strip()
        had_blank = False
        lines = []
        for line in result.splitlines():
            if line.strip():
                had_blank = False
                lines.append(line.rstrip())
            elif not had_blank:
                lines.append("")
                had_blank = True
        result = "\n".join(lines) + "\n"
        return result

    def _type_params(self, obj: Function | Class | TypeAlias | Interface) -> str:
        if not obj.type_params:
            return ""
        return "<{}>".format(", ".join(tp.name for tp in obj.type_params))

    def _formal_params(self, obj: Function) -> str:
        """Return the JS function params, looking first to any explicit params
        written into the directive and falling back to those in comments or JS
        code.

        Return a ReST-escaped string ready for substitution into the template.

        """
        if self._explicit_formal_params:
            return self._explicit_formal_params

        formals = []
        used_names = set()

        for param in obj.params:
            # Turn "@param p2.subProperty" into just p2. We wouldn't want to
            # add subproperties to the flat formal param list:
            name = param.name.split(".")[0]

            # Add '...' to the parameter name if it's a variadic argument
            if param.is_variadic:
                name = "..." + name

            if name not in used_names:
                # We don't rst.escape() anything here, because, empirically,
                # the js:function directive (or maybe directive params in
                # general) automatically ignores markup constructs in its
                # parameter (though not its contents).
                formals.append(
                    name if not param.has_default else f"{name}={param.default}"
                )
                used_names.add(name)

        return "({})".format(", ".join(formals))

    def render_type(self, type: Type, escape: bool = False, bold: bool = True) -> str:
        if not type:
            return ""
        if isinstance(type, str):
            if bold:
                type = "**%s**" % type
            if escape:
                type = rst.escape(type)
            return type
        it = iter(type)

        def strs() -> Iterator[str]:
            for elem in it:
                if isinstance(elem, str):
                    yield elem
                else:
                    xref.append(elem)
                    return

        res = []
        while True:
            xref: list[TypeXRef] = []
            s = "".join(strs())
            if escape:
                s = rst.escape(s)
            if s:
                res.append(s)
            if not xref:
                break
            res.append(self.render_xref(xref[0], escape))

        joined = r"\ ".join(res)
        if self._add_span:
            return f":sphinx_js_type:`{rst.escape(joined)}`"
        return joined

    def render_xref(self, s: TypeXRef, escape: bool = False) -> str:
        obj = None
        if isinstance(s, TypeXRefInternal):
            try:
                obj = self.lookup_object(s.path)
                # Stick the kind on the xref so that the formatter will know what
                # xref role to emit. I'm not sure how to compute this earlier. It's
                # convenient to do it here.
                s.kind = type(obj).__name__.lower()
            except SphinxError:
                # This sometimes happens on the code path in
                # convertReferenceToXRef when we generate an xref internal from
                # a symbolId. That code path is probably entirely wrong.
                # TODO: fix and add test coverage.
                pass
        result = self._type_xref_formatter(s)
        if escape:
            result = rst.escape(result)
        return result

    def _return_formatter(self, return_: Return) -> tuple[list[str], str]:
        """Derive heads and tail from ``@returns`` blocks."""
        tail = []
        if return_.type:
            tail.append(self.render_type(return_.type, escape=False))
        if return_.description:
            tail.append(render_description(return_.description))
        return ["returns"], " -- ".join(tail)

    def _type_param_formatter(self, tparam: TypeParam) -> tuple[list[str], str] | None:
        v = tparam.name
        descr = render_description(tparam.description)
        if tparam.extends:
            descr += " (extends " + self.render_type(tparam.extends) + ")"
        heads = ["typeparam", v]
        return heads, descr

    def _param_formatter(self, param: Param) -> tuple[list[str], str] | None:
        """Derive heads and tail from ``@param`` blocks."""
        if not param.type and not param.description:
            # There's nothing worth saying about this param.
            return None
        heads = ["param"]
        heads.append(param.name)

        tail = render_description(param.description)
        return heads, tail

    def _param_type_formatter(self, param: Param) -> tuple[list[str], str] | None:
        """Generate types for function parameters specified in field."""
        if not param.type:
            return None
        heads = ["type", param.name]
        tail = self.render_type(param.type)
        return heads, tail

    def _exception_formatter(self, exception: Exc) -> tuple[list[str], str]:
        """Derive heads and tail from ``@throws`` blocks."""
        heads = ["throws"]
        if exception.type:
            heads.append(self.render_type(exception.type, bold=False))
        tail = render_description(exception.description)
        return heads, tail

    def _fields(self, obj: TopLevel) -> Iterator[tuple[list[str], str]]:
        """Return an iterable of "info fields" to be included in the directive,
        like params, return values, and exceptions.

        Each field consists of a tuple ``(heads, tail)``, where heads are
        words that go between colons (as in ``:param string href:``) and
        tail comes after.

        """
        FIELD_TYPES: list[tuple[str, Callable[[Any], tuple[list[str], str] | None]]] = [
            ("type_params", self._type_param_formatter),
            ("params", self._param_formatter),
            ("params", self._param_type_formatter),
            ("properties", self._param_formatter),
            ("properties", self._param_type_formatter),
            ("exceptions", self._exception_formatter),
            ("returns", self._return_formatter),
        ]
        for collection_attr, callback in FIELD_TYPES:
            for instance in getattr(obj, collection_attr, []):
                result = callback(instance)
                if not result:
                    continue
                heads, tail = result
                # If there are line breaks in the tail, the RST parser will
                # end the field list prematurely.
                #
                # TODO: Instead, indent multi-line tails juuuust right, and
                # we can enjoy block-level constructs within tails:
                # https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#field-lists.
                yield [rst.escape(h) for h in heads], unwrapped(tail)


class AutoFunctionRenderer(JsRenderer):
    _template = "function.rst"
    _renderer_type = "function"

    def _template_vars(self, name: str, obj: Function) -> dict[str, Any]:  # type: ignore[override]
        deprecated = obj.deprecated
        if not isinstance(deprecated, bool):
            deprecated = render_description(deprecated)
        return dict(
            name=name,
            type_params=self._type_params(obj),
            params=self._formal_params(obj),
            fields=self._fields(obj),
            description=render_description(obj.description),
            examples=[render_description(x) for x in obj.examples],
            deprecated=deprecated,
            is_optional=obj.is_optional,
            is_static=obj.is_static,
            is_async=obj.is_async,
            see_also=obj.see_alsos,
            content="\n".join(self._content),
        )


class AutoClassRenderer(JsRenderer):
    _template = "class.rst"
    _renderer_type = "class"

    def _template_vars(self, name: str, obj: Class | Interface) -> dict[str, Any]:  # type: ignore[override]
        # TODO: At the moment, we pull most fields (params, returns,
        # exceptions, etc.) off the constructor only. We could pull them off
        # the class itself too in the future.
        if not isinstance(obj, Class) or not obj.constructor_:
            # One way or another, it has no constructor, so make a blank one to
            # keep from repeating this long test for every constructor-using
            # line in the dict() call:
            constructor = Function(
                name="",
                path=Pathname([]),
                filename="",
                deppath=None,
                description="",
                line=0,
                deprecated=False,
                examples=[],
                see_alsos=[],
                properties=[],
                exported_from=None,
                is_abstract=False,
                is_optional=False,
                is_static=False,
                is_async=False,
                is_private=False,
                type_params=obj.type_params,
                params=[],
                exceptions=[],
                returns=[],
            )
        else:
            constructor = obj.constructor_
        return dict(
            name=name,
            params=self._formal_params(constructor),
            type_params=self._type_params(obj),
            fields=self._fields(constructor),
            examples=[render_description(ex) for ex in constructor.examples],
            deprecated=constructor.deprecated,
            see_also=constructor.see_alsos,
            exported_from=obj.exported_from,
            class_comment=render_description(obj.description),
            is_abstract=isinstance(obj, Class) and obj.is_abstract,
            interfaces=[self.render_type(x) for x in obj.interfaces]
            if isinstance(obj, Class)
            else [],
            is_interface=isinstance(obj, Interface),
            supers=[self.render_type(x) for x in obj.supers],
            constructor_comment=render_description(constructor.description),
            content="\n".join(self._content),
            members=self._members_of(
                obj,
                include=self._options["members"],
                exclude=self._options.get("exclude-members", set()),
                should_include_private="private-members" in self._options,
            )
            if "members" in self._options
            else "",
        )

    def _members_of(
        self,
        obj: Class | Interface,
        include: list[str],
        exclude: list[str],
        should_include_private: bool,
    ) -> str:
        """Return RST describing the members of a given class.

        :arg obj Class: The class we're documenting
        :arg include: List of names of members to include. If empty, include
            all.
        :arg exclude: Set of names of members to exclude
        :arg should_include_private: Whether to include private members

        """
        return "\n\n".join(
            self.rst_for(member)
            for member in members_to_include(
                obj.members, include, exclude, should_include_private
            )
        )


class AutoAttributeRenderer(JsRenderer):
    _template = "attribute.rst"
    _renderer_type = "attribute"

    def _template_vars(self, name: str, obj: Attribute | TypeAlias) -> dict[str, Any]:  # type: ignore[override]
        is_optional = False
        ty = self.render_type(obj.type)
        if isinstance(obj, Attribute):
            is_optional = obj.is_optional
            if obj.readonly:
                ty = "readonly " + ty
        type_params = ""
        is_type_alias = isinstance(obj, TypeAlias)
        fields: Iterator[tuple[list[str], str]] = iter([])
        if isinstance(obj, TypeAlias):
            type_params = self._type_params(obj)
            fields = self._fields(obj)
        return dict(
            name=name,
            is_type_alias=is_type_alias,
            type_params=type_params,
            fields=fields,
            description=render_description(obj.description),
            deprecated=obj.deprecated,
            is_optional=is_optional,
            see_also=obj.see_alsos,
            examples=[render_description(ex) for ex in obj.examples],
            type=ty,
            content="\n".join(self._content),
        )


_SECTION_ORDER = ["type_aliases", "attributes", "functions", "interfaces", "classes"]


class AutoModuleRenderer(JsRenderer):
    def _parse_path(self, arg: str) -> None:
        # content, arguments, options, app: all need to be accessible to
        # template_vars, so we bring them in on construction and stow them away
        # on the instance so calls to template_vars don't need to concern
        # themselves with what it needs.
        self._explicit_formal_params = ""
        self._partial_path = arg.split("/")

    def get_object(self) -> Module:  # type:ignore[override]
        analyzer: Analyzer = self._app._sphinxjs_analyzer  # type:ignore[attr-defined]
        assert isinstance(analyzer, TsAnalyzer)
        return analyzer._modules_by_path.get(self._partial_path)

    def rst_for_group(self, objects: Iterable[TopLevel]) -> list[str]:
        return [
            self.rst_for(obj)
            for obj in objects
            if "@omitFromAutoModule" not in obj.modifier_tags
        ]

    def rst(  # type:ignore[override]
        self,
        partial_path: list[str],
        obj: Module,
        use_short_name: bool = False,
    ) -> str:
        rst: list[Sequence[str]] = []
        rst.append([f".. js:module:: {''.join(partial_path)}"])
        for group_name in _SECTION_ORDER:
            rst.append(self.rst_for_group(getattr(obj, group_name)))
        return "\n\n".join(["\n\n".join(r) for r in rst if r])


class AutoSummaryRenderer(Renderer):
    def _parse_path(self, arg: str) -> None:
        # content, arguments, options, app: all need to be accessible to
        # template_vars, so we bring them in on construction and stow them away
        # on the instance so calls to template_vars don't need to concern
        # themselves with what it needs.
        self._explicit_formal_params = ""
        self._partial_path = arg.split("/")

    def get_object(self) -> Module:
        analyzer: Analyzer = self._app._sphinxjs_analyzer  # type:ignore[attr-defined]
        assert isinstance(analyzer, TsAnalyzer)
        return analyzer._modules_by_path.get(self._partial_path)

    def rst_nodes(self) -> list[Node]:
        module = self.get_object()
        pkgname = "".join(self._partial_path)

        result: list[Node] = []
        for group_name in _SECTION_ORDER:
            group_objects = getattr(module, group_name)
            if not group_objects:
                continue
            n = nodes.container()
            n += self.format_heading(group_name.replace("_", " ").title() + ":")
            table_items = self.get_summary_table(pkgname, group_objects)
            n += self.format_table(table_items)
            n["classes"] += ["jssummarytable", group_name]
            result.append(n)
        return result

    def format_heading(self, text: str) -> Node:
        """Make a section heading. This corresponds to the rst: "**Heading:**"
        autodocsumm uses headings like that, so this will match that style.
        """
        heading = nodes.paragraph("")
        strong = nodes.strong("")
        strong.append(nodes.Text(text))
        heading.append(strong)
        return heading

    def extract_summary(self, descr: str) -> str:
        """Wrapper around autosummary extract_summary that is easier to use.
        It seems like colons need escaping for some reason.
        """
        colon_esc = "esccolon\\\xafhoa:"
        # extract_summary seems to have trouble if there are Sphinx
        # directives in descr
        descr, _, _ = descr.partition("\n..")
        return extract_summary(
            [descr.replace(":", colon_esc)], self._directive.state.document
        ).replace(colon_esc, ":")

    def get_sig(self, obj: TopLevel) -> str:
        """If the object is a function, get its signature (as figured by JsDoc)"""
        if isinstance(obj, ir.Function):
            return AutoFunctionRenderer(
                self._directive, self._app, arguments=["dummy"]
            )._formal_params(obj)
        else:
            return ""

    def get_summary_row(self, pkgname: str, obj: TopLevel) -> tuple[str, str, str]:
        """Get the summary table row for obj.

        The output is designed to be input to format_table. The link name
        needs to be set up so that :any:`link_name` makes a link to the
        actual API docs for this object.
        """
        display_name = obj.name
        prefix = "**async** " if getattr(obj, "is_async", False) else ""
        qualifier = "any"
        link_name = pkgname + "." + display_name
        main = f"{prefix}:{qualifier}:`{display_name} <{link_name}>`"
        if slink := obj.block_tags.get("summaryLink"):
            main = render_description(slink[0])
        sig = self.get_sig(obj)
        summary = self.extract_summary(render_description(obj.description))
        return (main, sig, summary)

    def get_summary_table(
        self, pkgname: str, group: Iterable[TopLevel]
    ) -> list[tuple[str, str, str]]:
        """Get the data for a summary tget_summary_tableable. Return value
        is set up to be an argument of format_table.
        """
        return [self.get_summary_row(pkgname, obj) for obj in group]

    # This following method is copied almost verbatim from autosummary
    # (where it is called get_table).
    #
    # We have to change the value of one string: qualifier = 'obj   ==>
    # qualifier = 'any'
    # https://github.com/sphinx-doc/sphinx/blob/6.0.x/sphinx/ext/autosummary/__init__.py#L375
    def format_table(self, items: list[tuple[str, str, str]]) -> list[Node]:
        """Generate a proper list of table nodes for autosummary:: directive.

        *items* is a list produced by :meth:`get_items`.
        """
        table_spec = addnodes.tabular_col_spec()
        table_spec["spec"] = r"\X{1}{2}\X{1}{2}"

        table = autosummary_table("")
        real_table = nodes.table("", classes=["longtable"])
        table.append(real_table)
        group = nodes.tgroup("", cols=2)
        real_table.append(group)
        group.append(nodes.colspec("", colwidth=10))
        group.append(nodes.colspec("", colwidth=90))
        body = nodes.tbody("")
        group.append(body)

        def append_row(column_texts: list[tuple[str, str]]) -> None:
            row = nodes.row("")
            source, line = self._directive.state_machine.get_source_and_line()
            for [text, cls] in column_texts:
                node = nodes.paragraph("")
                vl = StringList()
                assert source
                assert line
                vl.append(text, "%s:%d:<autosummary>" % (source, line))
                with switch_source_input(self._directive.state, vl):
                    self._directive.state.nested_parse(vl, 0, node)
                    try:
                        if isinstance(node[0], nodes.paragraph):
                            node = node[0]
                    except IndexError:
                        pass
                    entry = nodes.entry("", node)
                    entry["classes"].append(cls)
                    row.append(entry)
            body.append(row)

        for name, sig, summary in items:
            # The body of this loop is changed from copied code.
            if "nosignatures" not in self._options:
                sig = rst.escape(sig)
                if sig:
                    sig = f"**{sig}**"
                name = rf"{name}\ {sig}"
            append_row([(name, "name"), (summary, "summary")])

        return [table_spec, table]
