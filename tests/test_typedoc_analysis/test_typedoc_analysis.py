from copy import copy, deepcopy

import pytest

from sphinx_js.ir import (
    Attribute,
    Class,
    Description,
    DescriptionCode,
    DescriptionText,
    Function,
    Interface,
    Param,
    Pathname,
    Return,
    Type,
    TypeAlias,
    TypeParam,
    TypeXRef,
    TypeXRefExternal,
    TypeXRefInternal,
    TypeXRefIntrinsic,
)
from sphinx_js.renderers import AutoClassRenderer, AutoFunctionRenderer
from tests.testing import NO_MATCH, TypeDocAnalyzerTestCase, TypeDocTestCase, dict_where


def join_type(t: Type) -> str:
    if not t:
        return ""
    if isinstance(t, str):
        return t
    return "".join(e.name if isinstance(e, TypeXRef) else e for e in t)


def join_description(t: Description) -> str:
    if not t:
        return ""
    if isinstance(t, str):
        return t
    return "".join(e.code if isinstance(e, DescriptionCode) else e.text for e in t)


class TestPathSegments(TypeDocTestCase):
    """Make sure ``make_path_segments() `` works on all its manifold cases."""

    files = ["subdir/pathSegments.ts"]

    def commented_object(self, comment, **kwargs):
        """Return the object from ``json`` having the given comment short-text."""
        comment = [DescriptionText(text=comment)]
        return dict_where(self.json, description=comment, **kwargs)

    def commented_object_path(self, comment, **kwargs):
        """Return the path segments of the object with the given comment."""
        obj = self.commented_object(comment, **kwargs)
        if obj is NO_MATCH:
            raise RuntimeError(f'No object found with the comment "{comment}".')
        return obj.path.segments  # type:ignore[attr-defined]

    def test_class(self):
        assert self.commented_object_path("Foo class") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo",
        ]

    def test_instance_property(self):
        assert self.commented_object_path("Num instance var") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo#",
            "numInstanceVar",
        ]

    def test_static_property(self):
        assert self.commented_object_path("Static member") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo.",
            "staticMember",
        ]

    def test_interface_property(self):
        assert self.commented_object_path("Interface property") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Face.",
            "moof",
        ]

    def test_weird_name(self):
        """Make sure property names that themselves contain delimiter chars
        like #./~ get their pathnames built correctly."""
        assert self.commented_object_path("Weird var") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo#",
            "weird#Var",
        ]

    def test_getter(self):
        assert self.commented_object_path("Getter") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo#",
            "getter",
        ]

    def test_setter(self):
        assert self.commented_object_path("Setter") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo#",
            "setter",
        ]

    def test_method(self):
        assert self.commented_object_path("Method") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo#",
            "someMethod",
        ]

    def test_static_method(self):
        """Since ``make_path_segments()`` looks at the inner Call Signature,
        make sure the flags (which determine staticness) are on the node we
        expect."""
        assert self.commented_object_path("Static method") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo.",
            "staticMethod",
        ]

    def test_constructor(self):
        # Pass the kindString so we're sure to find the signature (which is
        # what convert_nodes() passes to make_path_segments()) rather than the
        # constructor itself. They both have the same comments.
        #
        # Constructors get a #. They aren't static; they can see ``this``.
        assert self.commented_object_path("Constructor") == [
            "./",
            "subdir/",
            "pathSegments.",
            "Foo#",
            "constructor",
        ]

    def test_function(self):
        assert self.commented_object_path("Function") == [
            "./",
            "subdir/",
            "pathSegments.",
            "foo",
        ]

    @pytest.mark.xfail(
        reason="Test approach doesn't work anymore and broken by typedoc v0.20"
    )
    def test_relative_paths(self):
        """Make sure FS path segments are emitted if ``base_dir`` doesn't
        directly contain the code."""
        assert self.commented_object_path("Function") == [
            "./",
            "test_typedoc_analysis/",
            "source/",
            "subdir/",
            "pathSegments.",
            "foo",
        ]

    def test_namespaced_var(self):
        """Make sure namespaces get into the path segments."""
        assert self.commented_object_path("Namespaced number") == [
            "./",
            "subdir/",
            "pathSegments.",
            "SomeSpace.",
            "spacedNumber",
        ]


class TestConvertNode(TypeDocAnalyzerTestCase):
    """Test all the branches of ``convert_node()`` by analyzing every kind of
    TypeDoc JSON object."""

    files = ["nodes.ts", "exports.ts"]

    def test_class1(self):
        """Test that superclasses, implemented interfaces, abstractness, and
        nonexistent constructors, members, and top-level attrs are surfaced."""
        # Make sure is_abstract is sometimes false:
        super = self.analyzer.get_object(["Superclass"])
        assert isinstance(super, Class)
        assert not super.is_abstract

        # There should be a single member representing method():
        (method,) = super.members
        assert isinstance(method, Function)
        assert method.name == "method"

        # Class-specific attrs:
        subclass = self.analyzer.get_object(["EmptySubclass"])
        assert isinstance(subclass, Class)
        assert subclass.constructor_ is None
        assert subclass.is_abstract
        assert subclass.interfaces == [
            [TypeXRefInternal("Interface", ["./", "nodes.", "Interface"])]
        ]

        subclass2 = self.analyzer.get_object(["EmptySubclass2"])
        assert isinstance(subclass2, Class)
        assert join_type(subclass2.supers[0]) == "Promise<number>"

        # _MembersAndSupers attrs:
        assert subclass.supers == [
            [TypeXRefInternal("Superclass", ["./", "nodes.", "Superclass"])]
        ]
        assert subclass.members == []

        # TopLevel attrs. This should cover them for other kinds of objs as
        # well (if node structures are the same across object kinds), since we
        # have the filling of them factored out.
        assert subclass.name == "EmptySubclass"
        assert subclass.path == Pathname(["./", "nodes.", "EmptySubclass"])
        assert subclass.description == [DescriptionText("An empty subclass")]
        assert subclass.deprecated is False
        assert subclass.examples == []
        assert subclass.see_alsos == []
        assert subclass.properties == []
        assert subclass.exported_from == Pathname(["./", "nodes"])

    def test_interface(self):
        """Test that interfaces get indexed and have their supers exposed.

        Members and top-level properties should be covered in test_class()
        assuming node structure is the same as for classes.

        """
        interface = self.analyzer.get_object(["Interface"])
        assert isinstance(interface, Interface)
        assert interface.supers == [
            [TypeXRefInternal("SuperInterface", ["./", "nodes.", "SuperInterface"])]
        ]

    def test_interface_function_member(self):
        """Make sure function-like properties are understood."""
        obj = self.analyzer.get_object(["InterfaceWithMembers"])
        assert isinstance(obj, Interface)
        prop = obj.members[0]
        assert isinstance(prop, Function)
        assert prop.name == "callableProperty"

    def test_variable(self):
        """Make sure top-level consts and vars are found."""
        const = self.analyzer.get_object(["topLevelConst"])
        assert isinstance(const, Attribute)
        assert const.type == ["3"]

    def test_function(self):
        """Make sure Functions, Params, and Returns are built properly for
        top-level functions.

        This covers a few simple function typing cases as well.

        """
        func = self.analyzer.get_object(["func"])
        assert isinstance(func, Function)
        assert func.params == [
            Param(
                name="a",
                description=[DescriptionText("Some number")],
                has_default=True,
                is_variadic=False,
                type=[TypeXRefIntrinsic("number")],
                default="1",
            ),
            Param(
                name="b",
                description=[DescriptionText("Some strings")],
                has_default=False,
                is_variadic=True,
                type=[TypeXRefIntrinsic("string"), "[]"],
            ),
        ]
        assert func.exceptions == []
        assert func.returns == [
            Return(
                type=[TypeXRefIntrinsic("number")],
                description=[DescriptionText("The best number")],
            )
        ]

    def test_constructor(self):
        """Make sure constructors get attached to classes and analyzed into
        Functions.

        The rest of their analysis should share a code path with functions.

        """
        cls = self.analyzer.get_object(["ClassWithProperties"])
        assert isinstance(cls, Class)
        assert isinstance(cls.constructor_, Function)

    def test_properties(self):
        """Make sure properties are hooked onto classes and expose their
        flags."""
        cls = self.analyzer.get_object(["ClassWithProperties"])
        assert isinstance(cls, Class)
        # The properties are on the class and are Attributes:
        assert (
            len(
                [
                    m
                    for m in cls.members
                    if isinstance(m, Attribute)
                    and m.name
                    in ["someStatic", "someOptional", "somePrivate", "someNormal"]
                ]
            )
            == 4
        )

        # The unique things about properties (over and above Variables) are set
        # right:
        def get_prop(delim: str, val: str) -> Attribute:
            res = self.analyzer.get_object(["ClassWithProperties" + delim, val])
            assert isinstance(res, Attribute)
            return res

        assert get_prop(".", "someStatic").is_static
        assert get_prop("#", "someOptional").is_optional
        assert get_prop("#", "somePrivate").is_private
        normal_property = get_prop("#", "someNormal")
        assert (
            not normal_property.is_optional
            and not normal_property.is_static
            and not normal_property.is_abstract
            and not normal_property.is_private
        )

    def test_getter(self):
        """Test that we represent getters as Attributes and find their return
        types."""
        getter = self.analyzer.get_object(["gettable"])
        assert isinstance(getter, Attribute)
        assert getter.type == [TypeXRefIntrinsic("number")]

    def test_setter(self):
        """Test that we represent setters as Attributes and find the type of
        their 1 param."""
        setter = self.analyzer.get_object(["settable"])
        assert isinstance(setter, Attribute)
        assert setter.type == [TypeXRefIntrinsic("string")]

    def test_type_alias(self):
        alias = self.analyzer.get_object(["TestTypeAlias"])
        assert isinstance(alias, TypeAlias)
        assert join_description(alias.description) == "A super special type alias"
        assert join_type(alias.type) == "1 | 2 | T"
        assert alias.type_params == [TypeParam(name="T", extends=None, description=[])]


class TestTypeName(TypeDocAnalyzerTestCase):
    """Make sure our rendering of TypeScript types into text works."""

    files = ["types.ts"]

    def test_basic(self):
        """Test intrinsic types."""
        for obj_name, type_name in [
            ("bool", "boolean"),
            ("num", "number"),
            ("str", "string"),
            ("array", "number[]"),
            ("genericArray", "number[]"),
            ("tuple", "[string, number]"),
            ("color", "Color"),
            ("unk", "unknown"),
            ("whatever", "any"),
            ("voidy", "void"),
            ("undef", "undefined"),
            ("nully", "null"),
            ("nev", "never"),
            ("obj", "object"),
            ("sym", "symbol"),
        ]:
            obj = self.analyzer.get_object([obj_name])
            assert isinstance(obj, Attribute)
            assert join_type(obj.type) == type_name

    def test_named_interface(self):
        """Make sure interfaces can be referenced by name."""
        obj = self.analyzer.get_object(["interfacer"])
        assert isinstance(obj, Function)
        assert obj.params[0].type == [
            TypeXRefInternal(name="Interface", path=["./", "types.", "Interface"])
        ]

    def test_interface_readonly_member(self):
        """Make sure the readonly modifier doesn't keep us from computing the
        type of a property."""
        obj = self.analyzer.get_object(["Interface"])
        assert isinstance(obj, Interface)
        read_only_num = obj.members[0]
        assert isinstance(read_only_num, Attribute)
        assert read_only_num.name == "readOnlyNum"
        assert read_only_num.type == [TypeXRefIntrinsic("number")]

    def test_array(self):
        """Make sure array types are rendered correctly.

        As a bonus, make sure we grab the first signature of an overloaded
        function.

        """
        obj = self.analyzer.get_object(["overload"])
        assert isinstance(obj, Function)
        assert obj.params[0].type == [TypeXRefIntrinsic("string"), "[]"]

    def test_literal_types(self):
        """Make sure a thing of a named literal type has that type name
        attached."""
        obj = self.analyzer.get_object(["certainNumbers"])
        assert isinstance(obj, Attribute)
        assert obj.type == [
            TypeXRefInternal(
                name="CertainNumbers", path=["./", "types.", "CertainNumbers"]
            )
        ]

    def test_unions(self):
        """Make sure unions get rendered properly."""
        obj = self.analyzer.get_object(["union"])
        assert isinstance(obj, Attribute)
        assert obj.type == [
            TypeXRefIntrinsic("number"),
            " | ",
            TypeXRefIntrinsic("string"),
            " | ",
            TypeXRefInternal(name="Color", path=["./", "types.", "Color"]),
        ]

    def test_intersection(self):
        obj = self.analyzer.get_object(["intersection"])
        assert isinstance(obj, Attribute)
        assert obj.type == [
            TypeXRefInternal(name="FooHaver", path=["./", "types.", "FooHaver"]),
            " & ",
            TypeXRefInternal(name="BarHaver", path=["./", "types.", "BarHaver"]),
        ]

    def test_generic_function(self):
        """Make sure type params appear in args and return types."""
        obj = self.analyzer.get_object(["aryIdentity"])
        assert isinstance(obj, Function)
        T = ["T", "[]"]
        assert obj.params[0].type == T
        assert obj.returns[0].type == T

    def test_generic_member(self):
        """Make sure members of a class have their type params taken into
        account."""
        obj = self.analyzer.get_object(["add"])
        assert isinstance(obj, Function)
        assert obj.name == "add"
        assert len(obj.params) == 2
        T = ["T"]
        assert obj.params[0].type == T
        assert obj.params[1].type == T
        assert obj.returns[0].type == T

    def test_constrained_by_interface(self):
        """Make sure ``extends SomeInterface`` constraints are rendered."""
        obj = self.analyzer.get_object(["constrainedIdentity"])
        assert isinstance(obj, Function)
        T = ["T"]
        assert obj.params[0].type == T
        assert obj.returns[0].type == T
        assert obj.type_params[0] == TypeParam(
            name="T",
            extends=[
                TypeXRefInternal(name="Lengthwise", path=["./", "types.", "Lengthwise"])
            ],
            description=[DescriptionText("the identity type")],
        )

    def test_constrained_by_key(self):
        """Make sure ``extends keyof SomeObject`` constraints are rendered."""
        obj = self.analyzer.get_object(["getProperty"])
        assert isinstance(obj, Function)
        assert obj.params[0].name == "obj"
        assert join_type(obj.params[0].type) == "T"
        assert join_type(obj.params[1].type) == "K"
        # TODO?
        # assert obj.returns[0].type == "<TODO: not implemented>"
        assert obj.type_params[0] == TypeParam(
            name="T",
            extends=None,
            description=[DescriptionText("The type of the object")],
        )
        tp = copy(obj.type_params[1])
        tp.extends = join_type(tp.extends)
        assert tp == TypeParam(
            name="K",
            extends="string | number | symbol",
            description=[DescriptionText("The type of the key")],
        )

        # TODO: this part maybe belongs in a unit test for the renderer or something
        a = AutoFunctionRenderer.__new__(AutoFunctionRenderer)
        a._add_span = False
        a._set_type_xref_formatter(None)
        a._explicit_formal_params = None  # type:ignore[attr-defined]
        a._content = []
        rst = a.rst([obj.name], obj)
        rst = rst.replace("\\", "").replace("  ", " ")
        assert ":typeparam T: The type of the object" in rst
        assert (
            ":typeparam K: The type of the key (extends string | number | symbol)"
            in rst
        )

    def test_class_constrained(self):
        # TODO: this may belong somewhere else
        obj = self.analyzer.get_object(["ParamClass"])
        assert isinstance(obj, Class)
        tp = copy(obj.type_params[0])
        tp.extends = join_type(tp.extends)
        assert tp == TypeParam(
            name="S",
            extends="number[]",
            description=[DescriptionText("The type we contain")],
        )
        a = AutoClassRenderer.__new__(AutoClassRenderer)
        a._set_type_xref_formatter(None)
        a._explicit_formal_params = None  # type:ignore[attr-defined]
        a._add_span = False
        a._content = []
        a._options = {}
        rst = a.rst([obj.name], obj)
        rst = rst.replace("\\ ", "").replace("\\", "").replace("  ", " ")
        assert ":typeparam S: The type we contain (extends number[])" in rst

    def test_constrained_by_constructor(self):
        """Make sure ``new ()`` expressions and, more generally, per-property
        constraints are rendered properly."""
        obj = self.analyzer.get_object(["create1"])
        assert isinstance(obj, Function)
        assert join_type(obj.params[0].type) == "{new (x: number) => A}"
        obj = self.analyzer.get_object(["create2"])
        assert isinstance(obj, Function)
        assert join_type(obj.params[0].type) == "{new () => T}"

    def test_utility_types(self):
        """Test that a representative one of TS's utility types renders.

        Partial should generate a SymbolReference that we turn into a
        TypeXRefExternal
        """
        obj = self.analyzer.get_object(["partial"])
        assert isinstance(obj, Attribute)
        t = deepcopy(obj.type)
        assert t
        s = t[0]
        assert isinstance(s, TypeXRefExternal)
        s.sourcefilename = "xxx"
        assert t == [
            TypeXRefExternal("Partial", "typescript", "xxx", "Partial"),
            "<",
            TypeXRefIntrinsic("string"),
            ">",
        ]

    def test_internal_symbol_reference(self):
        """
        Blah should generate a SymbolReference that we turn into a
        TypeXRefInternal
        """
        obj = self.analyzer.get_object(["internalSymbolReference"])
        assert isinstance(obj, Attribute)
        assert obj.type == [
            TypeXRefInternal(name="Blah", path=["./", "exports"], type="internal")
        ]

    def test_constrained_by_property(self):
        obj = self.analyzer.get_object(["objProps"])
        assert isinstance(obj, Function)
        assert obj.params[0].type == [
            "{ ",
            "label",
            ": ",
            TypeXRefIntrinsic("string"),
            "; ",
            "}",
        ]
        assert (
            join_type(obj.params[1].type) == "{ [key: number]: string; label: string; }"
        )

    def test_optional_property(self):
        """Make sure optional properties render properly."""
        obj = self.analyzer.get_object(["option"])
        assert isinstance(obj, Attribute)
        assert join_type(obj.type) == "{ a: number; b?: string; }"

    def test_code_in_description(self):
        obj = self.analyzer.get_object(["codeInDescription"])
        assert obj.description == [
            DescriptionText(text="Code 1 had "),
            DescriptionCode(code="`single ticks around it`"),
            DescriptionText(text=".\nCode 2 has "),
            DescriptionCode(code="``double ticks around it``"),
            DescriptionText(text=".\nCode 3 has a :sphinx:role:"),
            DescriptionCode(code="`before it`"),
            DescriptionText(text=".\n\n"),
            DescriptionCode(code="```js\nA JS code pen!\n```"),
            DescriptionText(text="\nAnd some closing words."),
        ]

    def test_destructured(self):
        obj = self.analyzer.get_object(["destructureTest"])
        assert isinstance(obj, Function)
        # Parameters should be sorted by source position in the type annotation not by name.
        assert obj.params[0].name == "options.b"
        assert join_type(obj.params[0].type) == "{ c: string; }"
        assert obj.params[0].description == [DescriptionText(text="The 'b' string.")]
        assert obj.params[1].name == "options.a"
        assert join_type(obj.params[1].type) == "string"
        assert obj.params[1].description == [DescriptionText(text="The 'a' string.")]

        obj = self.analyzer.get_object(["destructureTest2"])
        assert isinstance(obj, Function)
        assert obj.params[0].name == "options.b"
        assert join_type(obj.params[0].type) == "{ c: string; }"
        assert obj.params[0].description == [DescriptionText(text="The 'b' object.")]

        assert obj.params[1].name == "options.a"
        assert join_type(obj.params[1].type) == "string"
        assert obj.params[1].description == [DescriptionText(text="The 'a' string.")]

        obj = self.analyzer.get_object(["destructureTest3"])
        assert isinstance(obj, Function)
        assert obj.params[0].name == "options"
        assert join_type(obj.params[0].type) == "{ a: string; b: { c: string; }; }"

        obj = self.analyzer.get_object(["destructureTest4"])
        assert isinstance(obj, Function)
        assert obj.params[0].name == "destructureThisPlease.a"
        assert join_type(obj.params[0].type) == "string"
        assert obj.params[0].description == [DescriptionText(text="The 'a' string.")]

    def test_funcarg(self):
        obj = self.analyzer.get_object(["funcArg"])
        assert isinstance(obj, Function)
        assert obj.params[0].name == "a"
        assert join_type(obj.params[0].type) == "(b: number, c: number) => number"

    def test_namedtuplearg(self):
        obj = self.analyzer.get_object(["namedTupleArg"])
        assert isinstance(obj, Function)
        assert obj.params[0].name == "namedTuple"
        assert join_type(obj.params[0].type) == "[key: string, value: any]"

    def test_query(self):
        obj = self.analyzer.get_object(["queryType"])
        assert isinstance(obj, Attribute)
        assert join_type(obj.type) == "typeof A"

    def test_type_operator(self):
        obj = self.analyzer.get_object(["typeOperatorType"])
        assert isinstance(obj, Attribute)
        assert join_type(obj.type) == "keyof A"

    def test_private_type_alias1(self):
        obj = self.analyzer.get_object(["typeIsPrivateTypeAlias1"])
        assert isinstance(obj, Attribute)
        assert join_type(obj.type) == "{ a: number; b: string; }"

    def test_private_type_alias2(self):
        obj = self.analyzer.get_object(["typeIsPrivateTypeAlias2"])
        assert isinstance(obj, Attribute)
        assert join_type(obj.type) == "{ a: number; b: string; }"

    def test_hidden_type_top_level(self):
        obj = self.analyzer.get_object(["hiddenType"])
        assert obj.modifier_tags == ["@hidetype"]
        assert isinstance(obj, Attribute)
        assert obj.type == []

    def test_hidden_type_member(self):
        obj = self.analyzer.get_object(["HasHiddenTypeMember"])
        assert isinstance(obj, Class)
        assert obj.members
        member = obj.members[0]
        assert isinstance(member, Attribute)
        assert member.type == []

    def test_rest_type(self):
        obj = self.analyzer.get_object(["restType"])
        assert isinstance(obj, Attribute)
        assert join_type(obj.type) == "[...number[]]"

    def test_indexed_access_type(self):
        obj = self.analyzer.get_object(["indexedAccessType"])
        assert isinstance(obj, Attribute)
        assert join_type(obj.type) == 'FunctionInterface["length"]'

    def test_conditional_type(self):
        obj = self.analyzer.get_object(["ConditionalType"])
        assert isinstance(obj, TypeAlias)
        assert join_type(obj.type) == "T extends A ? 1 : 2"

    def test_inferred_type(self):
        obj = self.analyzer.get_object(["InferredType"])
        assert isinstance(obj, TypeAlias)
        assert join_type(obj.type) == "T extends Promise<infer S> ? S : T"

    def test_mapped_type(self):
        obj = self.analyzer.get_object(["MappedType1"])
        assert isinstance(obj, TypeAlias)
        assert join_type(obj.type) == "{ [property in keys]: number }"
        obj = self.analyzer.get_object(["MappedType2"])
        assert isinstance(obj, TypeAlias)
        assert join_type(obj.type) == "{ -readonly [property in keys]?: number }"
        obj = self.analyzer.get_object(["MappedType3"])
        assert isinstance(obj, TypeAlias)
        assert join_type(obj.type) == "{ readonly [property in keys]-?: number }"

    def test_template_literal(self):
        obj = self.analyzer.get_object(["TemplateLiteral"])
        assert isinstance(obj, TypeAlias)
        assert join_type(obj.type) == "`${number}: ${string}`"
