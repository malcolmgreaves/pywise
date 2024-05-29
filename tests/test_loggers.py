import logging

import pytest

from core_utils.loggers import (
    deprecation_warning,
    filename_wo_ext,
    logger_name,
    loggers_at_level,
    make_standard_logger,
    print_logger,
    silence_chatty_logger,
    standardize_log_level,
)
from core_utils.support_for_testing import MockLogger


def test_logger_name():
    name = logger_name(fallback_name="test_logger_name")
    assert len(name) > 0

    name = logger_name(fallback_name="test_logger_name")
    # only equal to fallback_name when the module is __main__
    assert name != "test_logger_name"


def test_make_standard_logger():
    logger = make_standard_logger("test_make_standard_logger")
    logger.info("hello world!")
    assert True

    with pytest.raises(ValueError):
        make_standard_logger("")


@pytest.mark.parametrize(
    "input_,expected",
    [
        ("debug", logging.DEBUG),
        ("info", logging.INFO),
        ("WARNING", logging.WARNING),
        ("error", logging.ERROR),
        ("FATAL", logging.FATAL),
        (logging.DEBUG, logging.DEBUG),
        (logging.DEBUG, logging.DEBUG),
        (logging.INFO, logging.INFO),
        (logging.WARNING, logging.WARNING),
        (logging.ERROR, logging.ERROR),
        (logging.FATAL, logging.FATAL),
    ],
)
def test_standardize_log_level(input_, expected):
    actual = standardize_log_level(input_)
    assert actual == expected

    with pytest.raises(ValueError):
        standardize_log_level(-10)  # type: ignore


def test_standardize_log_level_fail():
    with pytest.raises(ValueError):
        standardize_log_level("infos")

    with pytest.raises(ValueError):
        standardize_log_level(-10)

    with pytest.raises(TypeError):
        standardize_log_level(None)  # type: ignore


def test_print_logger():
    print_logger().info("hello world")
    assert True


@pytest.mark.parametrize("prepend_deprecated", [True, False])
def test_deprecation_warning(prepend_deprecated):
    deprecation_warning(
        print_logger(),
        "This is what a deprecated warning will look like!",
        prepend_deprecated=prepend_deprecated,
    )


def test_silence_chatty_logger():
    _ = make_standard_logger("test_make_standard_logger", log_level=logging.DEBUG)  # type: ignore
    silence_chatty_logger("test_make_standard_logger", quieter=logging.FATAL)  # type: ignore
    assert True


def test_loggers_at_level():
    message = "this is printed twice!"
    logger = MockLogger()
    logger.info(message)
    with loggers_at_level(logger, new_level=logging.FATAL):  # type: ignore
        logger.debug(message)
        logger.info(message)
        logger.warning(message)
        logger.error(message)
        logger.fatal(message)
    assert len(logger.internal) == 2
    assert logger.internal[0] == message
    assert logger.internal[1] == message
    # OLD: uncomment this line to see output!
    # requires logger = print_logger()
    # raise ValueError()
    """
        def test_loggers_at_level():
            message = "this is printed twice!"
            logger = print_logger()
            logger.info(message)
            with loggers_at_level(logger, new_level=logging.FATAL):
                logger.debug(message)
                logger.info(message)
                logger.warning(message)
                logger.error(message)
                logger.fatal(message)
    >       raise ValueError()
    E       ValueError

    tests/test_loggers.py:75: ValueError
    ------------------------------------------------------------------------------------------------- Captured log call --------------------------------------------------------------------------------------------------
    INFO     print:test_loggers.py:96 this is printed twice!
    INFO     print:test_loggers.py:100 this is printed twice!
    """


def test_filename_wo_ext():
    fi = filename_wo_ext(__file__)
    assert fi == "test_loggers"
