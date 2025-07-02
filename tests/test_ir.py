from inspect import getmembers
from json import dumps, loads

import pytest

from sphinx_js.ir import (
    Attribute,
    DescriptionCode,
    DescriptionName,
    DescriptionText,
    Function,
    Param,
    Pathname,
    Return,
    TopLevel,
    TypeXRefExternal,
    TypeXRefInternal,
    converter,
    json_to_ir,
)


def test_default():
    """Accessing ``.default`` on a Param having a default should return the
    default value."""
    p = Param(name="fred", has_default=True, default="boof")
    assert p.default == "boof"


def test_missing_default():
    """Constructing a Param with ``has_default=True`` but without a ``default``
    value should raise an error."""
    with pytest.raises(ValueError):
        Param(name="fred", has_default=True)


top_level_base = TopLevel(
    name="blah",
    block_tags={},
    deppath="x",
    deprecated=False,
    description=[],
    examples=[],
    exported_from=Pathname([]),
    filename="",
    line=7,
    modifier_tags=[],
    path=Pathname([]),
    properties=[],
    see_alsos=[],
    kind="",
)
tl_dict = {k: v for k, v in getmembers(top_level_base) if not k.startswith("_")}
del tl_dict["kind"]

attribute_base = Attribute(
    **tl_dict,
    is_abstract=False,
    is_optional=False,
    is_static=False,
    is_private=False,
    readonly=False,
    type=[]
)
attr_dict = {k: v for k, v in getmembers(attribute_base) if not k.startswith("_")}


def attr_with(**kwargs):
    return Attribute(**(attr_dict | kwargs))


function_base = Function(
    **tl_dict,
    is_abstract=False,
    is_optional=False,
    is_static=False,
    is_private=False,
    is_async=False,
    params=[],
    exceptions=[],
    returns=[]
)
func_dict = {k: v for k, v in getmembers(function_base) if not k.startswith("_")}


def func_with(**kwargs):
    return Function(**(func_dict | kwargs))


# Check that we can successfully serialize and desrialize IR.


@pytest.mark.parametrize(
    "x",
    [
        attr_with(),
        attr_with(type="a string"),
        attr_with(
            type=[
                TypeXRefInternal("xx", ["a", "b"]),
                "x",
                TypeXRefExternal("blah", "pkg", "sfn", "qn"),
            ]
        ),
        attr_with(
            deprecated=True,
        ),
        attr_with(
            deprecated="a string",
        ),
        attr_with(
            deprecated=[
                DescriptionName("name"),
                DescriptionText("xx"),
                DescriptionCode("yy"),
            ],
        ),
        func_with(),
        func_with(params=[Param(name="fred", has_default=True, default="boof")]),
        func_with(
            params=[Param(name="fred", has_default=False)],
            returns=[
                Return(
                    type=[TypeXRefInternal("a", [])], description=[DescriptionText("x")]
                )
            ],
        ),
    ],
)
def test_ir_serialization(x):
    l = [x]
    s = converter.unstructure(l)
    s2 = loads(dumps(s))
    assert s == s2
    l2 = json_to_ir(s2)
    assert l2 == l
