"""The book's steps runner."""

import sys
import subprocess
from collections import Iterable
import pprint

from ..log import logger


async def _run(steps, init_step_args):
    previous_step_returns = init_step_args

    for step in steps:
        previous_step_returns = await step(*previous_step_returns)

        if not isinstance(previous_step_returns, Iterable):
            previous_step_returns = [previous_step_returns]


async def book_runner(steps, init_step_args, comic_url):
    """Run the steps one by one and pass args from previous returns."""
    try:
        await _run(steps, init_step_args)

    except subprocess.CalledProcessError as e:
        logger.error(
            'Book Error: {}\n{}'.format(
                comic_url,
                e.stderr.decode(),
            ),
            exc_info=sys.exc_info())

    except Exception as e:
        if hasattr(e, 'ori_meta'):
            extra_info = '>> original metadata:\n{}'.format(
                pprint.pformat(e.ori_meta))
        else:
            extra_info = ''

        logger.error(
            'Unexpected Book Error: {}\n{}'.format(comic_url, extra_info),
            exc_info=sys.exc_info())
