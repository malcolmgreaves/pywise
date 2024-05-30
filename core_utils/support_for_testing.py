"""THIS MODULE WILL *NEVER* BE PUBLISHED.

It exists to provide @dataclass definitions to test parameterized generic deserialization.
Classes cannot be defined in the `test/` directory and be used by `deserialize`:
they are not in a defined package and thus will not be available in the environment.

The workaround is to define them here and then, in pyproject.toml, ensure that this file
is excluded from the build process.
"""

import logging
from dataclasses import dataclass, field
from typing import Generic, List, Sequence, TypeVar

from core_utils.loggers import LogLevelInt

T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")

__all__: Sequence[str] = ()  # do not support wildcard imports


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
    group_name: str
    a: SimpleNoGen[T]
    b: SimpleNoGen[A]
    c: SimpleNoGen[B]


@dataclass
class MockLogger:
    internal: List[str] = field(default_factory=lambda: [])
    level: LogLevelInt = logging.DEBUG  # type: ignore

    def debug(self, x: str) -> None:
        if self.level <= logging.DEBUG:
            self.internal.append(x)

    def info(self, x: str) -> None:
        if self.level <= logging.INFO:
            self.internal.append(x)

    def warning(self, x: str) -> None:
        if self.level <= logging.WARNING:
            self.internal.append(x)

    def error(self, x: str) -> None:
        if self.level <= logging.ERROR:
            self.internal.append(x)

    def fatal(self, x: str) -> None:
        # always print! max level is FATAL
        self.internal.append(x)

    def setLevel(self, level: LogLevelInt) -> None:
        self.level = level
