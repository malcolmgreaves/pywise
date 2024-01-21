from typing import Tuple, Any, Type, List, Mapping

from pytest import fixture

from core_utils.support_for_testing import (
    SimpleGeneric,
    NestedGeneric,
    SimpleNoGen,
    NestedNoGen,
)

from core_utils.serialization import (
    serialize,
    deserialize,
    _align_generic_concrete,
)


@fixture(scope="module")
def simple_10() -> SimpleGeneric[int]:
    return SimpleGeneric(10)


@fixture(scope="module")
def simple_neg_2() -> SimpleGeneric[int]:
    return SimpleGeneric(-2)


@fixture(scope="module")
def simple_str() -> SimpleGeneric[str]:
    return SimpleGeneric("Hello world!")


@fixture(scope="module")
def nested_int_str(simple_10, simple_str) -> NestedGeneric[int, str]:
    return NestedGeneric(simple_10, simple_str)


@fixture(scope="module")
def nested_int_int(simple_10, simple_neg_2) -> NestedGeneric[int, int]:
    return NestedGeneric(simple_10, simple_neg_2)


def _rt(t: str, x: Any) -> None:
    _ = x
    assert eval(f"deserialize({t}, serialize(x)) == x")


def test_serialize_non_generic(simple_10, simple_neg_2, simple_str, nested_int_int, nested_int_str):
    for s in [simple_10, simple_neg_2, simple_str]:
        assert deserialize(SimpleGeneric, serialize(s)) == s
    for n in [nested_int_int, nested_int_str]:
        assert deserialize(NestedGeneric, serialize(n)) == n


def test_serialize_generic(simple_10, simple_neg_2, simple_str, nested_int_int, nested_int_str):
    for s in [simple_10, simple_neg_2]:
        _rt("SimpleGeneric[int]", s)
    _rt("SimpleGeneric[str]", simple_str)
    _rt("NestedGeneric[int,int]", nested_int_int)
    _rt("NestedGeneric[int, str]", nested_int_str)


def test_serialize_generic_complex_nested():
    x = NestedGeneric[
        str,
        NestedGeneric[
            int,
            NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]],
        ],
    ](
        SimpleGeneric[str](value="i am a str"),
        SimpleGeneric[
            NestedGeneric[
                int,
                NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]],
            ]
        ](
            value=NestedGeneric[
                int, NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]]
            ](
                v1=SimpleGeneric[int](value=999),
                v2=SimpleGeneric[NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]]](
                    value=NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]](
                        v1=SimpleGeneric[float](value=-1.0),
                        v2=SimpleGeneric[NestedGeneric[List[int], Mapping[str, int]]](
                            value=NestedGeneric[List[int], Mapping[str, int]](
                                v1=SimpleGeneric[List[int]](
                                    value=[0, 2, 4, 6, 8, 10],
                                ),
                                v2=SimpleGeneric[Mapping[str, int]](
                                    value={
                                        "hello": 0,
                                        "how": 78892,
                                        "are": -12561,
                                        "you?": 463,
                                    },
                                ),
                            )
                        ),
                    )
                ),
            )
        ),
    )

    d = deserialize(
        NestedGeneric[
            str,
            NestedGeneric[
                int,
                NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]],
            ],
        ],
        serialize(x),
    )
    assert d == x


def _align(x: Tuple[Type, Type], str_name: str, typ: Type) -> None:
    assert str(x[0]) == f"~{str_name}"
    assert x[1] == typ


def test_align_generic_concrete_one_level():
    x = list(_align_generic_concrete(SimpleGeneric[int]))
    assert len(x) == 1
    _align(x[0], "T", int)

    x = list(_align_generic_concrete(List[bytes]))
    assert len(x) == 1
    _align(x[0], "T", bytes)


def test_align_generic_concrete_two_level():
    x = list(_align_generic_concrete(NestedGeneric[str, float]))
    assert len(x) == 2
    _align(x[0], "A", str)
    _align(x[1], "B", float)

    x = list(_align_generic_concrete(Mapping[str, Any]))
    assert len(x) == 2
    _align(x[0], "KT", str)
    _align(x[1], "VT_co", Any)  # type: ignore


def test_align_generic_concrete_complex_nested():
    x = list(
        _align_generic_concrete(
            NestedGeneric[
                str,
                NestedGeneric[
                    int,
                    NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]],
                ],
            ]
        )
    )
    assert len(x) == 2
    _align(x[0], "A", str)
    _align(
        x[1],
        "B",
        NestedGeneric[
            int,
            NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]],
        ],
    )

    x = list(_align_generic_concrete(x[1][1]))
    assert len(x) == 2
    _align(x[0], "A", int)
    _align(x[1], "B", NestedGeneric[float, NestedGeneric[List[int], Mapping[str, int]]])

    x = list(_align_generic_concrete(x[1][1]))
    assert len(x) == 2
    _align(x[0], "A", float)
    _align(x[1], "B", NestedGeneric[List[int], Mapping[str, int]])

    x = list(_align_generic_concrete(x[1][1]))
    assert len(x) == 2
    _align(x[0], "A", List[int])
    _align(x[1], "B", Mapping[str, int])

    x_list = list(_align_generic_concrete(x[0][1]))
    assert len(x_list) == 1
    _align(x_list[0], "T", int)

    x_map = list(_align_generic_concrete(x[1][1]))
    assert len(x_map) == 2
    _align(x_map[0], "KT", str)
    _align(x_map[1], "VT_co", int)


def test_generic_wo_holes():
    x = SimpleNoGen[float](10, "hello")
    assert deserialize(SimpleNoGen[float], serialize(x)) == x
    assert deserialize(SimpleNoGen, serialize(x)) == x
    assert deserialize(SimpleNoGen[Any], serialize(x)) == x

    x = NestedNoGen[bytes, type, list](  # type: ignore
        group_name="The Three Stooges",
        a=SimpleNoGen[bytes](age=109, name="Mo"),  # type: ignore
        b=SimpleNoGen[bytes](age=42, name="Larry"), # type: ignore
        c=SimpleNoGen[bytes](age=-6, name="Curly"),  # type: ignore
    )
    assert deserialize(NestedNoGen[bytes, type, list], serialize(x)) == x
    assert deserialize(NestedNoGen, serialize(x)) == x
    assert deserialize(NestedNoGen[Any, Any, Any], serialize(x)) == x
