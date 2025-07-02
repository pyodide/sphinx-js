from pytest import raises

from sphinx_js.suffix_tree import SuffixAmbiguous, SuffixNotFound, SuffixTree


def test_things():
    s = SuffixTree()
    s.add(["./", "dir/", "utils.", "max"], 1)
    s.add(["./", "dir/", "footils.", "max"], 2)
    s.add(["./", "dir/", "footils.", "hacks"], 3)

    assert s.get(["hacks"]) == 3
    assert s.get_with_path(["footils.", "max"]) == (
        2,
        ["./", "dir/", "footils.", "max"],
    )
    with raises(SuffixNotFound):
        s.get(["quacks.", "max"])
    with raises(SuffixAmbiguous):
        s.get(["max"])


def test_full_path():
    """Looking up a full path should not crash."""
    s = SuffixTree()
    s.add(["./", "dir/", "footils.", "jacks"], 4)
    assert s.get_with_path(["./", "dir/", "footils.", "jacks"]) == (
        4,
        ["./", "dir/", "footils.", "jacks"],
    )


def test_terminal_insertion():
    """A non-terminal segment should be able to later be made terminal."""
    s = SuffixTree()
    s.add(["a", "b"], 5)
    s.add(["b"], 4)
    with raises(SuffixAmbiguous):
        s.get("b")


def test_ambiguous_even_if_full_path():
    """Even full paths should be considered ambiguous if there are paths that
    have them as suffixes."""
    s = SuffixTree()
    s.add(["a", "b"], 5)
    s.add(["q", "a", "b"], 6)
    with raises(SuffixAmbiguous):
        s.get(["a", "b"])


def test_ambiguous_paths_reported():
    """Make sure SuffixAmbiguous gives a good explanation."""
    s = SuffixTree()
    s.add(["q", "b", "c"], 5)
    s.add(["r", "b", "c"], 6)
    try:
        s.get(["b", "c"])
    except SuffixAmbiguous as exc:
        assert exc.next_possible_keys == ["q", "r"]
        assert not exc.or_ends_here


def test_value_ambiguity():
    """If we're at the point of following single-subtree links, make sure we
    throw SuffixAmbiguous if we encounter a value and a subtree at a given
    point (b in this case)."""
    s = SuffixTree()
    s.add(["a", "b", "c"], 5)
    s.add(["b", "c"], 6)
    try:
        assert s.get(["c"])
    except SuffixAmbiguous as exc:
        assert exc.next_possible_keys == ["b"]
        assert exc.or_ends_here
