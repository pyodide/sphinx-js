"""Intermediate representation that JS and TypeScript are transformed to for
use by the rest of sphinx-js

This results from my former inability to review any but the most trivial
TypeScript PRs due to jsdoc's JSON output format being undocumented, often
surprising, and occasionally changing.

This IR is not intended to be a lossless representation of either jsdoc's or
typedoc's output. Nor is it meant to generalize to other uses like static
analysis. Ideally, it provides the minimum information necessary to render our
Sphinx templates about JS and TS entities. Any expansion or generalization of
the IR should be driven by needs of those templates and the (minimal) logic
around them. The complexity of doing otherwise has no payback.

I was conflicted about introducing an additional representation, since a
multiplicity of representations incurs conversion complexity costs at a
superlinear rate. However, I think it is essential complexity here. The
potentially simpler approach would have been to let the RST template vars
required by our handful of directives be the IR. However, we still would have
wanted to factor out formatting like the joining of types with "|" and the
unwrapping of comments, making another representation inevitable. Therefore,
let's at least have a well-documented one and one slightly more likely to
survive template changes.

This has to match js/ir.ts
"""

from collections.abc import Callable, Sequence
from typing import Any, Literal, ParamSpec, TypeVar

import cattrs
from attrs import Factory, define, field

from .analyzer_utils import dotted_path


@define
class TypeXRefIntrinsic:
    name: str
    type: Literal["intrinsic"] = "intrinsic"


@define
class TypeXRefInternal:
    name: str
    path: list[str]
    type: Literal["internal"] = "internal"
    kind: str | None = None


@define
class TypeXRefExternal:
    name: str
    package: str
    # TODO: use snake case for these like for everything else
    sourcefilename: str | None
    qualifiedName: str | None
    type: Literal["external"] = "external"


TypeXRef = TypeXRefExternal | TypeXRefInternal | TypeXRefIntrinsic


@define
class DescriptionName:
    text: str
    type: Literal["name"] = "name"


@define
class DescriptionText:
    text: str
    type: Literal["text"] = "text"


@define
class DescriptionCode:
    code: str
    type: Literal["code"] = "code"


DescriptionItem = DescriptionName | DescriptionText | DescriptionCode

Description = str | Sequence[DescriptionItem]

#: Human-readable type of a value. None if we don't know the type.
Type = str | list[str | TypeXRef] | None


class Pathname:
    """A partial or full path to a language entity.

    Example: ``['./', 'dir/', 'dir/', 'file.', 'object.', 'object#', 'object']``

    """

    def __init__(self, segments: Sequence[str]):
        self.segments = segments

    def __str__(self) -> str:
        return "".join(self.segments)

    def __repr__(self) -> str:
        return "Pathname(%r)" % self.segments

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.segments == other.segments

    def dotted(self) -> str:
        return dotted_path(self.segments)


@define
class _NoDefault:
    """A conspicuous no-default value that will show up in templates to help
    troubleshoot code paths that grab ``Param.default`` without checking
    ``Param.has_default`` first."""

    _no_default: bool = True

    def __repr__(self) -> str:
        return "NO_DEFAULT"


NO_DEFAULT = _NoDefault()


@define(slots=False)
class _Member:
    """An IR object that is a member of another, as a method is a member of a
    class or interface"""

    #: Whether this member is required to be provided by a subclass of a class
    #: or implementor of an interface
    is_abstract: bool
    #: Whether this member is optional in the TypeScript sense of being allowed
    #: on but not required of an object to conform to a type
    is_optional: bool
    #: Whether this member can be accessed on the container itself rather than
    #: just on instances of it
    is_static: bool
    #: Is a private member of a class or, at least in JSDoc, a @namespace:
    is_private: bool


@define
class TypeParam:
    name: str
    extends: Type
    description: Description = ""


@define
class Param:
    """A parameter of either a function or (in the case of TS, which has
    classes parametrized by type) a class."""

    name: str
    #: The description text (like all other description fields in the IR)
    #: retains any line breaks and subsequent indentation whitespace that were
    #: in the source code.
    description: Description = ""
    has_default: bool = False
    is_variadic: bool = False
    type: Type | None = None
    #: Return the default value of this parameter, string-formatted so it can
    #: be immediately suffixed to an equal sign in a formal param list. For
    #: example, the number 6 becomes the string "6" to create ``foo=6``. If
    # : has_default=True, this must be set.
    default: str | _NoDefault = NO_DEFAULT

    def __attrs_post_init__(self) -> None:
        if self.has_default and self.default is NO_DEFAULT:
            raise ValueError(
                "Tried to construct a Param with has_default=True but without `default` specified."
            )


@define
class Exc:
    """One kind of exception that can be raised by a function"""

    #: The type of exception can have
    type: Type
    description: Description


@define
class Return:
    """One kind of thing a function can return"""

    #: The type this kind of return value can have
    type: Type
    description: Description


@define
class Module:
    filename: str
    deppath: str | None
    path: Pathname
    line: int
    attributes: list["TopLevel"] = Factory(list)
    functions: list["Function"] = Factory(list)
    classes: list["Class"] = Factory(list)
    interfaces: list["Interface"] = Factory(list)
    type_aliases: list["TypeAlias"] = Factory(list)


@define(slots=False)
class TopLevel:
    """A language object with an independent existence

    A TopLevel entity is a potentially strong entity in the database sense; one
    of these can exist on its own and not merely as a datum attached to another
    entity. For example, Returns do not qualify, since they cannot exist
    without a parent Function. And, though a given Attribute may be attached to
    a Class, Attributes can also exist top-level in a module.

    These are also complex entities: the sorts of thing with the potential to
    include the kinds of subentities referenced by the fields defined herein.

    """

    #: The short name of the object, regardless of whether it's a class or
    #: function or typedef or param.
    #:
    #: This is usually the same as the last item of path.segments but not
    #: always. For example, in JSDoc Attributes defined with @property, name is
    #: defined but path is empty. This was a shortcut and could be corrected at
    #: some point. If it is, we can stop storing name as a separate field. Also
    #: TypeScript constructors are named "new WhateverClass". They should
    #: instead be called "constructor".
    name: str
    #: The namepath-like unambiguous identifier of the object, e.g. ``['./',
    #: 'dir/', 'dir/', 'file/', 'object.', 'object#', 'object']``
    path: Pathname
    #: The basename of the file the object is from, e.g. "foo.js"
    filename: str
    #: The path to the dependency, i.e., the file the object is from.
    #: Either absolute or relative to the root_for_relative_js_paths.
    deppath: str | None
    #: The human-readable description of the entity or '' if absent
    description: Description
    modifier_tags: list[str] = field(kw_only=True, factory=list)
    block_tags: dict[str, Sequence[Description]] = field(kw_only=True, factory=dict)
    #: Line number where the object (excluding any prefixing comment) begins
    line: int | None
    #: Explanation of the deprecation (which implies True) or True or False
    deprecated: Description | bool
    #: List of preformatted textual examples
    examples: Sequence[Description]
    #: List of paths to also refer the reader to
    see_alsos: list[str]
    #: Explicitly documented sub-properties of the object, a la jsdoc's
    #: @properties
    properties: list["Attribute"]
    #: None if not exported for use by outside code. Otherwise, the Sphinx
    #: dotted path to the module it is exported from, e.g. 'foo.bar'
    exported_from: Pathname | None
    #: Descriminator
    kind: str = field(kw_only=True)
    #: Is it a root documentation item? Used by autosummary.
    documentation_root: bool = field(kw_only=True, default=False)


@define(slots=False)
class Attribute(TopLevel, _Member):
    """A property of an object

    These are called attributes to match up with Sphinx's autoattribute
    directive which is used to display them.

    """

    #: The type this property's value can have
    type: Type
    readonly: bool = False
    kind: Literal["attribute"] = "attribute"


@define
class Function(TopLevel, _Member):
    """A function or a method of a class"""

    is_async: bool
    params: list[Param]
    exceptions: list[Exc]
    returns: list[Return]
    type_params: list[TypeParam] = Factory(list)
    kind: Literal["function"] = "function"


@define
class _MembersAndSupers:
    """An IR object that can contain members and extend other types"""

    #: Class members, concretized ahead of time for simplicity. (Otherwise,
    #: we'd have to pass the doclets_by_class map in and keep it around, along
    #: with a callable that would create the member IRs from it on demand.)
    #: Does not include the default constructor.
    members: list[Function | Attribute]
    #: Objects this one extends: for example, superclasses of a class or
    #: superinterfaces of an interface
    supers: list[Type]


@define
class Interface(TopLevel, _MembersAndSupers):
    """An interface, a la TypeScript"""

    type_params: list[TypeParam] = Factory(list)
    kind: Literal["interface"] = "interface"


@define
class Class(TopLevel, _MembersAndSupers):
    #: The default constructor for this class. Absent if the constructor is
    #: inherited.
    constructor_: Function | None
    #: Whether this is an abstract class
    is_abstract: bool
    #: Interfaces this class implements
    interfaces: list[Type]
    # There's room here for additional fields like @example on the class doclet
    # itself. These are supported and extracted by jsdoc, but they end up in an
    # `undocumented: True` doclet and so are presently filtered out. But we do
    # have the space to include them someday.
    type_params: list[TypeParam] = Factory(list)
    kind: Literal["class"] = "class"


@define
class TypeAlias(TopLevel):
    type: Type
    type_params: list[TypeParam] = Factory(list)
    kind: Literal["typeAlias"] = "typeAlias"


TopLevelUnion = Class | Interface | Function | Attribute | TypeAlias

# Now make a serializer/deserializer.
# TODO: Add tests to make sure that serialization and deserialization are a
# round trip.


def json_to_ir(json: Any) -> list[TopLevelUnion]:
    """Structure raw json into a list of TopLevels"""
    return converter.structure(json, list[TopLevelUnion])


converter = cattrs.Converter()
# We just serialize Pathname as a list
converter.register_unstructure_hook(Pathname, lambda x: x.segments)
converter.register_structure_hook(Pathname, lambda x, _: Pathname(x))

# Nothing else needs custom serialization. Add a decorator to register custom
# deserializers for the various unions.

P = ParamSpec("P")
T = TypeVar("T")


def _structure(*types: Any) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def dec(func: Callable[P, T]) -> Callable[P, T]:
        for ty in types:
            converter.register_structure_hook(ty, func)
        return func

    return dec


@_structure(Description, Description | bool)
def structure_description(x: Any, _: Any) -> Description | bool:
    if isinstance(x, str):
        return x
    if isinstance(x, bool):
        return x
    return converter.structure(x, list[DescriptionItem])


def get_type_literal(t: type[DescriptionText]) -> str:
    """Take the "blah" from the type annotation in

    type: Literal["blah"]
    """
    return t.__annotations__["type"].__args__[0]  # type:ignore[no-any-return]


description_type_map = {
    get_type_literal(t): t for t in [DescriptionName, DescriptionText, DescriptionCode]
}


@_structure(DescriptionItem)
def structure_description_item(x: Any, _: Any) -> DescriptionItem:
    # Look up the expected type of x from the value of x["type"]
    return converter.structure(x, description_type_map[x["type"]])


@_structure(Type)
def structure_type(x: Any, _: Any) -> Type:
    if isinstance(x, str) or x is None:
        return x
    return converter.structure(x, list[str | TypeXRef])


@_structure(str | TypeXRef)
def structure_str_or_xref(x: Any, _: Any) -> Type:
    if isinstance(x, str):
        return x
    return converter.structure(x, TypeXRef)  # type:ignore[arg-type]


@_structure(str | _NoDefault)
def structure_str_or_nodefault(x: Any, _: Any) -> str | _NoDefault:
    if isinstance(x, str):
        return x
    return NO_DEFAULT
