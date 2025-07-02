from tests.testing import SphinxBuildTestCase


class Tests(SphinxBuildTestCase):
    def test_build_success(self):
        """Mostly just test that the build doesn't crash, which is what used to
        happen before we added the tab_width workaround.

        """
        self._file_contents_eq("index", "foo()\n\n   Foo.\n")
