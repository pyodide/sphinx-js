import sys
from inspect import getmembers
from os.path import dirname, join
from shutil import rmtree

from sphinx.cmd.build import main as sphinx_main

from sphinx_js.jsdoc import Analyzer as JsAnalyzer
from sphinx_js.jsdoc import jsdoc_output
from sphinx_js.typedoc import Analyzer as TsAnalyzer
from sphinx_js.typedoc import typedoc_output


class ThisDirTestCase:
    """A TestCase that knows how to find the directory the subclass is defined
    in"""

    @classmethod
    def this_dir(cls):
        """Return the path to the dir containing the testcase class."""
        # nose does some amazing magic that makes this work even if there are
        # multiple test modules with the same name:
        return dirname(sys.modules[cls.__module__].__file__)


class SphinxBuildTestCase(ThisDirTestCase):
    """Base class for tests which require a Sphinx tree to be built and then
    deleted afterward

    """

    builder = "text"

    @classmethod
    def setup_class(cls):
        """Run Sphinx against the dir adjacent to the testcase."""
        cls.docs_dir = join(cls.this_dir(), "source", "docs")
        # -v for better tracebacks:
        if sphinx_main(
            [cls.docs_dir, "-b", cls.builder, "-v", "-E", join(cls.docs_dir, "_build")]
        ):
            raise RuntimeError("Sphinx build exploded.")

    @classmethod
    def teardown_class(cls):
        rmtree(join(cls.docs_dir, "_build"))

    def _file_contents(self, filename):
        extension = "txt" if self.builder == "text" else "html"
        with open(
            join(self.docs_dir, "_build", f"{filename}.{extension}"),
            encoding="utf8",
        ) as file:
            return file.read()

    def _file_contents_eq(self, filename, expected_contents):
        __tracebackhide__ = True
        contents = self._file_contents(filename)
        # Fix a difference between sphinx v6 and v7
        contents = contents.replace(" --\n", "\n")
        assert contents == expected_contents


class JsDocTestCase(ThisDirTestCase):
    """Base class for tests which analyze a file using JSDoc"""

    @classmethod
    def setup_class(cls):
        """Run the JS analyzer over the JSDoc output."""
        source_dir = join(cls.this_dir(), "source")
        output = jsdoc_output(
            None, [join(source_dir, cls.file)], source_dir, source_dir
        )
        cls.analyzer = JsAnalyzer(output, source_dir)


class TypeDocTestCase(ThisDirTestCase):
    """Base class for tests which imbibe TypeDoc's output"""

    @classmethod
    def setup_class(cls):
        """Run the TS analyzer over the TypeDoc output."""
        cls._source_dir = join(cls.this_dir(), "source")
        from pathlib import Path

        config_file = Path(__file__).parent / "sphinxJsConfig.ts"

        [cls.json, cls.extra_data] = typedoc_output(
            abs_source_paths=[join(cls._source_dir, file) for file in cls.files],
            base_dir=cls._source_dir,
            ts_sphinx_js_config=str(config_file),
            typedoc_config_path=None,
            tsconfig_path="tsconfig.json",
            sphinx_conf_dir=cls._source_dir,
        )


class TypeDocAnalyzerTestCase(TypeDocTestCase):
    """Base class for tests which analyze a file using TypeDoc"""

    @classmethod
    def setup_class(cls):
        """Run the TS analyzer over the TypeDoc output."""
        super().setup_class()

        cls.analyzer = TsAnalyzer(cls.json, cls.extra_data, cls._source_dir)


NO_MATCH = object()


def dict_where(json, already_seen=None, **kwargs):
    """Return the first object in the given data structure with properties
    equal to the  ones given by ``kwargs``.

    For example::

        >>> dict_where({'hi': 'there', {'mister': 'zangler', 'and': 'friends'}},
                       mister=zangler)
        {'mister': 'zangler', 'and': 'friends'}

    So far, only dicts and lists are supported. Other data structures won't be
    recursed into. Cycles are avoided.

    """

    def matches_properties(json, **kwargs):
        """Return the given JSON object iff all the properties and values given
        by ``kwargs`` are in it. Else, return NO_MATCH."""
        for k, v in kwargs.items():
            if json.get(k, NO_MATCH) != v:
                return False
        return True

    if already_seen is None:
        already_seen = set()
    already_seen.add(id(json))
    if isinstance(json, list):
        for list_item in json:
            if id(list_item) not in already_seen:
                match = dict_where(list_item, already_seen, **kwargs)
                if match is not NO_MATCH:
                    return match
    elif isinstance(json, dict):
        if matches_properties(json, **kwargs):
            return json
        for v in json.values():
            if id(v) not in already_seen:
                match = dict_where(v, already_seen, **kwargs)
                if match is not NO_MATCH:
                    return match
    elif hasattr(type(json), "__attrs_attrs__"):
        d = dict([k, v] for [k, v] in getmembers(json) if not k.startswith("_"))
        if matches_properties(d, **kwargs):
            return json
        for k, v in d.items():
            if k.startswith("_"):
                continue
            if id(v) not in already_seen:
                match = dict_where(v, already_seen, **kwargs)
                if match is not NO_MATCH:
                    return match
    else:
        # We don't know how to match leaf values yet.
        pass
    return NO_MATCH
