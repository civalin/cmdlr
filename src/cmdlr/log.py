"""Setting the logger."""

import logging


def _get_stream_handler():
    ch = logging.StreamHandler()

    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    ch.setFormatter(formatter)

    ch.setLevel(logging.DEBUG)

    return ch


def _init():
    """Init the logger."""
    logger = logging.getLogger('cmdlr')
    logger.setLevel(level=logging.INFO)
    logger.addHandler(_get_stream_handler())


_init()


logger = logging.getLogger('cmdlr')
