import json
from dataclasses import dataclass
from typing import Tuple, NamedTuple, Mapping, Sequence, Dict, List

import numpy as np
import torch
from pytest import fixture

from core_utils.serialization import CustomFormat, serialize, deserialize


@fixture(scope="module")
def custom_serialize() -> CustomFormat:
    np_ser = lambda arr: arr.tolist()
    return {
        np.ndarray: np_ser,
        torch.Tensor: lambda tnsr: np_ser(tnsr.detach().cpu().numpy()),
    }


@fixture(scope="module")
def custom_deserialize() -> CustomFormat:
    np_deser = lambda lst: np.array(lst)
    return {
        np.ndarray: np_deser,
        torch.Tensor: lambda lst: torch.from_numpy(np_deser(lst)),
    }


@fixture(scope="module")
def simple_test_array_length() -> int:
    return 5


@fixture(scope="module")
def times_for_random_value_array_test() -> int:
    return 10


@fixture(scope="module")
def multi_dim_shape() -> Tuple[int, int, int, int, int]:
    return 2, 6, 3, 15, 4


def _test_procedue(cs, cd, simple_len, n_rando_times, multi_shape, make):
    roundtrip = lambda a: _roundtrip(a, cs, cd, _check_array_like)

    roundtrip(np.zeros(simple_len))

    for _ in range(n_rando_times):
        arr = make(multi_shape)
        roundtrip(arr)


def _roundtrip(a, cs, cd, check):
    s1 = serialize(a, custom=cs)
    d1 = deserialize(type(a), s1, custom=cd)
    check(actual=d1, expected=a)
    j = json.dumps(s1)
    s2 = json.loads(j)
    d2 = deserialize(type(a), s2, custom=cd)
    check(actual=d2, expected=a)


def _check_array_like(*, actual, expected):
    assert isinstance(
        actual, type(expected)
    ), f"Expecting {type(expected)} recieved {type(actual)}"
    assert (expected == actual).all()  # type: ignore


def test_serialization_numpy_array(
    custom_serialize,
    custom_deserialize,
    simple_test_array_length,
    times_for_random_value_array_test,
    multi_dim_shape,
):
    _test_procedue(
        custom_serialize,
        custom_deserialize,
        simple_test_array_length,
        times_for_random_value_array_test,
        multi_dim_shape,
        lambda s: np.random.random(s),
    )


def test_serialization_torch_tensor(
    custom_serialize,
    custom_deserialize,
    simple_test_array_length,
    times_for_random_value_array_test,
    multi_dim_shape,
):
    _test_procedue(
        custom_serialize,
        custom_deserialize,
        simple_test_array_length,
        times_for_random_value_array_test,
        multi_dim_shape,
        lambda s: torch.from_numpy(np.random.random(s)),
    )


def test_custom_serialize_map(custom_serialize, custom_deserialize, multi_dim_shape):
    class MNT(NamedTuple):
        field: Mapping[str, np.ndarray]

    @dataclass(frozen=True)
    class MDC:
        field: Mapping[str, np.ndarray]

    mnt = MNT(field={"an_id": np.random.random(multi_dim_shape)})
    mdc = MDC(field={"an_id": np.random.random(multi_dim_shape)})

    def check(*, actual, expected):
        assert isinstance(actual, type(expected))
        assert "an_id" in actual.field
        _check_array_like(
            actual=actual.field["an_id"], expected=expected.field["an_id"]
        )

    _roundtrip(mnt, custom_serialize, custom_deserialize, check)
    _roundtrip(mdc, custom_serialize, custom_deserialize, check)


def test_custom_serialize_iterable(
    custom_serialize, custom_deserialize, multi_dim_shape
):
    class MNT(NamedTuple):
        field: Sequence[np.ndarray]

    @dataclass(frozen=True)
    class MDC:
        field: Sequence[np.ndarray]

    mnt = MNT(
        field=[np.random.random(multi_dim_shape), np.random.random(multi_dim_shape)]
    )
    mdc = MDC(
        field=[np.random.random(multi_dim_shape), np.random.random(multi_dim_shape)]
    )

    def check(*, actual, expected):
        assert isinstance(actual, type(expected))
        for a, e in zip(actual.field, expected.field):
            _check_array_like(actual=a, expected=e)

    _roundtrip(mnt, custom_serialize, custom_deserialize, check)
    _roundtrip(mdc, custom_serialize, custom_deserialize, check)


def test_nested_array_dict_int_keys(custom_serialize, custom_deserialize):
    N = 4
    M = 3

    def check(*, actual, expected):
        assert isinstance(actual, type(expected))
        assert len(actual) == N
        for xs in actual:
            assert len(xs) == M
            for i, arr in xs.items():
                assert isinstance(i, int)
                _check_array_like(actual=arr, expected=np.ones(i))

    m: List[List[Dict[int, np.ndarray]]] = [
        [{i: np.ones(i)} for i in range(M)] for _ in range(N)
    ]

    _roundtrip(m, custom_serialize, custom_deserialize, check)
