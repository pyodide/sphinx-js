from tests.testing import SphinxBuildTestCase


class Tests(SphinxBuildTestCase):
    def test_dot_dot(self):
        """Make sure the build doesn't explode with a parse error on
        the "../more.bar" path that is constructed when the JSDoc doclets are
        imbibed.

        Also make sure it render correctly afterward.

        """
        self._file_contents_eq("index", "bar(node)\n\n" "   Bar function\n")
