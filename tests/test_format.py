from dataclasses import dataclass, field
from typing import List, Sequence

import pytest

from core_utils.format import program_init_param_msg


@dataclass
class MockLogger:
    internal: List[str] = field(default_factory=lambda: [])

    def info(self, x: str) -> None:
        self.internal.append(x)


@pytest.fixture(scope='module')
def message() -> Sequence[str]:
    return ['hello', 'world', 'how', 'are', 'you', 'today?']

def test_program_init_param_msg(message):
    log = MockLogger()
    program_init_param_msg(log, message, name=None, log_each_line=False)  # type: ignore
    assert log.internal
