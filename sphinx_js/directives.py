"""These are the actual Sphinx directives we provide, but they are skeletal.

The real meat is in their parallel renderer classes, in renderers.py. The split
is due to the unfortunate trick we need here of having functions return the
directive classes after providing them the ``app`` symbol, where we store the
JSDoc output, via closure. The renderer classes, able to be top-level classes,
can access each other and collaborate.

"""
import re
from collections.abc import Iterable
from functools import cache
from os.path import join, relpath
from typing import Any, cast

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import Directive
from docutils.parsers.rst import Parser as RstParser
from docutils.parsers.rst.directives import flag
from docutils.utils import new_document
from sphinx import addnodes
from sphinx.addnodes import desc_signature
from sphinx.application import Sphinx
from sphinx.domains import ObjType, javascript
from sphinx.domains.javascript import (
    JavaScriptDomain,
    JSCallable,
    JSConstructor,
    JSObject,
    JSXRefRole,
)
from sphinx.locale import _
from sphinx.util.docfields import GroupedField, TypedField
from sphinx.writers.html5 import HTML5Translator
from sphinx.writers.latex import LaTeXTranslator
from sphinx.writers.text import TextTranslator

from .renderers import (
    AutoAttributeRenderer,
    AutoClassRenderer,
    AutoFunctionRenderer,
    AutoModuleRenderer,
    AutoSummaryRenderer,
    Renderer,
)


def unescape(escaped: str) -> str:
    # For some reason the string we get has a bunch of null bytes in it??
    # Remove them...
    escaped = escaped.replace("\x00", "")
    # For some reason the extra slash before spaces gets lost between the .rst
    # source and when this directive is called. So don't replace "\<space>" =>
    # "<space>"
    return re.sub(r"\\([^ ])", r"\1", escaped)


def _members_to_exclude(arg: str | None) -> set[str]:
    """Return a set of members to exclude given a comma-delim list of them.

    Exclude none if none are passed. This differs from autodocs' behavior,
    which excludes all. That seemed useless to me.

    """
    return set(a.strip() for a in (arg or "").split(","))


def sphinx_js_type_role(role, rawtext, text, lineno, inliner, options=None, content=None):  # type: ignore[no-untyped-def]
    """
    The body should be escaped rst. This renders its body as rst and wraps the
    result in <span class="sphinx_js-type"> </span>
    """
    unescaped = unescape(text)
    doc = new_document("", inliner.document.settings)
    RstParser().parse(unescaped, doc)
    n = nodes.inline(text)
    n["classes"].append("sphinx_js-type")
    n += doc.children[0].children
    return [n], []


class JSXrefMixin:
    def make_xref(
        self,
        rolename: Any,
        domain: Any,
        target: Any,
        innernode: Any = nodes.emphasis,
        contnode: Any = None,
        env: Any = None,
        inliner: Any = None,
        location: Any = None,
    ) -> Any:
        # Set inliner to None just like the PythonXrefMixin does so the
        # xref doesn't get rendered as a function.
        return super().make_xref(  # type:ignore[misc]
            rolename,
            domain,
            target,
            innernode,
            contnode,
            env,
            inliner=None,
            location=None,
        )


class JSTypedField(JSXrefMixin, TypedField):
    pass


class JSGroupedField(JSXrefMixin, GroupedField):
    pass


# Cache this to guarantee it only runs once.
@cache
def fix_js_make_xref() -> None:
    """Monkeypatch to fix sphinx.domains.javascript TypedField and GroupedField

    Fixes https://github.com/sphinx-doc/sphinx/issues/11021

    """

    # Replace javascript module
    javascript.TypedField = JSTypedField  # type:ignore[attr-defined]
    javascript.GroupedField = JSGroupedField  # type:ignore[attr-defined]

    # Fix the one place TypedField and GroupedField are used in the javascript
    # module
    javascript.JSCallable.doc_field_types = [
        JSTypedField(
            "arguments",
            label=_("Arguments"),
            names=("argument", "arg", "parameter", "param"),
            typerolename="func",
            typenames=("paramtype", "type"),
        ),
        JSGroupedField(
            "errors",
            label=_("Throws"),
            rolename="func",
            names=("throws",),
            can_collapse=True,
        ),
    ] + javascript.JSCallable.doc_field_types[2:]


# Cache this to guarantee it only runs once.
@cache
def fix_staticfunction_objtype() -> None:
    """Override js:function directive with one that understands static and async
    prefixes
    """

    JavaScriptDomain.directives["function"] = JSFunction


@cache
def add_type_param_field_to_directives() -> None:
    typeparam_field = JSGroupedField(
        "typeparam",
        label="Type parameters",
        rolename="func",
        names=("typeparam",),
        can_collapse=True,
    )

    JSCallable.doc_field_types.insert(0, typeparam_field)
    JSConstructor.doc_field_types.insert(0, typeparam_field)


class JsDirective(Directive):
    """Abstract directive which knows how to pull things out of our IR"""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {"short-name": flag}

    def _run(self, renderer_class: type[Renderer], app: Sphinx) -> list[Node]:
        renderer = renderer_class.from_directive(self, app)
        note_dependencies(app, renderer.dependencies())
        return renderer.rst_nodes()


class JsDirectiveWithChildren(JsDirective):
    option_spec = JsDirective.option_spec.copy()
    option_spec.update(
        {
            "members": lambda members: (
                [m.strip() for m in members.split(",")] if members else []
            ),
            "exclude-members": _members_to_exclude,
            "private-members": flag,
        }
    )


def note_dependencies(app: Sphinx, dependencies: Iterable[str]) -> None:
    """Note dependencies of current document.

    :arg app: Sphinx application object
    :arg dependencies: iterable of filename strings relative to root_for_relative_paths
    """
    for fn in dependencies:
        # Dependencies in the IR are relative to `root_for_relative_paths`, itself
        # relative to the configuration directory.
        analyzer = app._sphinxjs_analyzer  # type:ignore[attr-defined]
        abs = join(analyzer._base_dir, fn)
        # Sphinx dependencies are relative to the source directory.
        rel = relpath(abs, app.srcdir)
        app.env.note_dependency(rel)


def auto_function_directive_bound_to_app(app: Sphinx) -> type[Directive]:
    class AutoFunctionDirective(JsDirective):
        """js:autofunction directive, which spits out a js:function directive

        Takes a single argument which is a JS function name combined with an
        optional formal parameter list, all mashed together in a single string.

        """

        def run(self) -> list[Node]:
            return self._run(AutoFunctionRenderer, app)

    return AutoFunctionDirective


def auto_class_directive_bound_to_app(app: Sphinx) -> type[Directive]:
    class AutoClassDirective(JsDirectiveWithChildren):
        """js:autoclass directive, which spits out a js:class directive

        Takes a single argument which is a JS class name combined with an
        optional formal parameter list for the constructor, all mashed together
        in a single string.

        """

        def run(self) -> list[Node]:
            return self._run(AutoClassRenderer, app)

    return AutoClassDirective


def auto_attribute_directive_bound_to_app(app: Sphinx) -> type[Directive]:
    class AutoAttributeDirective(JsDirective):
        """js:autoattribute directive, which spits out a js:attribute directive

        Takes a single argument which is a JS attribute name.

        """

        def run(self) -> list[Node]:
            return self._run(AutoAttributeRenderer, app)

    return AutoAttributeDirective


class desc_js_type_parameter_list(nodes.Part, nodes.Inline, nodes.FixedTextElement):
    """Node for a javascript type parameter list.

    Unlike normal parameter lists, we use angle braces <> as the braces. Based
    on sphinx.addnodes.desc_type_parameter_list
    """

    child_text_separator = ", "

    def astext(self) -> str:
        return f"<{nodes.FixedTextElement.astext(self)}>"


def html5_visit_desc_js_type_parameter_list(
    self: HTML5Translator, node: nodes.Element
) -> None:
    """Define the html/text rendering for desc_js_type_parameter_list. Based on
    sphinx.writers.html5.visit_desc_type_parameter_list
    """
    if hasattr(self, "_visit_sig_parameter_list"):
        # Sphinx 7
        return self._visit_sig_parameter_list(node, addnodes.desc_parameter, "<", ">")
    # Sphinx <7
    self.body.append('<span class="sig-paren">&lt;</span>')
    self.first_param = 1
    self.optional_param_level = 0
    # How many required parameters are left.
    self.required_params_left = sum(
        [isinstance(c, addnodes.desc_parameter) for c in node.children]
    )
    self.param_separator = node.child_text_separator


def html5_depart_desc_js_type_parameter_list(
    self: HTML5Translator, node: nodes.Element
) -> None:
    """Define the html/text rendering for desc_js_type_parameter_list. Based on
    sphinx.writers.html5.depart_desc_type_parameter_list
    """
    if hasattr(self, "_depart_sig_parameter_list"):
        # Sphinx 7
        return self._depart_sig_parameter_list(node)
    # Sphinx <7
    self.body.append('<span class="sig-paren">&gt;</span>')


def text_visit_desc_js_type_parameter_list(
    self: TextTranslator, node: nodes.Element
) -> None:
    if hasattr(self, "_visit_sig_parameter_list"):
        # Sphinx 7
        return self._visit_sig_parameter_list(node, addnodes.desc_parameter, "<", ">")
    # Sphinx <7
    self.add_text("<")
    self.first_param = 1  # type:ignore[attr-defined]


def text_depart_desc_js_type_parameter_list(
    self: TextTranslator, node: nodes.Element
) -> None:
    if hasattr(self, "_depart_sig_parameter_list"):
        # Sphinx 7
        return self._depart_sig_parameter_list(node)
    # Sphinx <7
    self.add_text(">")


def latex_visit_desc_type_parameter_list(
    self: LaTeXTranslator, node: nodes.Element
) -> None:
    pass


def latex_depart_desc_type_parameter_list(
    self: LaTeXTranslator, node: nodes.Element
) -> None:
    pass


def add_param_list_to_signode(signode: desc_signature, params: str) -> None:
    paramlist = desc_js_type_parameter_list()
    for arg in params.split(","):
        paramlist += addnodes.desc_parameter("", "", addnodes.desc_sig_name(arg, arg))
    signode += paramlist


def handle_typeparams_for_signature(
    self: JSObject, sig: str, signode: desc_signature, *, keep_callsig: bool
) -> tuple[str, str]:
    """Generic function to handle type params in the sig line for interfaces,
    classes, and functions.

    For interfaces and classes we don't prefer the look with parentheses so we
    also remove them (by setting keep_callsig to False).
    """
    typeparams = None
    if "<" in sig and ">" in sig:
        base, _, rest = sig.partition("<")
        typeparams, _, params = rest.partition(">")
        sig = base + params
    res = JSCallable.handle_signature(cast(JSCallable, self), sig, signode)
    sig = sig.strip()
    lastchild = None
    # Check for call signature, if present take it off
    if signode.children[-1].astext().endswith(")"):
        lastchild = signode.children[-1]
        signode.remove(lastchild)
    if typeparams:
        add_param_list_to_signode(signode, typeparams)
    # if we took off a call signature and we want to keep it put it back.
    if keep_callsig and lastchild:
        signode += lastchild
    return res


class JSFunction(JSCallable):
    """Variant of JSCallable that can take static/async prefixes"""

    option_spec = {
        **JSCallable.option_spec,
        "static": flag,
        "async": flag,
    }

    def get_display_prefix(
        self,
    ) -> list[Any]:
        result = []
        for name in ["static", "async"]:
            if name in self.options:
                result.extend(
                    [
                        addnodes.desc_sig_keyword(name, name),
                        addnodes.desc_sig_space(),
                    ]
                )
        return result

    def handle_signature(self, sig: str, signode: desc_signature) -> tuple[str, str]:
        return handle_typeparams_for_signature(self, sig, signode, keep_callsig=True)


class JSInterface(JSCallable):
    """An interface directive.

    Based on sphinx.domains.javascript.JSConstructor.
    """

    allow_nesting = True

    def get_display_prefix(self) -> list[Node]:
        return [
            addnodes.desc_sig_keyword("interface", "interface"),
            addnodes.desc_sig_space(),
        ]

    def handle_signature(self, sig: str, signode: desc_signature) -> tuple[str, str]:
        return handle_typeparams_for_signature(self, sig, signode, keep_callsig=False)


class JSTypeAlias(JSObject):
    doc_field_types = [
        JSGroupedField(
            "typeparam",
            label="Type parameters",
            names=("typeparam",),
            can_collapse=True,
        )
    ]

    def handle_signature(self, sig: str, signode: desc_signature) -> tuple[str, str]:
        return handle_typeparams_for_signature(self, sig, signode, keep_callsig=False)


class JSClass(JSConstructor):
    def handle_signature(self, sig: str, signode: desc_signature) -> tuple[str, str]:
        return handle_typeparams_for_signature(self, sig, signode, keep_callsig=True)


@cache
def patch_JsObject_get_index_text() -> None:
    """Add our additional object types to the index"""
    orig_get_index_text = JSObject.get_index_text

    def patched_get_index_text(
        self: JSObject, objectname: str, name_obj: tuple[str, str]
    ) -> str:
        name, obj = name_obj
        if self.objtype == "interface":
            return _("%s() (interface)") % name
        return orig_get_index_text(self, objectname, name_obj)

    JSObject.get_index_text = patched_get_index_text  # type:ignore[method-assign]


def auto_module_directive_bound_to_app(app: Sphinx) -> type[Directive]:
    class AutoModuleDirective(JsDirectiveWithChildren):
        required_arguments = 1

        def run(self) -> list[Node]:
            return self._run(AutoModuleRenderer, app)

    return AutoModuleDirective


def auto_summary_directive_bound_to_app(app: Sphinx) -> type[Directive]:
    class JsDocSummary(JsDirective):
        required_arguments = 1

        def run(self) -> list[Node]:
            return self._run(AutoSummaryRenderer, app)

    return JsDocSummary


def add_directives(app: Sphinx) -> None:
    fix_js_make_xref()
    fix_staticfunction_objtype()
    add_type_param_field_to_directives()
    patch_JsObject_get_index_text()
    app.add_role("sphinx_js_type", sphinx_js_type_role)
    app.add_directive_to_domain(
        "js", "autofunction", auto_function_directive_bound_to_app(app)
    )
    app.add_directive_to_domain(
        "js", "autoclass", auto_class_directive_bound_to_app(app)
    )
    app.add_directive_to_domain(
        "js", "autoattribute", auto_attribute_directive_bound_to_app(app)
    )
    app.add_directive_to_domain(
        "js", "automodule", auto_module_directive_bound_to_app(app)
    )
    app.add_directive_to_domain(
        "js", "autosummary", auto_summary_directive_bound_to_app(app)
    )
    app.add_directive_to_domain("js", "class", JSClass)
    app.add_role_to_domain("js", "class", JSXRefRole())
    JavaScriptDomain.object_types["interface"] = ObjType(_("interface"), "interface")
    app.add_directive_to_domain("js", "interface", JSInterface)
    app.add_role_to_domain("js", "interface", JSXRefRole())
    JavaScriptDomain.object_types["typealias"] = ObjType(_("type alias"), "typealias")
    app.add_directive_to_domain("js", "typealias", JSTypeAlias)
    app.add_role_to_domain("js", "typealias", JSXRefRole())
    app.add_node(
        desc_js_type_parameter_list,
        html=(
            html5_visit_desc_js_type_parameter_list,
            html5_depart_desc_js_type_parameter_list,
        ),
        text=(
            text_visit_desc_js_type_parameter_list,
            text_depart_desc_js_type_parameter_list,
        ),
        latex=(
            latex_visit_desc_type_parameter_list,
            latex_depart_desc_type_parameter_list,
        ),
    )
