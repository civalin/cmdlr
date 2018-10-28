"""Cmdlr core module."""

import asyncio
import sys
import pprint
from collections import Iterable
from itertools import groupby
from itertools import zip_longest
from itertools import chain
from urllib.parse import urlparse

from .reqpool import RequestPool
from .log import logger
from .exception import NoMatchAnalyzer


def _get_optimized_order(comics):
    """Get a list contain all comics with optimized ordering.

    Build a list contain all comics input, and interlaced them by its
    host of the entry url as much as possible.

    Assume the input has 10 comics across 3 hosts, like this:

    [hostA1, hostA2,
     hostB1, hostB2, hostB3, hostB4, hostB5,
     hostC1, hostC2, hostC3]

    Then the returned list will be re-orderd to:

    [hostA1, hostB1, hostC1,
     hostA2, hostB2, hostC2,
     hostB3, hostC3,
     hostB4,
     hostB5]

    Args:
        comics: iterable comic container

    Returns:
        a list

    """
    def get_host(comic):
        return urlparse(comic.url).netloc

    def sort_key(comic):
        return (get_host(comic), comic.meta['name'])

    def is_not_none(x):
        return x is not None

    sorted_comics = sorted(comics, key=sort_key)
    grouped_comics = [
        list(partial_comics)
        for host, partial_comics
        in groupby(sorted_comics, key=get_host)
    ]
    comics = list(filter(
        is_not_none,
        chain(*zip_longest(*grouped_comics)),
    ))

    return comics


class LoopManager:
    """Control the main loop."""

    def __init__(self, config):
        """Init core loop manager."""
        self.config = config
        self.loop = asyncio.get_event_loop()
        self.__semaphore = asyncio.Semaphore(
            value=config.max_concurrent,
            loop=self.loop,
        )

    async def __run_cogens(self, cogens, curl):
        """Run coroutine generator list and pass args, one by one."""
        async def run():
            prev_cogen_ret = []
            for cogen in cogens:
                prev_cogen_ret = await cogen(*prev_cogen_ret)

                if not isinstance(prev_cogen_ret, Iterable):
                    prev_cogen_ret = [prev_cogen_ret]

        async with self.__semaphore:
            try:
                await run()

            except NoMatchAnalyzer as e:
                logger.error(e)

            except Exception as e:
                if hasattr(e, 'ori_meta'):
                    extra_info = '>> original metadata:\n{}'.format(
                        pprint.pformat(e.ori_meta))
                else:
                    extra_info = ''

                logger.error(
                    'Unexpected Book Error: {}\n{}'.format(curl, extra_info),
                    exc_info=sys.exc_info())

    def __build_coro_from_comic(self, comic, request_pool, ctrl):
        """Get coro to process a exists comic."""
        coro_generators = []

        if ctrl.get('update_meta'):
            async def update_meta_cogen(*args):
                await comic.update_meta(request_pool)

            coro_generators.append(update_meta_cogen)

        if ctrl.get('download'):
            async def download_cogen(*args):
                await comic.download(
                    request_pool,
                    ctrl.get('skip_errors'),
                )

            coro_generators.append(download_cogen)

        return self.__run_cogens(coro_generators, comic.url)

    def __build_coro_from_url(self, cmgr, url, request_pool, ctrl):
        """Get coro to process a non-exists url."""
        async def create_meta_cogen(*args):
            comic = await cmgr.build_comic(request_pool, url)

            return comic

        coro_generators = [create_meta_cogen]

        if ctrl.get('download'):
            async def download_cogen(comic):
                await comic.download(
                    request_pool,
                    ctrl.get('skip_errors'),
                )

            coro_generators.append(download_cogen)

        return self.__run_cogens(coro_generators, url)

    async def __get_main_task(self, cmgr, urls, ctrl):
        """Get main task for loop."""
        try:
            request_pool = RequestPool(self.config, self.loop)

            url_to_comics = cmgr.get_url_to_comics(urls)
            exist_comics = _get_optimized_order(url_to_comics.values())
            exist_coros = [
                self.__build_coro_from_comic(comic, request_pool, ctrl)
                for comic in exist_comics
            ]

            non_exist_urls = cmgr.get_non_exist_urls(urls)
            non_exist_coros = [
                self.__build_coro_from_url(cmgr, url, request_pool, ctrl)
                for url in non_exist_urls
            ]

            coros = non_exist_coros + exist_coros

            if len(coros) == 0:
                return

            await asyncio.wait(
                [self.loop.create_task(coro) for coro in coros],
            )

        finally:
            await request_pool.close()

    def start(self, amgr, cmgr, urls, ctrl):
        """Start core system."""
        try:
            self.loop.run_until_complete(self.__get_main_task(
                cmgr=cmgr,
                urls=urls,
                ctrl=ctrl,
            ))

        except Exception as e:
            logger.critical('Critical Error: {}'.format(e),
                            exc_info=sys.exc_info())
            sys.exit(1)
