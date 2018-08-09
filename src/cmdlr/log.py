"""Setting the logger."""

import logging


def _get_stream_handler():
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    return ch


def _init():
    """Init the logger."""
    logger = logging.getLogger('cmdlr')
    logger.setLevel(level=logging.INFO)
    logger.addHandler(_get_stream_handler())


_init()


logger = logging.getLogger('cmdlr')
