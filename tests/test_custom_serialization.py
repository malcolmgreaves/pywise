import json
from typing import Tuple

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
    def check(*, actual, expected):
        assert isinstance(
            actual, type(expected)
        ), f"Expecting {type(expected)} recieved {type(actual)}"
        assert (expected == actual).all()  # type: ignore

    def roundtrip(a):
        s1 = serialize(a, custom=cs)
        d1 = deserialize(type(a), s1, custom=cd)
        check(actual=d1, expected=a)
        j = json.dumps(s1)
        s2 = json.loads(j)
        d2 = deserialize(type(a), s2, custom=cd)
        check(actual=d2, expected=a)

    roundtrip(np.zeros(simple_len))

    for _ in range(n_rando_times):
        arr = make(multi_shape)
        roundtrip(arr)


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
