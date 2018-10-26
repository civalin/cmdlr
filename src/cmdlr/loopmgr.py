"""Cmdlr core module."""

import asyncio
import sys
import pprint
from collections import Iterable

from .reqpool import RequestPool
from .log import logger
from .exception import NoMatchAnalyzer


async def _get_empty_coro():
    pass


class LoopManager:
    """Control the main loop."""

    def __init__(self, max_concurrent):
        """Init core loop manager."""
        self.loop = asyncio.get_event_loop()
        self.__semaphore = asyncio.Semaphore(
            value=max_concurrent,
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
                    ctrl.get('skip_download_errors'),
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
                    ctrl.get('skip_download_errors'),
                )

            coro_generators.append(download_cogen)

        return self.__run_cogens(coro_generators, url)

    def __get_main_task(self, cmgr, urls, request_pool, ctrl):
        """Get main task for loop."""
        url_to_comics = cmgr.get_url_to_comics(urls)
        exist_coros = [
            self.__build_coro_from_comic(comic, request_pool, ctrl)
            for comic in url_to_comics.values()
        ]

        non_exist_urls = cmgr.get_non_exist_urls(urls)
        non_exist_coros = [
            self.__build_coro_from_url(cmgr, url, request_pool, ctrl)
            for url in non_exist_urls
        ]

        coros = non_exist_coros + exist_coros

        if len(coros) == 0:
            return _get_empty_coro()

        return asyncio.wait([self.loop.create_task(coro) for coro in coros])

    def start(self, config, amgr, cmgr, urls, ctrl):
        """Start core system."""
        request_pool = RequestPool(config, self.loop)

        try:
            self.loop.run_until_complete(self.__get_main_task(
                cmgr=cmgr,
                urls=urls,
                request_pool=request_pool,
                ctrl=ctrl,
            ))

        except Exception as e:
            logger.critical('Critical Error: {}'.format(e),
                            exc_info=sys.exc_info())
            sys.exit(1)

        finally:
            request_pool.close()
