from textwrap import dedent

from bs4 import BeautifulSoup, Tag

from tests.testing import SphinxBuildTestCase


class TestTextBuilder(SphinxBuildTestCase):
    """Tests which require our big TS Sphinx tree to be built (as text)"""

    def test_autoclass_constructor(self):
        """Make sure class constructor comes before methods."""
        contents = self._file_contents("index")
        pos_cstrct = contents.index("ClassDefinition constructor")
        pos_method = contents.index("ClassDefinition.method1")
        assert pos_method > pos_cstrct, (
            "Constructor appears after method in " + contents
        )

    def test_autoclass_order(self):
        """Make sure fields come before methods."""
        contents = self._file_contents("index")
        pos_field = contents.index("ClassDefinition.field")
        pos_method2 = contents.index("ClassDefinition.anotherMethod")
        pos_method = contents.index("ClassDefinition.method1")
        assert pos_field < pos_method2 < pos_method, (
            "Methods and fields are not in right order in " + contents
        )

    def test_autoclass_star_order(self):
        """Make sure fields come before methods even when using ``*``."""
        contents = self._file_contents("autoclass_star")
        pos_method = contents.index("ClassDefinition.method1")
        pos_field = contents.index("ClassDefinition.field")
        pos_method2 = contents.index("ClassDefinition.anotherMethod")
        assert pos_method < pos_field < pos_method2, (
            "Methods and fields are not in right order in " + contents
        )

    def test_abstract_extends_and_implements(self):
        """Make sure the template correctly represents abstract classes,
        classes with superclasses, and classes that implement interfaces.

        These are all TypeScript-specific features.

        """
        # The quotes around ClassDefinition must be some weird decision in
        # Sphinx's text output. I don't care if they go away in a future
        # version of Sphinx. It doesn't affect the HTML output.
        self._file_contents_eq(
            "autoclass_class_with_interface_and_supers",
            "class ClassWithSupersAndInterfacesAndAbstract()\n"
            "\n"
            "   A definition of a class\n\n"
            "   *abstract*\n"
            "\n"
            '   *exported from* "class"\n'
            "\n"
            "   **Extends:**\n"
            '      * "ClassDefinition"\n'
            "\n"
            "   **Implements:**\n"
            '      * "Interface"\n'
            "\n"
            "   I construct.\n",
        )

    def test_exported_from(self):
        """Make sure classes say where they were exported from.

        I'm divided on whether this is even useful. Maybe people should just
        specify full.path.Names in the js:autoclass directives if they want to
        surface that info.

        """
        self._file_contents_eq(
            "autoclass_exported",
            "class ExportedClass()\n" "\n" '   *exported from* "class"\n',
        )

    def test_constructorless_class(self):
        """Make sure constructorless classes don't crash the renderer."""
        self._file_contents_eq(
            "autoclass_constructorless",
            'class ConstructorlessClass()\n\n   *exported from* "class"\n',
        )

    def test_optional_members(self):
        """Make sure optional attributes and functions of interfaces get
        question marks sticking out of them."""
        self._file_contents_eq(
            "autoclass_interface_optionals",
            "interface OptionalThings\n"
            "\n"
            '   *exported from* "class"\n'
            "\n"
            "   OptionalThings.boop?\n"
            "\n"
            "      type: boolean\n"
            "\n"
            "   OptionalThings.foop?()\n",
        )

    def test_deprecated(self):
        self._file_contents_eq(
            "deprecated",
            dedent(
                """\
                deprecatedFunction1()

                   Note:

                     Deprecated: since v20!

                deprecatedFunction2()

                   Note:

                     Deprecated.
                """
            ),
        )

    def test_example(self):
        self._file_contents_eq(
            "example",
            dedent(
                """\
                exampleFunction()

                   Example:

                      This is an example.

                   Example: This is another example.

                      Something python
                """
            ),
        )

    def test_async(self):
        self._file_contents_eq(
            "async_function",
            dedent(
                """\
                async asyncFunction()

                   Returns:
                      Promise<void>
                """
            ),
        )

    def test_symbol(self):
        expected = dedent(
            """\
            class Iterable()

               *exported from* "class"

               Iterable.[Symbol․iterator]()

                  Returns:
                     Iterator<number, string, undefined>
            """
        )
        self._file_contents_eq("symbol", expected)

    def test_predicate(self):
        self._file_contents_eq(
            "predicate",
            dedent(
                """\
                predicate(c)

                   Arguments:
                      * **c** (any)

                   Returns:
                      boolean (typeguard for "ConstructorlessClass")
                """
            ),
        )

    def test_get_set(self):
        self._file_contents_eq(
            "getset",
            dedent(
                """\
class GetSetDocs()

   *exported from* "class"

   GetSetDocs.a

      type: readonly number

      Getter with comment

   GetSetDocs.b

      type: number

      Setter with comment

   GetSetDocs.x

      type: readonly number

   GetSetDocs.y

      type: number
                """
            ),
        )

    def test_inherited_docs(self):
        # Check that we aren't including documentation entries from the base class
        self._file_contents_eq(
            "inherited_docs",
            dedent(
                """\
                class Base()

                   *exported from* "class"

                   Base.a

                      type: readonly number

                   Base.f()

                      Some docs for f

                class Extension()

                   *exported from* "class"

                   **Extends:**
                      * "Base"

                   Extension.g()

                      Some docs for g
                """
            ),
        )

    def test_automodule(self):
        self._file_contents_eq(
            "automodule",
            dedent(
                """\
module.TestTypeAlias<T>

   type: { a: T; }

   A super special type alias

   Type parameters:
      **T** -- The whatsit (extends "A")

module.TestTypeAlias2

   type: { a: number; }

module.a

   type: 7

   The thing.

module.aInstance

   type: "A"

   An instance of class A

module.interfaceInstance

   type: "I"

   An instance of the interface

module.q

   type: { a: string; b: number; }

   Another thing.

module.t

   type: "TestTypeAlias"<"A">

module.t2

   type: "TestTypeAlias2"

module.zInstance

   type: "Z"<"A">

async module.f()

   Clutches the bundle

   Returns:
      Promise<void>

module.functionWithTypeParam<T>(z)

   A function with a type parameter!

   We'll refer to ourselves: "functionWithTypeParam()"

   Type parameters:
      **T** -- The type parameter (extends "A")

   Arguments:
      * **z** ("Z"<T>) -- A Z of T

   Returns:
      T -- The x field of z

module.z(a, b)

   Arguments:
      * **a** (number)

      * **b** ({ a: string; b: number; })

   Returns:
      number

interface module.I

   Documentation for the interface I

   *exported from* "module"

class module.A()

   This is a summary. This is more info.

   *exported from* "module"

   A.[Symbol․iterator]()

   async A.f()

      Returns:
         Promise<void>

   A.g(a)

      Arguments:
         * **a** (number)

      Returns:
         number

class module.Z<T>(a, b)

   *exported from* "module"

   Type parameters:
      **T** -- Description of T (extends "A")

   Arguments:
      * **a** (number)

      * **b** (number)

   Z.x

      type: T

   Z.z()
                """
            ),
        )


class TestHtmlBuilder(SphinxBuildTestCase):
    """Tests which require an HTML build of our Sphinx tree, for checking
    links"""

    builder = "html"

    def test_extends_links(self):
        """Make sure superclass mentions link to their definitions."""
        assert 'href="index.html#ClassDefinition"' in self._file_contents(
            "autoclass_class_with_interface_and_supers"
        )

    def test_implements_links(self):
        """Make sure implemented interfaces link to their definitions."""
        assert 'href="index.html#Interface"' in self._file_contents(
            "autoclass_class_with_interface_and_supers"
        )

    def test_extends_type_param_links(self):
        """Make sure implemented interfaces link to their definitions."""
        soup = BeautifulSoup(self._file_contents("automodule"), "html.parser")
        z = soup.find(id="module.Z")
        assert z
        assert z.parent
        t = z.parent.find_all(class_="sphinx_js-type")
        s: Tag = t[0]
        href: Tag = list(s.children)[0]
        assert href.name == "a"
        assert href.get_text() == "A"
        assert href.attrs["class"] == ["reference", "internal"]
        assert href.attrs["title"] == "module.A"
        assert href.attrs["href"] == "#module.A"

    def test_xrefs(self):
        soup = BeautifulSoup(self._file_contents("xrefs"), "html.parser")

        def get_links(id):
            return soup.find(id=id).parent.find_all("a")

        links = get_links("blah")
        href = links[1]
        assert href.attrs["class"] == ["reference", "internal"]
        assert href.attrs["href"] == "autoclass_interface_optionals.html#OptionalThings"
        assert href.attrs["title"] == "OptionalThings"
        assert next(href.children).name == "code"
        assert href.get_text() == "OptionalThings"

        href = links[2]
        assert href.attrs["class"] == ["reference", "internal"]
        assert (
            href.attrs["href"] == "autoclass_constructorless.html#ConstructorlessClass"
        )
        assert href.get_text() == "ConstructorlessClass"

        thunk_links = get_links("thunk")
        assert thunk_links[1].get_text() == "OptionalThings"
        assert thunk_links[2].get_text() == "ConstructorlessClass"

    def test_sphinx_link_in_description(self):
        soup = BeautifulSoup(
            self._file_contents("sphinx_link_in_description"), "html.parser"
        )
        href = soup.find(id="spinxLinkInDescription").parent.find_all("a")[1]
        assert href.get_text() == "abc"
        assert href.attrs["href"] == "http://example.com"

    def test_sphinx_js_type_class(self):
        soup = BeautifulSoup(self._file_contents("async_function"), "html.parser")
        href = soup.find_all(class_="sphinx_js-type")
        assert len(href) == 1
        assert href[0].get_text() == "Promise<void>"

    def test_autosummary(self):
        soup = BeautifulSoup(self._file_contents("autosummary"), "html.parser")
        attrs = soup.find(class_="attributes")
        rows = list(attrs.find_all("tr"))
        assert len(rows) == 7

        href = rows[0].find("a")
        assert href.get_text() == "a"
        assert href["href"] == "automodule.html#module.a"
        assert rows[0].find(class_="summary").get_text() == "The thing."

        href = rows[1].find("a")
        assert href.get_text() == "aInstance"
        assert href["href"] == "automodule.html#module.aInstance"
        assert rows[1].find(class_="summary").get_text() == "An instance of class A"

        funcs = soup.find(class_="functions")
        rows = list(funcs.find_all("tr"))
        assert len(rows) == 3
        row0 = list(rows[0].children)
        NBSP = "\xa0"
        assert row0[0].get_text() == f"async{NBSP}f()"
        href = row0[0].find("a")
        assert href.get_text() == "f"
        assert href["href"] == "automodule.html#module.f"
        assert rows[0].find(class_="summary").get_text() == "Clutches the bundle"

        row1 = list(rows[2].children)
        assert row1[0].get_text() == "z(a, b)"
        href = row1[0].find("a")
        assert href.get_text() == "z"
        assert href["href"] == "automodule.html#module.z"

        classes = soup.find(class_="classes")
        assert classes.find(class_="summary").get_text() == "This is a summary."

        classes = soup.find(class_="interfaces")
        assert (
            classes.find(class_="summary").get_text()
            == "Documentation for the interface I"
        )

        classes = soup.find(class_="type_aliases")
        assert classes
        assert classes.find(class_="summary").get_text() == "A super special type alias"
