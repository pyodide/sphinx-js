from tests.testing import NO_MATCH, dict_where


def test_dict_where():
    json = {"hi": "there", "more": {"mister": "zangler", "and": "friends"}}
    assert dict_where(json, mister="zangler") == {"mister": "zangler", "and": "friends"}
    assert dict_where(json, mister="zangler", fee="foo") == NO_MATCH
    assert dict_where(json, hi="there") == json
