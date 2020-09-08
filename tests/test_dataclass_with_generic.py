from dataclasses import dataclass
from typing import Generic, TypeVar, Tuple, Any, Type, List, Mapping

from pytest import fixture

from core_utils.serialization import (
    serialize,
    deserialize,
)

T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True)
class SimpleGeneric(Generic[T]):
    value: T


@dataclass(frozen=True)
class NestedGeneric(Generic[A, B]):
    v1: SimpleGeneric[A]
    v2: SimpleGeneric[B]

    @property
    def values(self) -> Tuple[A, B]:
        return self.v1.value, self.v2.value


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


def test_serialize_non_generic(
    simple_10, simple_neg_2, simple_str, nested_int_int, nested_int_str
):
    for s in [simple_10, simple_neg_2, simple_str]:
        assert deserialize(SimpleGeneric, serialize(s)) == s
    for n in [nested_int_int, nested_int_str]:
        assert deserialize(NestedGeneric, serialize(n)) == n


def test_serialize_generic(
    simple_10, simple_neg_2, simple_str, nested_int_int, nested_int_str
):
    for s in [simple_10, simple_neg_2]:
        _rt("SimpleGeneric[int]", s)
    _rt("SimpleGeneric[str]", simple_str)
    _rt("NestedGeneric[int,int]", nested_int_int)
    _rt("NestedGeneric[int, str]", nested_int_str)
