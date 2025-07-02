"""Test incremental builds."""

import warnings
from pathlib import Path

import pytest
from sphinx.environment import CONFIG_NEW, CONFIG_OK
from sphinx.testing.util import strip_escseq


def build(app):
    """Build the given app, collecting docnames read and written (resolved).

    Returns a tuple (status text, [reads], [writes]), with reads and writes
    sorted for convenience.

    """
    reads = set([])
    writes = set([])

    def source_read(app, docname, source):
        reads.add(docname)

    def doctree_resolved(app, doctree, docname):
        writes.add(docname)

    source_read_id = app.connect("source-read", source_read)
    doctree_resolved_id = app.connect("doctree-resolved", doctree_resolved)

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(action="ignore", category=DeprecationWarning)
            app.build()
    finally:
        app.disconnect(source_read_id)
        app.disconnect(doctree_resolved_id)

    return (
        strip_escseq(app._status.getvalue()),
        list(sorted(reads)),
        list(sorted(writes)),
    )


def do_test(app, extension="js"):
    # Clean build.
    assert app.env.config_status == CONFIG_NEW
    status, reads, writes = build(app)
    assert reads == ["a", "a_b", "b", "index", "unrelated"]
    assert writes == ["a", "a_b", "b", "index", "unrelated"]

    # Incremental build, no config changed and no files changed.
    assert app.env.config_status == CONFIG_OK
    status, reads, writes = build(app)
    assert reads == []
    assert writes == []

    # Incremental build, one file changed.
    a_js = Path(app.srcdir) / f"a.{extension}"
    a_js.write_text(a_js.read_text() + "\n\n")

    assert app.env.config_status == CONFIG_OK
    status, reads, writes = build(app)
    # FIXME: re-enable the rest of this test!
    return

    assert reads == ["a", "a_b"]
    # Note that the transitive dependency 'index' is written.
    assert writes == ["a", "a_b", "index"]

    # Incremental build, the other file changed.
    b_js = Path(app.srcdir) / "inner" / f"b.{extension}"
    b_js.write_text(b_js.read_text() + "\n\n")

    assert app.env.config_status == CONFIG_OK
    status, reads, writes = build(app)
    assert reads == ["a_b", "b"]
    # Note that the transitive dependency 'index' is written.
    assert writes == ["a_b", "b", "index"]


# We must use a "real" builder since the `dummy` builder does not track changed
# files.
@pytest.mark.sphinx("html", testroot="incremental_js")
def test_incremental_js(make_app, app_params):
    args, kwargs = app_params

    app = make_app(*args, freshenv=True, **kwargs)
    do_test(app, extension="js")


@pytest.mark.xfail(reason="TODO: fix me!")
@pytest.mark.sphinx("html", testroot="incremental_ts")
def test_incremental_ts(make_app, app_params):
    args, kwargs = app_params

    app = make_app(*args, freshenv=True, **kwargs)
    do_test(app, extension="ts")
