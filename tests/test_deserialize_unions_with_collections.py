import pytest

from core_utils.serialization import serialize, deserialize
from dataclasses import dataclass
from typing import Union, Sequence, Mapping


@dataclass(frozen=True)
class A:
    a: int


@dataclass(frozen=True)
class B:
    b: str


@dataclass(frozen=True)
class C:
    c: Union[A, B, Sequence[A], Sequence[B], Mapping[int, str]]


@pytest.mark.parametrize(
    "c_input",
    [
        # "simple" dataclass cases
        C(A(1)),
        C(B("hello world")),
        # list cases
        C([A(1)]),
        C([B("hello world")]),
        C([A(1), A(2), A(4)]),
        C([B("a"), B("b"), B("c")]),
        C([]),
        # dict cases
        C({0: "hello", 1: "world", 2: "how", 3: "are", 4: "you"}),
        C(dict()),
    ],
)
def test_deserialize_dataclass_with_union_of_collections(c_input: C) -> None:
    assert deserialize(C, serialize(c_input)) == c_input
