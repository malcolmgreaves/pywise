"""Utilities for timing code blocks."""

import inspect
import time
from datetime import timedelta
from logging import Logger
from types import FrameType
from typing import Optional, Sequence

__all__: Sequence[str] = ("Timer",)


class Timer:  # pylint: disable=invalid-name
    """Context manager for timing a block of code.

    Example use case -- consider timing a function `f`:

    >>> def long_computation(n_seconds: int = 1) -> None:
    >>> # simulate lots of computation by waiting
    >>>     time.sleep(n_seconds)

    Directly use the timer and access the `duration` attribute after the context block has finished:

    >>> with Timer() as timing_block:
    >>>     long_computation()
    >>> print(f"{timing_block.duration:0.4f}s")

    Note that the duration is in seconds. It is a `float`: it can represent fractional seconds.

    The other use case is to pass in a `name` and a standard `logging.Logger` instance.
    The timing will be recorded when the context block is exited:

    >>> from logging import Logger
    >>>
    >>> log: Logger = ...
    >>>
    >>> with Timer(logger=log, name="timing long_computation(10)"):
    >>>     long_computation(n_seconds=10)
    """

    __slots__ = ("_logger", "_name", "_duration", "_start")

    def __init__(self, logger: Optional[Logger] = None, name: str = "") -> None:
        self._logger = logger
        self._name = name
        self._duration: Optional[float] = None
        # for start, -1 is the uninitialized value
        # it is set at the context-block qentering method: __enter__
        self._start: float = -1.0

    def __enter__(self) -> "Timer":
        """Captures start time.

        Raises a `ValueError`
        """
        if self._start != -1.0:
            raise ValueError("Cannot restart timing: create a new Timer for each managed context!")
        self._start = time.monotonic()
        # avoid any code execution *after* recording start
        return self

    def __exit__(self, *args) -> None:
        """Stores end time.

        Raises a `ValueError` iff this is called before `__enter__` (i.e. before context block is entered).
        """
        # calculate the duration *first*
        # CRITICAL: do not introduce any additional latency in this timing measurement
        self._duration = time.monotonic() - self._start
        # i.e. validation occurs after
        if self._start == -1:
            raise ValueError("Must start timing before recording end!")
        self._maybe_log_end_time()

    def _maybe_log_end_time(self) -> None:
        if self._logger is not None:
            caller_namespace = "<unknown_caller_namespace>"
            frame: Optional[FrameType] = inspect.currentframe()
            if frame is not None:
                frame = frame.f_back
                if frame is not None:
                    caller_namespace = frame.f_globals["__name__"]
            metric_name = f"timer.{caller_namespace}"
            if self._name:
                metric_name = f"{metric_name}.{self._name}"
            msg = f"{metric_name} - {self._duration:5.2f}s"
            self._logger.info(msg, stacklevel=2)

    @property
    def duration(self) -> float:
        """The number of seconds from when the context block was entered until it was exited.

        Raises ValueError if the context block was either:
            - never entered
            - entered but not exited
        """
        if self._duration is None:
            raise ValueError("Cannot get duration if timer has not exited context block!")
        return self._duration

    @property
    def timedelta(self) -> timedelta:
        """Formats the duration as a datetime timedelta object.

        Raises ValueError on same conditions as `duration`.
        """
        return timedelta(seconds=self.duration)

    def __format__(self, format_spec: str) -> str:
        """String representation of the timer's duration, using the supplied formatting
        specification.
        """
        return f"{self.duration:{format_spec}}"

    #
    # It is often necessary to compute statistics on a collection of timers.
    # e.g. "What's the median time? Average time?" etc.
    #

    def __float__(self) -> float:
        """Alias to the timer's duration. See :func:`duration` for specification."""
        return self.duration

    def __int__(self) -> int:
        """Rounds the duration to the nearest second."""
        return int(round(float(self)))

    #
    # Implementations for builtins numeric operations.
    #

    def __eq__(self, other) -> bool:
        return float(self) == float(other)

    def __lt__(self, other) -> bool:
        return float(self) < float(other)

    def __le__(self, other) -> bool:
        return float(self) <= float(other)

    def __gt__(self, other) -> bool:
        return float(self) > float(other)

    def __ge__(self, other) -> bool:
        return float(self) >= float(other)

    def __abs__(self) -> float:
        return abs(float(self))

    def __add__(self, other) -> float:
        return float(self) + float(other)

    def __sub__(self, other) -> float:
        return float(self) - float(other)

    def __mul__(self, other) -> float:
        return float(self) * float(other)

    def __floordiv__(self, other) -> int:
        return int(self) // int(other)

    def __truediv__(self, other) -> float:
        return float(self) / float(other)
