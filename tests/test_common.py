from dataclasses import dataclass
from pathlib import Path
from typing import (
    NamedTuple,
    Union,
    Optional,
    Generic,
    TypeVar,
    Sequence,
    Mapping,
    Dict,
    List,
)

import typing
from pytest import raises

from core_utils.common import type_name, import_by_name, checkable_type


class NTX(NamedTuple):
    name: str


A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


class WithTypeParams(Generic[A, B, C]):
    pass


class Constrained(WithTypeParams[str, int, NTX]):
    pass


@dataclass
class DTX:
    name: str


def test_type_name():
    class X:
        pass

    # _t = "tests."
    _t = ""

    tests = [
        (str, "str"),
        (float, "float"),
        (int, "int"),
        (Path, "pathlib.Path"),
        (NTX, f"{_t}test_common.NTX"),
        (DTX, f"{_t}test_common.DTX"),
        (Union[float, str], "typing.Union[float, str]"),
        (Optional[int], "typing.Optional[int]"),
        (ValueError, "ValueError"),
        (X, f"{_t}test_common.X"),
        (Constrained, f"{_t}test_common.Constrained"),
        (
            WithTypeParams[float, int, NTX],
            f"{_t}test_common.WithTypeParams[float, int, {_t}test_common.NTX]",
        ),
        (
            WithTypeParams[float, int, DTX],
            f"{_t}test_common.WithTypeParams[float, int, {_t}test_common.DTX]",
        ),
    ]
    for inp, expected in tests:
        actual = type_name(inp)
        assert actual == expected, f"Failed for {inp}"


def test_import_by_name():
    with raises(ValueError):
        import_by_name("           ", validate=True)

    with raises(ModuleNotFoundError):
        import_by_name("_invalid_", validate=False)

    for x in [int, dict, float, str, list, bool]:
        t = type_name(x)
        l = import_by_name(f"builtins.{t}")
        assert l == x
        l = import_by_name(t)
        assert l == x

    assert Constrained == import_by_name(f"{_t}test_common.Constrained")

    assert typing == import_by_name("typing")


def test_checkable_type():
    assert int == checkable_type(int)
    assert NTX == checkable_type(NTX)
    assert DTX == checkable_type(DTX)
    assert Sequence == checkable_type(Sequence)
    assert Sequence == checkable_type(Sequence[int])
    assert Mapping == checkable_type(Mapping[str, Sequence[int]])
    assert Dict == checkable_type(Dict[str, Sequence[int]])
    assert List == checkable_type(List[List[List[str]]])
