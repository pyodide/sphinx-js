from sphinx import __version__ as sphinx_version

from tests.testing import SphinxBuildTestCase


SPHINX_VERSION = tuple(int(part) for part in sphinx_version.split('.'))

# NOTE(willkg): This is the version of Sphinx that removes trailing " --" from
# :params: lines when there is no description.
SPHINX_7_3_0 = (7, 3, 0)


class Tests(SphinxBuildTestCase):
    """Tests which require our big JS Sphinx tree to be built.

    Yes, it's too coupled.

    Many of these are renderer tests, but some indirectly test JS analysis.
    These latter are left over from when JS was the only supported language and
    had its assumptions coded into the renderers.

    """

    def test_autofunction_minimal(self):
        """Make sure we render correctly and pull the params out of the JS code
        when only the function name is provided."""
        self._file_contents_eq(
            "autofunction_minimal", "linkDensity(node)" + DESCRIPTION + FIELDS
        )

    def test_autofunction_explicit(self):
        """Make sure any explicitly provided params override the ones from the
        code, and make sure any explicit arbitrary RST content gets
        preserved."""
        self._file_contents_eq(
            "autofunction_explicit",
            "linkDensity(snorko, borko[, forko])" + DESCRIPTION + FIELDS + CONTENT,
        )

    def test_autofunction_short(self):
        """Make sure the ``:short-name:`` option works."""
        self._file_contents_eq("autofunction_short", "someMethod(hi)\n\n   Here.\n")

    def test_autofunction_long(self):
        """Make sure instance methods get converted to dotted notation which
        indexes better in Sphinx."""
        self._file_contents_eq(
            "autofunction_long", "ContainingClass.someMethod(hi)\n\n   Here.\n"
        )

    def test_autofunction_typedef(self):
        """Make sure @typedef uses can be documented with autofunction."""
        self._file_contents_eq(
            "autofunction_typedef",
            "TypeDefinition()\n\n   Arguments:\n      * **width** (**Number**) -- width in pixels\n",
        )

    def test_autofunction_callback(self):
        """Make sure @callback uses can be documented with autofunction."""
        self._file_contents_eq(
            "autofunction_callback",
            "requestCallback(responseCode)\n\n   Some global callback\n\n   Arguments:\n      * **responseCode** (**number**)\n",
        )

    def test_autofunction_example(self):
        """Make sure @example tags can be documented with autofunction."""
        self._file_contents_eq(
            "autofunction_example",
            "exampleTag()\n\n"
            "   JSDoc example tag\n\n"
            "   Example:\n\n"
            "      // This is the example.\n"
            "      exampleTag();\n",
        )

    def test_autofunction_destructured_params(self):
        """Make sure that all documented params appears in the function
        definition."""
        self._file_contents_eq(
            "autofunction_destructured_params",
            "destructuredParams(p1, p2)\n\n"
            "   Arguments:\n"
            "      * **p1** (**number**)\n\n"
            "      * **p2** (**Object**)\n\n"
            "      * **p2.foo** (**string**)\n\n"
            "      * **p2.bar** (**string**)\n",
        )

    def test_autofunction_defaults_in_doclet(self):
        """Make sure param default values appear in the function definition,
        when defined in JSDoc."""
        self._file_contents_eq(
            "autofunction_defaults_doclet",
            'defaultsDocumentedInDoclet(func=() => 5, str="a string with \\" quote", strNum="42", strBool="true", num=5, nil=null)\n\n'
            "   Arguments:\n"
            "      * **func** (**function**)\n\n"
            "      * **strNum** (**string**)\n\n"
            "      * **strBool** (**string**)\n",
        )

    def test_autofunction_defaults_in_code(self):
        """Make sure param default values appear in the function definition,
        when defined in code."""
        self._file_contents_eq(
            "autofunction_defaults_code",
            'defaultsDocumentedInCode(num=5, str="true", bool=true, nil=null)\n',
        )

    def test_autofunction_variadic(self):
        """Make sure variadic parameters are rendered as ellipses."""
        self._file_contents_eq(
            "autofunction_variadic",
            "variadicParameter(a, ...args)\n\n" "   Variadic parameter\n",
        )

    def test_autofunction_deprecated(self):
        """Make sure @deprecated tags can be documented with autofunction."""
        self._file_contents_eq(
            "autofunction_deprecated",
            "deprecatedFunction()\n\n"
            "   Note:\n\n"
            "     Deprecated.\n\n"
            "deprecatedExplanatoryFunction()\n\n"
            "   Note:\n\n"
            "     Deprecated: don't use anymore\n",
        )

    def test_autofunction_see(self):
        """Make sure @see tags work with autofunction."""
        self._file_contents_eq(
            "autofunction_see",
            "seeFunction()\n\n"
            "   See also:\n\n"
            '     * "DeprecatedClass"\n\n'
            '     * "deprecatedFunction"\n\n'
            '     * "DeprecatedAttribute"\n',
        )

    def test_autofunction_static(self):
        """Make sure the static function gets its prefix ``static``."""
        self._file_contents_eq(
            "autofunction_static",
            "class SimpleClass()\n\n"
            "   Class doc.\n"
            "\n"
            "   SimpleClass.nonStaticMethod()\n"
            "\n"
            "      Non-static member.\n"
            "\n"
            "      See also:\n"
            "\n"
            '        * "staticMethod"\n'
            "\n"
            "   static SimpleClass.staticMethod()\n"
            "\n"
            "      Static.\n"
            "\n"
            "      See also:\n"
            "\n"
            '        * "nonStaticMethod"\n',
        )

    def test_autoclass(self):
        """Make sure classes show their class comment and constructor
        comment."""
        contents = self._file_contents("autoclass")
        assert "Class doc." in contents
        assert "Constructor doc." in contents

    def test_autoclass_members(self):
        """Make sure classes list their members if ``:members:`` is specified.

        Make sure it shows both functions and attributes and shows getters and
        setters as if they are attributes. Make sure it doesn't show private
        members.

        """
        self._file_contents_eq(
            "autoclass_members",
            "class ContainingClass(ho)\n\n"
            "   Class doc.\n"
            "\n"
            "   Constructor doc.\n"
            "\n"
            "   Arguments:\n"
            "      * **ho** -- A thing\n"
            "\n"
            "   ContainingClass.bar\n"
            "\n"
            "      Setting this also frobs the frobnicator.\n"
            "\n"
            "   ContainingClass.someVar\n"
            "\n"
            "      A var\n"
            "\n"
            "   ContainingClass.anotherMethod()\n"
            "\n"
            "      Another.\n"
            "\n"
            "   ContainingClass.someMethod(hi)\n"
            "\n"
            "      Here.\n"
            "\n"
            "   ContainingClass.yetAnotherMethod()\n"
            "\n"
            "      More.\n",
        )

    def test_autoclass_members_list(self):
        """Make sure including a list of names after ``members`` limits it to
        those names and follows the order you specify."""
        self._file_contents_eq(
            "autoclass_members_list",
            "class ClosedClass()\n\n   Closed class.\n\n   ClosedClass.publical3()\n\n      Public thing 3.\n\n   ClosedClass.publical()\n\n      Public thing.\n",
        )

    def test_autoclass_members_list_star(self):
        """Make sure including ``*`` in a list of names after
        ``members`` includes the rest of the names in the normal order
        at that point."""
        self._file_contents_eq(
            "autoclass_members_list_star",
            "class ContainingClass(ho)\n"
            "\n"
            "   Class doc.\n"
            "\n"
            "   Constructor doc.\n"
            "\n"
            "   Arguments:\n"
            "      * **ho** -- A thing\n"
            "\n"
            "   ContainingClass.bar\n"
            "\n"
            "      Setting this also frobs the frobnicator.\n"
            "\n"
            "   ContainingClass.someVar\n"
            "\n"
            "      A var\n"
            "\n"
            "   ContainingClass.anotherMethod()\n"
            "\n"
            "      Another.\n"
            "\n"
            "   ContainingClass.yetAnotherMethod()\n"
            "\n"
            "      More.\n"
            "\n"
            "   ContainingClass.someMethod(hi)\n"
            "\n"
            "      Here.\n",
        )

    def test_autoclass_alphabetical(self):
        """Make sure members sort alphabetically when not otherwise specified."""
        self._file_contents_eq(
            "autoclass_alphabetical",
            "class NonAlphabetical()\n\n   Non-alphabetical class.\n\n   NonAlphabetical.a()\n\n      Fun a.\n\n   NonAlphabetical.z()\n\n      Fun z.\n",
        )

    def test_autoclass_private_members(self):
        """Make sure classes list their private members if
        ``:private-members:`` is specified."""
        contents = self._file_contents("autoclass_private_members")
        assert "secret()" in contents

    def test_autoclass_exclude_members(self):
        """Make sure ``exclude-members`` option actually excludes listed
        members."""
        contents = self._file_contents("autoclass_exclude_members")
        assert "publical()" in contents
        assert "publical2" not in contents
        assert "publical3" not in contents

    def test_autoclass_example(self):
        """Make sure @example tags can be documented with autoclass."""
        self._file_contents_eq(
            "autoclass_example",
            "class ExampleClass()\n\n"
            "   JSDoc example tag for class\n\n"
            "   Example:\n\n"
            "      // This is the example.\n"
            "      new ExampleClass();\n",
        )

    def test_autoclass_deprecated(self):
        """Make sure @deprecated tags can be documented with autoclass."""
        self._file_contents_eq(
            "autoclass_deprecated",
            "class DeprecatedClass()\n\n"
            "   Note:\n\n"
            "     Deprecated.\n\n"
            "class DeprecatedExplanatoryClass()\n\n"
            "   Note:\n\n"
            "     Deprecated: don't use anymore\n",
        )

    def test_autoclass_see(self):
        """Make sure @see tags work with autoclass."""
        self._file_contents_eq(
            "autoclass_see",
            "class SeeClass()\n\n"
            "   See also:\n\n"
            '     * "DeprecatedClass"\n\n'
            '     * "deprecatedFunction"\n\n'
            '     * "DeprecatedAttribute"\n',
        )

    def test_autoattribute(self):
        """Make sure ``autoattribute`` works."""
        self._file_contents_eq("autoattribute", "ContainingClass.someVar\n\n   A var\n")

    def test_autoattribute_example(self):
        """Make sure @example tags can be documented with autoattribute."""
        self._file_contents_eq(
            "autoattribute_example",
            "ExampleAttribute\n\n"
            "   JSDoc example tag for attribute\n\n"
            "   Example:\n\n"
            "      // This is the example.\n"
            "      console.log(ExampleAttribute);\n",
        )

    def test_autoattribute_deprecated(self):
        """Make sure @deprecated tags can be documented with autoattribute."""
        self._file_contents_eq(
            "autoattribute_deprecated",
            "DeprecatedAttribute\n\n"
            "   Note:\n\n"
            "     Deprecated.\n\n"
            "DeprecatedExplanatoryAttribute\n\n"
            "   Note:\n\n"
            "     Deprecated: don't use anymore\n",
        )

    def test_autoattribute_see(self):
        """Make sure @see tags work with autoattribute."""
        self._file_contents_eq(
            "autoattribute_see",
            "SeeAttribute\n\n"
            "   See also:\n\n"
            '     * "DeprecatedClass"\n\n'
            '     * "deprecatedFunction"\n\n'
            '     * "DeprecatedAttribute"\n',
        )

    def test_getter_setter(self):
        """Make sure ES6-style getters and setters can be documented."""
        self._file_contents_eq(
            "getter_setter",
            "ContainingClass.bar\n\n   Setting this also frobs the frobnicator.\n",
        )

    def test_no_shadowing(self):
        """Make sure we can disambiguate objects of the same name."""
        self._file_contents_eq(
            "avoid_shadowing",
            "more_code.shadow()\n\n   Another thing named shadow, to threaten to shadow the one in\n   code.js\n",
        )

    def test_restructuredtext_injection(self):
        """Make sure param names and types are escaped and cannot be
        interpreted as RestructuredText.

        Descriptions should not be escaped; it is a feature to be able to use
        RST markup there.

        """
        self._file_contents_eq(
            "injection",
            "injection(a_, b)\n\n"
            "   Arguments:\n"
            "      * **a_** -- Snorf\n\n"
            "      * **b** (**type_**) -- >>Borf_<<\n\n"
            "   Returns:\n"
            "      **rtype_** -- >>Dorf_<<\n",
        )

    def test_union_types(self):
        """Make sure union types render into RST non-wonkily.

        The field was rendering into text as this before::

            * **| Fnode fnodeA** (*Node*) --

        I don't know what RST was thinking, but it got sane again when we
        switched from " | " as the union separator back to "|".

        """
        assert "* **fnodeA** (**Node|Fnode**)" in self._file_contents("union")

    def test_field_list_unwrapping(self):
        """Ensure the tails of field lists have line breaks and leading
        whitespace removed.

        Otherwise, the RST parser decides the field list is over, leading to
        mangled markup.

        """
        self._file_contents_eq(
            "unwrapped",
            "longDescriptions(a, b)\n"
            "\n"
            "   Once upon a time, there was a large bear named Sid. Sid wore green\n"
            "   pants with blue stripes and pink polka dots.\n"
            "\n"
            # Also assert that line breaks in the description are preserved:
            "   * List!\n"
            "\n"
            "   Arguments:\n"
            "      * **a** -- A is the first letter of the Roman alphabet. It is\n"
            "        used in such illustrious words as aardvark and artichoke.\n"
            "\n"
            "      * **b** -- Next param, which should be part of the same field\n"
            "        list\n",
        )


DESCRIPTION = """

   Return the ratio of the inline text length of the links in an
   element to the inline text length of the entire element."""

FIELDS = """

   Arguments:
      * **node** (**Node**) -- Something of a single type

   Throws:
      **PartyError|FartyError** -- Something with multiple types and a
      line that wraps

   Returns:
      **Number** -- What a thing
"""

# Oddly enough, the text renderer renders these bullets with a blank line
# between, but the HTML renderer does make them a single list.
CONTENT = """
   Things are "neat".

   Off the beat.

   * Sweet

   * Fleet
"""
