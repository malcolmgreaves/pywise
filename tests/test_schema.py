import json
from typing import NamedTuple, Sequence, Optional, Mapping
from dataclasses import dataclass

from core_utils.schema import dict_type_representation


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                        Shared Test Helpers                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
from core_utils.serialization import serialize


def _test_pretty_fmt(t):
    tests = [
        (
            t("Xander", 9999),
            """
{
    "name": "Xander",
    "age": 9999
}
            """.strip(),
        )
    ]
    for x, expected in tests:
        assert json.dumps(serialize(x), indent=4) == expected


def _test_simple_dict_type_representation(t):
    expected = {"name": "str", "age": "int"}
    assert dict_type_representation(t) == expected


def _test_more_complex_dict_type_representation(t):
    t_expected = {"name": "str", "age": "int"}
    expected = {
        "priority": t_expected,
        "secondaries": [t_expected],
        "level": "int",
        "extra": {"str": "float"},
    }
    assert dict_type_representation(t) == expected


def _test_with_optional_dict_type_representation(t):
    expected = {"level": "int", "maybe": "typing.Union[int, NoneType]"}
    assert dict_type_representation(t) == expected


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                           NamedTuple Tests                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class NT(NamedTuple):
    name: str
    age: int


def test_pretty_fmt_namedtuple():
    _test_pretty_fmt(NT)


def test_simple_dict_type_representation_namedtuple():
    _test_simple_dict_type_representation(NT)


class NTX(NamedTuple):
    priority: NT
    secondaries: Sequence[NT]
    level: int
    extra: Mapping[str, float]


def test_more_complex_dict_type_representation_namedtuple():
    _test_more_complex_dict_type_representation(NTX)


class NTO(NamedTuple):
    level: int
    maybe: Optional[int]


def test_with_optional_dict_type_representation_namedtuple():
    _test_with_optional_dict_type_representation(NTO)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                            Dataclass Tests                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@dataclass
class DT:
    name: str
    age: int


def test_pretty_fmt_dataclass():
    _test_pretty_fmt(DT)


def test_simple_dict_type_representation_dataclass():
    _test_simple_dict_type_representation(DT)


@dataclass
class DTX:
    priority: DT
    secondaries: Sequence[DT]
    level: int
    extra: Mapping[str, float]


def test_more_complex_dict_type_representation_dataclass():
    _test_more_complex_dict_type_representation(DTX)


@dataclass
class DTO:
    level: int
    maybe: Optional[int]


def test_with_optional_dict_type_representation_dataclass():
    _test_with_optional_dict_type_representation(DTO)
