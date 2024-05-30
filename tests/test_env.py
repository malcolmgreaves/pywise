import os
from functools import partial
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

import pytest

from core_utils.env import Environment, to_environment_value


def _expect_not_present(e: str) -> None:
    assert (
        e not in os.environ
    ), f"Not expecting env var {e} to be present, instead found {os.environ[e]}"


def _expect_present(e: str, value: Any) -> None:
    assert e in os.environ, f"Expecting env var {e} to be present with {value}"
    assert (
        os.environ[e] == value
    ), f"Expected env var {e} to have value {value} but instead found {os.environ[e]}"


def _prepare(e: str, existing: Optional[str]) -> Callable[[], None]:
    if existing is not None:
        os.environ[e] = existing
        return partial(_expect_present, e, existing)
    else:
        return partial(_expect_not_present, e)


def test_environment_kwarg():
    e = "ENV_VAR_TEST"
    _expect_not_present(e)
    # NOTE: This is to test keyword argument use.
    #       Make sure this **literal value** is the same as `e`'s contents.
    with Environment(ENV_VAR_TEST="x"):
        _expect_present(e, "x")
    _expect_not_present(e)


@pytest.mark.parametrize("existing", ["env var has prior value", None])
def test_environment_normal_cases(existing):
    e = f"___{uuid4()}-test_env_var"
    check = _prepare(e, existing)

    check()
    new = f"{uuid4()}--hello_world"
    with Environment(**{e: new}):
        _expect_present(e, new)
    check()


def test_environment_unset():
    k = f"___{uuid4()}___--test_unset_env_var--"
    v = "hello world! how are you doing today?"
    # when there is a previous value
    try:
        os.environ[k] = v
        with Environment(**{k: None}):
            assert k not in os.environ
        assert k in os.environ
        assert os.environ[k] == v
    finally:
        del os.environ[k]

    # when there is not a previous value
    assert k not in os.environ
    with Environment(**{k: None}):
        assert k not in os.environ
    assert k not in os.environ


def test_environment_multi():
    env_vars: Dict[str, str] = {f"___{uuid4()}-test_env_var--{i}": f"value_{i}" for i in range(100)}

    def ok():
        for e in env_vars.keys():
            _expect_not_present(e)

    ok()
    with Environment(**env_vars):
        for e, v in env_vars.items():
            _expect_present(e, v)
    ok()


def test_environment_invalid_states():
    with pytest.raises(ValueError):
        Environment(**{"": "2"})


@pytest.mark.parametrize("existing", ["env var has prior value", None])
def test_environment_with_exception(existing):
    e = f"___{uuid4()}-test_env_var"
    check = _prepare(e, existing)

    check()
    new = f"{uuid4()}--hello_world"
    with pytest.raises(ValueError):
        with Environment(**{e: new}):
            _expect_present(e, new)
            raise ValueError("Uh oh! Something went wrong in our context!")
    # unreachable
    check()  # type: ignore


def test_environment_manual():
    e = "hello123"
    assert e not in os.environ
    env = Environment(**{e: "world"})
    assert e not in os.environ
    env.set()
    assert e in os.environ
    assert os.environ[e] == "world"
    env.unset()
    assert e not in os.environ


@pytest.mark.parametrize(
    "input_,expected",
    [
        (None, None),
        ("hello", "hello"),
        (True, "1"),
        (False, "0"),
        (9999, "9999"),
        (-1234.982, "-1234.982"),
        ("goodbye".encode("utf8"), "goodbye"),
    ],
)
def test_to_environment_value(input_, expected):
    actual = to_environment_value(input_)
    assert actual == expected


def test_to_environment_value_failing():
    with pytest.raises(ValueError):
        to_environment_value(["not, ok"])  # type: ignore
