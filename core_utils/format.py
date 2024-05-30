import traceback
from logging import Logger
from typing import Any, List, Optional, Sequence, Tuple, Union

__all__: Sequence[str] = (
    "program_init_param_msg",
    "evenly_space",
    "exception_stacktrace",
    "format_stacktrace",
)


def program_init_param_msg(
    logger: Logger,
    msg: Sequence[str],
    name: Optional[str] = None,
    log_each_line: bool = False,
) -> None:
    """Pretty prints important, configurable values for command-line programs.

    Uses the :param:`logger` to output all messages in :param:`msg`.

    If :param:`log_each_line` is true, then each message is applied to `logger.info`.
    Otherwise, a newline is inserted between all messages and they are all logged once.

    If :param:`name` is supplied, then it is the first logged message. If there is no
    name and the function is logging all messages at once, then a single newline is
    inserted before the mass of messages.
    """
    separator: str = max(map(len, msg)) * "-"
    if log_each_line:
        logger.info(separator)
        if name is not None:
            logger.info(name)
        for line in msg:
            logger.info(line)
        logger.info(separator)
    else:
        if name:
            starting = f"{name}\n"
        else:
            starting = "\n"
        logger.info(starting + "\n".join([separator] + list(msg) + [separator]))


def evenly_space(name_and_value: Sequence[Tuple[str, Any]]) -> List[str]:
    """Pads the middle of (name,value) pairs such that all values vertically align.

    Adds a ':' after each name (first element of each tuple).
    """
    if len(name_and_value) == 0:
        return []
    max_name_len = max(map(lambda x: len(x[0]), name_and_value))
    values = []
    for name, value in name_and_value:
        len_spacing = max_name_len - len(name)
        spacing = " " * len_spacing
        values.append(f"{name}: {spacing}{value}")
    return values


def exception_stacktrace(e: Exception) -> List[str]:
    """Formats the given exception as a standard stack trace error message."""
    return traceback.format_exception(type(e), e, e.__traceback__)


def format_stacktrace(stacktrace_or_exception: Union[Sequence[str], Exception]) -> str:
    """Formats the exception, or its stacktrace, for easy logging or printing."""
    stacktrace: Sequence[str] = (
        exception_stacktrace(stacktrace_or_exception)
        if isinstance(stacktrace_or_exception, Exception)
        else stacktrace_or_exception
    )
    return "\n".join([s for s in stacktrace if len(s.strip()) > 0])
