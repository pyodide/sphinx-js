import pytest
from sphinx.errors import SphinxError

from sphinx_js import root_or_fallback


def test_relative_path_root():
    """Make sure the computation of the root path for relative JS entity
    pathnames is right."""
    # Fall back to the only source path if not specified.
    assert root_or_fallback(None, ["a"]) == "a"
    with pytest.raises(SphinxError):
        root_or_fallback(None, ["a", "b"])
    assert root_or_fallback("smoo", ["a"]) == "smoo"
