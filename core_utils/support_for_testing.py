from dataclasses import dataclass
from typing import Generic, TypeVar, Tuple

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
