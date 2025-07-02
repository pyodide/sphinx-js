from sphinx_js.ir import (
    Attribute,
    DescriptionCode,
    Exc,
    Function,
    Param,
    Pathname,
    Return,
)
from sphinx_js.jsdoc import full_path_segments
from tests.testing import JsDocTestCase


def test_doclet_full_path():
    """Sanity-check full_path_segments(), including throwing it a non-.js filename."""
    doclet = {
        "meta": {
            "filename": "utils.jsm",
            "path": "/boogie/smoo/Checkouts/fathom",
        },
        "longname": "best#thing~yeah",
    }
    assert full_path_segments(doclet, "/boogie/smoo/Checkouts") == [
        "./",
        "fathom/",
        "utils.",
        "best#",
        "thing~",
        "yeah",
    ]


class TestFunction(JsDocTestCase):
    file = "function.js"

    def test_top_level_and_function(self):
        """Test Function (and thus also TopLevel) analysis.

        This also includes exceptions, returns, params, and default values.

        """
        function = self.analyzer.get_object(["foo"], "function")
        assert function == Function(
            name="foo",
            path=Pathname(["./", "function.", "foo"]),
            filename="function.js",
            deppath="function.js",
            # Line breaks and indentation should be preserved:
            description=(
                "Determine any of type, note, score, and element using a callback. This\n"
                "overrides any previous call.\n"
                "\n"
                "The callback should return...\n"
                "\n"
                "* An optional :term:`subscore`\n"
                "* A type (required on ``dom(...)`` rules, defaulting to the input one on\n"
                "  ``type(...)`` rules)"
            ),
            line=17,
            deprecated=False,
            examples=[],
            see_alsos=[],
            properties=[],
            is_private=False,
            exported_from=None,
            is_abstract=False,
            is_optional=False,
            is_static=False,
            is_async=False,
            params=[
                Param(
                    name="bar",
                    description="Which bar",
                    has_default=False,
                    is_variadic=False,
                    type="String",
                ),
                Param(
                    name="baz",
                    description="",
                    has_default=True,
                    default="8",
                    is_variadic=False,
                    type=None,
                ),
            ],
            exceptions=[Exc(type=None, description="ExplosionError It went boom.")],
            returns=[
                Return(
                    type="Number",
                    # Line breaks and indentation should be preserved:
                    description="How many things\n    there are",
                )
            ],
        )


class TestClass(JsDocTestCase):
    file = "class.js"

    def test_class(self):
        """Test Class analysis, including members, attributes, and privacy."""
        cls = self.analyzer.get_object(["Foo"], "class")
        assert cls.name == "Foo"
        assert cls.path == Pathname(["./", "class.", "Foo"])
        assert cls.filename == "class.js"
        assert (
            cls.description
            == "This is a long description that should not be unwrapped. Once day, I was\nwalking down the street, and a large, green, polka-dotted grand piano fell\nfrom the 23rd floor of an apartment building."
        )
        # Not ideal, as it refers to the constructor, but we'll allow it
        assert cls.line in (
            8,  # jsdoc 4.0.0
            15,  # jsdoc 3.6.3
        )
        # We ignore examples and other fields from the class doclet so far. This could change someday.
        assert cls.examples == [[DescriptionCode(code="```js\nExample in class\n```")]]

        # Members:
        getter, private_method = cls.members  # default constructor not included here
        assert isinstance(private_method, Function)
        assert private_method.name == "secret"
        assert private_method.path == Pathname(["./", "class.", "Foo#", "secret"])
        assert private_method.description == "Private method."
        assert private_method.is_private is True
        assert isinstance(getter, Attribute)
        assert getter.name == "bar"
        assert getter.path == Pathname(["./", "class.", "Foo#", "bar"])
        assert getter.filename == "class.js"
        assert getter.description == "Setting this also frobs the frobnicator."

        # Constructor:
        constructor = cls.constructor_
        assert constructor.name == "Foo"
        assert constructor.path == Pathname(
            ["./", "class.", "Foo"]
        )  # Same path as class. This might differ in different languages.
        assert constructor.filename == "class.js"
        assert constructor.description == "Constructor doc."
        assert constructor.examples == [
            [DescriptionCode(code="```js\nExample in class\n```")]
        ]
        assert constructor.params == [
            Param(
                name="ho",
                description="A thing",
                has_default=False,
                is_variadic=False,
                type=None,
            )
        ]
