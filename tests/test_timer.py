import time
from datetime import timedelta

from pytest import raises

from core_utils.loggers import print_logger
from core_utils.timer import timer


def test_timer():
    with timer(logger=print_logger(), name="testing_timer_class") as t:
        time.sleep(0.01)
    assert t.timedelta > timedelta(seconds=0)
    assert f"{t:0.02f}s" == "0.01s"


def test_timer_fail():
    with raises(ValueError):
        t = timer()
        t.__exit__()

    with timer() as t:
        pass
    with raises(ValueError):
        with t:
            pass

    with raises(ValueError):
        with timer() as t:
            _ = t.duration


def test_comparisons():
    with timer() as t2:
        time.sleep(0.01)
        with timer() as t1:
            time.sleep(0.01)
    assert t2 > t1
    assert t2 >= t1
    assert t1 < t2
    assert t1 <= t2
    assert t1 == t1
    assert t2 != t1
    assert t2 - t1 < t2.duration
    assert t1 + t1 > 0.0
    assert t1 * t1 > 0.0
    assert t1 / t1 <= 1.0
    assert t1 / (int(t1) + 1) > 0
    assert int(t1) / (int(t1) + 1) == 0
    assert t1 // (int(t1) + 1) == 0
    assert abs(t1) > 0
