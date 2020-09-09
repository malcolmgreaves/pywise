"""THIS MODULE WILL *NEVER* BE PUBLISHED.

It exists to provide @dataclass definitions to test parameterized generic deserialization.
Classes cannot be defined in the `test/` directory and be used by `deserialize`:
they are not in a defined package and thus will not be available in the environment.

The workaround is to define them here and then, in pyproject.toml, ensure that this file
is excluded from the build process.
"""
from dataclasses import dataclass
from typing import Generic, TypeVar

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


@dataclass(frozen=True)
class SimpleNoGen(Generic[T]):
    age: int
    name: str


@dataclass(frozen=True)
class NestedNoGen(Generic[T, A, B]):
    mo: SimpleNoGen[T]
    larry: SimpleNoGen[A]
    curly: SimpleNoGen[B]
