"""
RST errors from ts_type_xref_formatter should cause build failures.

The test conf.py uses a formatter that always returns :js:None:`...`, which is
an invalid RST role. This should cause the build to fail.

We also test that the error message points to the right location.
"""

import io
from contextlib import redirect_stderr
from pathlib import Path

from sphinx.cmd.build import main as sphinx_main


def test_build_fails_with_invalid_role(tmp_path: Path):
    """Build must fail when ts_type_xref_formatter emits an invalid RST role."""
    docs_dir = str(Path(__file__).parent / "source" / "docs")
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        result = sphinx_main([docs_dir, "-b", "text", "-W", "-E", str(tmp_path)])
    output = stderr.getvalue()
    assert result != 0, "Expected build failure due to invalid :js:None: role"
    assert "index.rst:4" in output, f"Expected error at index.rst:4, got: {output}"
