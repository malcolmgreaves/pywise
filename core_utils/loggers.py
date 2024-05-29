import inspect
import logging
import os
import sys
import warnings
from contextlib import contextmanager
from typing import Iterator, Literal, Optional, Sequence, Union, cast

__all__: Sequence[str] = (
    "LOG_FORMAT",
    "LogLevelStr",
    "LogLevelInt",
    "LogLevel",
    "logger_name",
    "make_standard_logger",
    "standardize_log_level",
    "deprecation_warning",
    "LOG_FORMAT",
    "print_logger",
    "silence_chatty_logger",
    "loggers_at_level",
    "filename_wo_ext",
)

LOG_FORMAT: str = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"

# NOTE: The following log level names map to the these log level integer values:
# NOTSET = 0
# DEBUG = 10
# INFO = 20
# WARNING = 30
# WARN = WARNING
# ERROR = 40
# CRITICAL = 50
# FATAL = CRITICAL

LogLevelStr = Literal["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"]
LogLevelInt = Literal[10, 20, 30, 40, 50]
LogLevel = Union[LogLevelStr, LogLevelInt]

# NOTE: While this is *usually* a _very bad idea_, we opt to include some runtime checking logic
#       here at module loading time. We must ensure that the logging package's values for log
#       levels match our expected values (i.e. what's in `LogLevelInt` and the assumption that
#       these correspond 1:1 with `LogLevelStr`).
#
#       It is **highly unlikely** that these will _ever_ change. If so, all Python programs using
#       them would break! Nevertheless, we do this here for the sake of correctness.
assert logging.DEBUG in LogLevelInt.__args__  # type: ignore
assert logging.INFO in LogLevelInt.__args__  # type: ignore
assert logging.WARNING in LogLevelInt.__args__  # type: ignore
assert logging.ERROR in LogLevelInt.__args__  # type: ignore
assert logging.FATAL in LogLevelInt.__args__  # type: ignore


def logger_name(*, fallback_name: Optional[str] = None) -> str:
    """Returns the __name__ from where the calling function is defined or its filename if it is "__main__".

    Normally, __name__ is the fully qualified Python name of the module. However, if execution starts at
    the module, then it's __name__ attribute is "__main__". In this scenario, we obtain the module's filename.

    The returned string is as close to a unique Python name for the caller's defining module.

    NOTE: If :param:`fallback_name` is provided and is not-None and non-empty, then, in the event that
          the logger name cannot be inferred from the calling __main__ module, this value will be used
          instead of raising a ValueError.
    """
    # Get the module where the calling function is defined.
    # https://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
    stack = inspect.stack()
    calling_frame = stack[1]
    calling_module = inspect.getmodule(calling_frame[0])
    if calling_module is None:
        raise ValueError(
            f"Cannot obtain module from calling function. Tried to use calling frame {calling_frame}"
        )
    # we try to use this module's name
    name = calling_module.__name__
    if name == "__main__":
        # unless logger_name was called from an executing script,
        # in which case we use it's file name

        if hasattr(calling_module, "__file__"):
            assert calling_module.__file__ is not None
            return filename_wo_ext(calling_module.__file__)
        if fallback_name is not None:
            fallback_name = fallback_name.strip()
            if len(fallback_name) > 0:
                return fallback_name
        raise ValueError("Cannot determine calling module's name from its __file__ attribute!")
    return name


def make_standard_logger(
    name: str,
    log_level: LogLevel = logging.INFO,  # type: ignore
) -> logging.Logger:
    """Standard protocol for creating a logger that works well with Datadog & local development.

    Interoperates with the log formatting performed by standard structured log systems
    (e.g. Datadog's `ddtrace-run` program). This logger ensures that you will always be able to
    view the logging output on stderr.
    """
    if not isinstance(name, str) or len(name) == 0:
        raise ValueError("Name must be a non-empty string.")

    logger = logging.getLogger(name)
    logger.setLevel(standardize_log_level(log_level))
    logging.basicConfig(format=LOG_FORMAT)
    return logger


def standardize_log_level(log_level: LogLevel) -> LogLevelInt:
    """Converts string (or int) for log level into its canonical int representation."""
    if isinstance(log_level, str):
        if log_level not in LogLevelStr.__args__ or log_level not in logging._nameToLevel:  # type: ignore
            raise ValueError(
                f"Unrecognized logging level (str): {log_level}, from known {LogLevelStr}"
            )
        else:
            level: LogLevelInt = cast(LogLevelInt, logging._nameToLevel[log_level])  # type: ignore
    elif isinstance(log_level, int):
        level = cast(LogLevelInt, log_level)
        if level not in LogLevelInt.__args__:  # type: ignore
            raise ValueError(
                f"Unrecognized logging level (int): {log_level}, from known {LogLevelInt}"
            )
    else:
        raise TypeError(
            f"Expecting either int or str for log level ({LogLevel}), but found {type(log_level)}"
        )
    return level


def print_logger() -> logging.Logger:
    """A logger that is equivalent to calling `print(...)`.

    Has debug-level enabled, no formatting, and is called 'print'.
    """
    logger = logging.getLogger("print")
    logger.setLevel(logging.DEBUG)
    logging.basicConfig(stream=sys.stdout, format="%(message)s")
    return logger


def deprecation_warning(
    logger: logging.Logger, msg: str, *, prepend_deprecated: bool = True
) -> None:
    """Creates a deprecation warning log event with given the message and logger.

    The logger must be enabled for WARNING level or below in order for the message to be observed.
    The :param:`prepend_deprecated` parameter will, if enabled, prepend the word 'DEPRECATED' to
    the beginning of the :param:`msg`. True by default. Set to false to log :param:`msg` without
    modifications.
    """
    if prepend_deprecated:
        msg = f"[DEPRECATED] {msg}"
    logger.warning(msg)
    warnings.simplefilter("always", DeprecationWarning)
    warnings.warn(msg, DeprecationWarning)


def silence_chatty_logger(
    *logger_names,
    quieter: LogLevelInt = logging.FATAL,  # type: ignore
) -> None:
    """Sets loggers to the `quieter` level, which defaults to the highest (FATAL).

    Accepts a variable number of logger names (str).
    """
    q = standardize_log_level(quieter)
    for log_name in logger_names:
        log = logging.getLogger(log_name)
        log.setLevel(q)


@contextmanager  # type: ignore
def loggers_at_level(*loggers_or_names, new_level: LogLevel) -> Iterator[None]:
    """Temporarily set one or more loggers to a specific level, resetting to previous levels on context end.

    The :param:`loggers_or_names` is one or more :class:`logging.Logger` instances, or `str` names
    of loggers regiested via `logging.getLogger`.

    The :param:`new_level` is the new logging level to set during the context. See
    `logging.{DEBUG,INFO,WARNING,ERROR,FATAL}` for values & documentation.

    To illustrate use, see this example:
    >>>> import logging
    >>>>
    >>>> your_logger: logging.Logger = ...
    >>>>
    >>>> with loggers_at_level(
    >>>>   your_logger,
    >>>>   'module_with_logger.loggers',
    >>>>   'library_with_loggers.utils_general',
    >>>>   new_level=logging.FATAL,
    >>>> ):
    >>>>   # do_something_while_those_loggers_will_only_log_FATAL_messages
    >>>>   your_logger.info("this will not be logged")
    >>>>   logging.getLogger('module_with_logger.loggers').warning("neither will this")
    >>>>   logging.getLogger('library_with_loggers.utils_general').warning("nor this")
    >>>>
    >>>> your_logger.info("this will be logged")
    """
    loggers: Sequence[logging.Logger] = [
        (logging.getLogger(log) if isinstance(log, str) else log) for log in loggers_or_names
    ]
    previous_levels: Sequence[LogLevelInt] = [cast(LogLevelInt, log.level) for log in loggers]
    try:
        for log in loggers:
            log.setLevel(new_level)

        yield

    finally:
        for log, level in zip(loggers, previous_levels):
            log.setLevel(level)


def filename_wo_ext(filename: str) -> str:
    """Gets the filename, without the file extension, if present."""
    return os.path.split(filename)[1].split(".", 1)[0]
