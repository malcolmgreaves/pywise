import io
import json
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import NamedTuple, Sequence, Optional, Mapping, Set, Tuple, Union, Any

from pytest import raises, fixture
import yaml


from core_utils.serialization import (
    serialize,
    deserialize,
    is_namedtuple,
    is_typed_namedtuple,
    _namedtuple_from_dict,
    _is_optional,
    FieldDeserializeFail,
    _dataclass_from_dict,
    MissingRequired,
)


@dataclass(frozen=True)
class YAML:
    def dumps(self, obj: Any) -> str:
        wt = io.StringIO()
        yaml.safe_dump(obj, wt)
        return wt.getvalue()

    def loads(self, string_data: str) -> Any:
        rt = io.StringIO(string_data)
        rt.seek(0)
        return yaml.safe_load(rt)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                        Shared Test Helpers                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@fixture(scope="module")
def yaml_handler() -> YAML:
    return YAML()


E1 = Enum("E1", ["a", "b", "c"])


class UnserializableObject:
    pass


class E2(Enum):
    a = UnserializableObject()
    b = UnserializableObject()
    c = UnserializableObject()


class E3(IntEnum):
    a, b, c = range(3)


class E4(Enum):
    a = "a"
    b = "b"
    c = "c"


def _test_serialize_t(t, v):
    assert serialize(t(v)) == {"x": v}


def _test_deserialize_t(t, v):
    assert deserialize(t, {"x": v}) == t(v)


def _test_roundtrip(s, t, v, expected_str):
    assert deserialize(t, s.loads(s.dumps(serialize(t(v))))) == t(
        v
    ), "From object to serialized format and back"

    assert (
        s.dumps(serialize(deserialize(t, s.loads(expected_str)))) == expected_str
    ), "From format to object and back."

    assert deserialize(t, serialize(deserialize(t, serialize(t(v))))) == t(
        v
    ), "Ensure serialize & deserialize RTs are idempotent."


def test_is_optional():
    assert _is_optional(Optional[int])
    assert not _is_optional(int)
    assert _is_optional(Union[str, float, None])
    assert not _is_optional(Union[str, float])


def _test_fail_deserialize_field_except(t):
    with raises(FieldDeserializeFail):
        deserialize(t, {"age": "hi!", "score": 10})

    with raises(FieldDeserializeFail):
        deserialize(t, {"age": 10.5, "score": 0.0})

    with raises(MissingRequired):
        deserialize(t, {"age": 10})
    deserialize(t, {"age": 10.0, "score": 100.0})
    deserialize(t, {"age": 10, "score": 100.0})
    deserialize(t, {"age": 10, "score": 100})


def _test_fail_deserialize_seq_field_except(t):
    with raises(FieldDeserializeFail):
        d = {"elements": None}
        deserialize(t, d)

    with raises(FieldDeserializeFail):
        d = {"elements": 1.0}
        deserialize(t, d)

    with raises(MissingRequired):
        d = {"world": "hello"}
        deserialize(t, d)


def _test_union_deserialization(X1, LS):
    s = """{"values": {"class_name": "Foobar"}}"""
    x1 = deserialize(X1, json.loads(s))
    assert isinstance(x1, X1)
    assert isinstance(x1.values, LS)

    s = """{"values": 1}"""
    x1 = deserialize(X1, json.loads(s))
    assert isinstance(x1, X1)
    assert isinstance(x1.values, int)
    assert x1.values == 1

    s = """{"values": {"class_name": "Foobar", "args": {"something": 10.0, "else": "world!"}}}"""
    x1 = deserialize(X1, json.loads(s))
    assert isinstance(x1, X1)
    assert isinstance(x1.values, LS)

    with raises(FieldDeserializeFail):
        s = """{"values": {"what": "is this?"}}"""
        deserialize(X1, json.loads(s))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                           NamedTuple Tests                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


nt = namedtuple("nt", ["x"])
NT = NamedTuple("NT", [("x", int)])


class Complex(NamedTuple):
    name: str
    nts: Sequence[NT]
    opt_nt: Optional[nt]
    lookup: Mapping[str, int]
    membership: Set[str]
    nested: Sequence[Sequence[int]]


def test_is_namedtuple():
    assert is_namedtuple(nt(10))
    assert is_namedtuple(NT(10))
    assert not is_namedtuple(10)
    assert not is_namedtuple(None)
    assert not is_namedtuple((1, 2, 3, 4, 5))

    class Y(NamedTuple):
        pass

    class Z:
        pass

    assert is_namedtuple(Y())
    assert is_namedtuple(Y)
    assert not is_namedtuple(Z())
    assert not is_namedtuple(Z)

    class Baz(tuple):
        pass

    assert not is_namedtuple(Baz)
    assert not is_namedtuple(Baz())

    class Foo(tuple):
        def _make(self):
            raise NotImplementedError

        _fields: int = 10

    assert not is_namedtuple(Foo)
    assert not is_namedtuple(Foo())


def test_is_typed_namedtuple():
    assert not is_typed_namedtuple(nt(10))
    assert is_typed_namedtuple(NT(10))
    assert not is_typed_namedtuple(10)
    assert not is_typed_namedtuple(None)
    assert not is_typed_namedtuple((1, 2, 3, 4, 5))

    class Y(NamedTuple):
        pass

    class Z:
        pass

    assert is_typed_namedtuple(Y)
    assert is_typed_namedtuple(Y())
    assert not is_typed_namedtuple(Z)
    assert not is_typed_namedtuple(Z())


def test_serialize_namedtuple():
    _test_serialize_t(NT, 10)


def test_deserialize_namedtuple():
    _test_deserialize_t(NT, 10)


def test_round_trip_json_serialization_namedtuple(yaml_handler):
    for v in [-1, 0, 50]:
        _test_roundtrip(json, NT, v, '{"x": ' + f"{v}" + "}")
        _test_roundtrip(yaml_handler, NT, v, f"x: {v}\n")


def test_complex_serialization_nt():
    c0 = Complex(
        name="c0",
        nts=[NT(1), NT(2), NT(3)],
        opt_nt=None,
        lookup={"hello": 23, "world": 42, "where is my super suit?": -1},
        membership={"dandy", "randy"},
        nested=[[5, 4, 3], [2], [1], [0, -1]],
    )
    assert deserialize(Complex, serialize(c0)) == c0
    j = json.dumps(serialize(c0))
    assert deserialize(Complex, json.loads(j)) == c0


def test_tuple_serialization():
    T = NamedTuple("T", [("t", Tuple[int, int, int])])
    x = T((1, 2, 3))
    assert deserialize(T, serialize(x)) == x


def test_namedtuple_from_dict_fail():
    with raises(TypeError):
        _ = _namedtuple_from_dict(int, 10)  # type: ignore


def test_deserialize_optional_field_not_present_nt():
    class C(NamedTuple):
        name: str
        artifact: Optional[str]

    j = """[
    {
        "name": "jenny",
        "artifact": "s3://hello/world.txt"
    },
    {
        "name": "jason"
    }
    ]"""
    expected = [C("jenny", "s3://hello/world.txt"), C("jason", None)]
    actual = deserialize(Sequence[C], json.loads(j))
    assert actual == expected


def test_serialize_deserialize_enum_nt():
    class N1(NamedTuple):
        e: E1

    class N2(NamedTuple):
        e: E2

    class N3(NamedTuple):
        e: E3

    class N4(NamedTuple):
        e: E4

    for enum_type, nt_type in [(E1, N1), (E2, N2), (E3, N3), (E4, N4)]:
        for value in enum_type:
            nt = nt_type(value)

            s = serialize(nt)
            d = deserialize(nt_type, s)
            assert isinstance(d, nt_type)
            assert d == nt

            j = json.dumps(s)
            s = json.loads(j)
            d = deserialize(nt_type, s)
            assert isinstance(d, nt_type)
            assert d == nt


class NTX(NamedTuple):
    age: int
    score: float


class NTL(NamedTuple):
    elements: Sequence[NTX]


def test_fail_deserialize_field_except_nt():
    _test_fail_deserialize_field_except(NTX)


def test_fail_deserialize_seq_field_except_nt():
    _test_fail_deserialize_seq_field_except(NTL)


def test_union_deserialization_nt():
    class LS_NT(NamedTuple):
        class_name: str
        args: Optional[Mapping[str, Any]]

    class X1_NT(NamedTuple):
        values: Union[LS_NT, int]

    _test_union_deserialization(X1_NT, LS_NT)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                            Dataclass Tests                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@dataclass
class DT:
    x: int


@dataclass
class ComplexDc:
    name: str
    nts: Sequence[DT]
    opt_nt: Optional[DT]
    lookup: Mapping[str, int]
    membership: Set[str]
    nested: Sequence[Sequence[int]]


def test_serialize_dataclass():
    _test_serialize_t(DT, 10)


def test_deserialize_dataclass():
    _test_deserialize_t(DT, 10)


def test_round_trip_json_serialization_dataclass(yaml_handler):
    for v in [-1, 0, 50]:
        _test_roundtrip(json, DT, v, '{"x": ' + f"{v}" + "}")
        _test_roundtrip(yaml_handler, DT, v, f"x: {v}\n")


def test_complex_serialization_dc():
    c0 = ComplexDc(
        name="c0",
        nts=[DT(1), DT(2), DT(3)],
        opt_nt=None,
        lookup={"hello": 23, "world": 42, "where is my super suit?": -1},
        membership={"dandy", "randy"},
        nested=[[5, 4, 3], [2], [1], [0, -1]],
    )
    assert deserialize(ComplexDc, serialize(c0)) == c0
    j = json.dumps(serialize(c0))
    assert deserialize(ComplexDc, json.loads(j)) == c0


def test_dc_from_dict_fail():
    with raises(TypeError):
        _ = _dataclass_from_dict(int, 10)  # type: ignore


def test_serialize_deserialize_enum_dc():
    @dataclass
    class D1:
        e: E1

    @dataclass
    class D2:
        e: E2

    @dataclass
    class D3:
        e: E3

    @dataclass
    class D4:
        e: E4

    for enum_type, dc_type in [(E1, D1), (E2, D2), (E3, D3), (E4, D4)]:
        for value in enum_type:
            nt = dc_type(value)

            s = serialize(nt)
            d = deserialize(dc_type, s)
            assert isinstance(d, dc_type)
            assert d == nt

            j = json.dumps(s)
            s = json.loads(j)
            d = deserialize(dc_type, s)
            assert isinstance(d, dc_type)
            assert d == nt


@dataclass
class DTX:
    age: int
    score: float


@dataclass
class DTL:
    elements: Sequence[DTX]


def test_fail_deserialize_field_except_dc():
    _test_fail_deserialize_field_except(DTX)


def test_fail_deserialize_seq_field_except_dc():
    _test_fail_deserialize_seq_field_except(DTL)


def test_union_deserialization_dc():
    @dataclass
    class LS_DC:
        class_name: str
        args: Optional[Mapping[str, Any]]

    @dataclass
    class X1_DC:
        values: Union[LS_DC, int]

    _test_union_deserialization(X1_DC, LS_DC)
