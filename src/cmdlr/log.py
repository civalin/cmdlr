"""Setting the logger."""

import os

from logging import getLogger
from logging import Formatter
from logging import StreamHandler
from logging import FileHandler
from logging import DEBUG

from datetime import datetime


def _get_formatter():
    return Formatter(
        fmt='%(asctime)s %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def _get_stream_handler(formatter):
    ch = StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(DEBUG)

    return ch


def _get_file_handler(logging_dir, formatter):
    if not logging_dir:
        return

    os.makedirs(logging_dir, exist_ok=True)

    filename = 'cmdlr-{}.log'.format(datetime.now().isoformat())
    filepath = os.path.join(logging_dir, filename)

    ch = FileHandler(filepath, encoding='utf8', delay=True)
    ch.setFormatter(formatter)
    ch.setLevel(DEBUG)

    return ch


def _init_logger(logging_level):
    logger = getLogger('cmdlr')
    logger.setLevel(level=logging_level)

    return logger


def init_logging(logging_dir, logging_level):
    """Init logging system."""
    formatter = _get_formatter()

    stream_handler = _get_stream_handler(formatter)
    file_handler = _get_file_handler(logging_dir, formatter)

    logger = _init_logger(logging_level)

    logger.addHandler(stream_handler)

    if file_handler:
        logger.addHandler(file_handler)


logger = getLogger('cmdlr')
