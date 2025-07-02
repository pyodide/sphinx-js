from sphinx_js.parsers import PathVisitor, path_and_formal_params


def test_escapes():
    r"""Make sure escapes work right and Python escapes like \n don't work."""
    assert PathVisitor().parse(r"d\.i:\nr/ut\\ils.max(whatever)") == [
        [r"d.i:nr/", r"ut\ils.", "max"],
        "(whatever)",
    ]


def test_relative_dirs():
    """Make sure all sorts of relative-dir prefixes result in proper path
    segment arrays."""
    assert PathVisitor().visit(path_and_formal_params["path"].parse("./hi")) == [
        "./",
        "hi",
    ]
    assert PathVisitor().visit(path_and_formal_params["path"].parse("../../hi")) == [
        "../",
        "../",
        "hi",
    ]
