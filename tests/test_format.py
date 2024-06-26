from typing import Sequence

import pytest

from core_utils.format import (
    evenly_space,
    exception_stacktrace,
    format_stacktrace,
    program_init_param_msg,
)
from core_utils.support_for_testing import MockLogger


@pytest.fixture(scope="module")
def message() -> Sequence[str]:
    return ["hello", "world", "how", "are", "you", "today?"]


@pytest.mark.parametrize("log_each_line", [True, False])
def test_program_init_param_msg_no_name(message, log_each_line):
    log = MockLogger()
    program_init_param_msg(log, message, name=None, log_each_line=log_each_line)  # type: ignore
    assert (
        "\n".join(log.internal).strip()
        == """
------
hello
world
how
are
you
today?
------""".strip()
    )


def test_program_init_param_msg_name_no_log_each_line(message):
    log = MockLogger()
    program_init_param_msg(log, message, name="my program", log_each_line=False)  # type: ignore
    assert (
        "\n".join(log.internal).strip()
        == """
my program
------
hello
world
how
are
you
today?
------""".strip()
    )


def test_evenly_space():
    terms = [
        ("hello", 52),
        ("what do we have", "here?"),
        ("something good?", None),
    ]
    results = evenly_space(terms)
    assert "\n".join(results) == (
        """
hello:           52
what do we have: here?
something good?: None
""".strip()
    )

    assert evenly_space([]) == []


def test_program_init_param_msg_name_log_each_line(message):
    log = MockLogger()
    program_init_param_msg(log, message, name="my program", log_each_line=True)  # type: ignore
    assert (
        "\n".join(log.internal).strip()
        == """
------
my program
hello
world
how
are
you
today?
------""".strip()
    )


def _helper_raise():
    raise ValueError()


def test_exception_stacktrace():
    try:
        _helper_raise()
    except ValueError as error:
        stacktrace_lines = exception_stacktrace(error)
        marker_1 = False
        marker_2 = False
        for s in stacktrace_lines:
            if "in test_exception_stacktrace" in s:
                marker_1 = True
            if "in _helper_raise" in s:
                marker_2 = True
        assert marker_1
        assert marker_2


def test_format_stacktrace():
    try:
        _helper_raise()
    except ValueError as error:
        s = format_stacktrace(error)
        assert "in test_format_stacktrace" in s
        assert "in _helper_raise" in s
