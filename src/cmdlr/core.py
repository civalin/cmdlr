"""Cmdlr core module."""

import asyncio
import sys
import pprint

from . import sessions
from . import log
from . import exceptions


_semaphore = None


def _init(max_concurrent):
    loop = asyncio.get_event_loop()

    global _semaphore
    _semaphore = asyncio.Semaphore(value=max_concurrent, loop=loop)

    return loop


async def _get_empty_coro():
    pass


async def _run_comic_coros_by_order(curl, coros):
    """Run tasks in list, one by one."""
    async with _semaphore:
        try:
            for coro in coros:
                await coro

        except exceptions.NoMatchAnalyzer as e:
            log.logger.error(e)

        except Exception as e:
            extra_info = ''
            if hasattr(e, 'ori_meta'):
                extra_info = '>> original metadata:\n{}'.format(
                    pprint.pformat(e.ori_meta))

            log.logger.error(
                'Unexpected Book Error: {}\n{}'.format(curl, extra_info),
                exc_info=sys.exc_info())

        finally:
            for coro in coros:
                coro.close()


def _one_comic_coro(loop, comic, ctrl):
    """Get one combined task."""
    comic_coros = []

    if ctrl.get('update_meta'):
        comic_coros.append(comic.update_meta(loop))

    if ctrl.get('download'):
        comic_coros.append(comic.download(
            loop,
            ctrl.get('skip_download_errors'),
        ))

    if len(comic_coros) == 0:
        return _get_empty_coro()

    return _run_comic_coros_by_order(comic.url, comic_coros)


def _get_main_task(loop, cmgr, urls, ctrl):
    """Get main task for loop."""
    url_to_comics = cmgr.get_url_to_comics(urls)
    exist_comic_coros = [
        _one_comic_coro(loop, comic, ctrl)
        for comic in url_to_comics.values()
    ]

    non_exist_urls = cmgr.get_non_exist_urls(urls)
    non_exist_url_coros = [
        _run_comic_coros_by_order(url, [cmgr.build_comic(loop, url, ctrl)])
        for url in non_exist_urls
    ]

    coros = non_exist_url_coros + exist_comic_coros

    if len(coros) == 0:
        return _get_empty_coro()

    return asyncio.wait(coros)


def start(config, amgr, cmgr, urls, ctrl):
    """Start core system."""
    loop = _init(config.max_concurrent)
    sessions.init(loop, config=config, amgr=amgr)

    try:
        loop.run_until_complete(_get_main_task(
            loop=loop,
            cmgr=cmgr,
            urls=urls,
            ctrl=ctrl,
        ))

    except Exception as e:
        log.logger.critical('Critical Error: {}'.format(e),
                            exc_info=sys.exc_info())
        sys.exit(1)

    finally:
        sessions.close()
