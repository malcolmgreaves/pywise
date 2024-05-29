import time
from datetime import timedelta

from core_utils.loggers import print_logger
from core_utils.timer import Timer, timeit


def test_timeit():
    with timeit(name="testing timer") as t:
        time.sleep(0.01)
    assert t.duration > 0.0


def test_timer():
    with Timer(logger=print_logger()) as t:
        time.sleep(0.01)
    assert t.timedelta > timedelta(seconds=0)


def test_comparisons():
    with timeit() as t2:
        time.sleep(0.01)
        with timeit() as t1:
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
    assert abs(t1) > 0
