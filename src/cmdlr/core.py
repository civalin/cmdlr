"""Cmdlr core module."""

import asyncio
import sys
import pprint

from . import sessions
from . import config
from . import cmgr
from . import log
from . import exceptions


_semaphore = None


def _init():
    loop = asyncio.get_event_loop()
    global _semaphore
    _semaphore = asyncio.Semaphore(
            value=config.get_max_concurrent(), loop=loop)

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


def _one_comic_coro(loop, c,
                    update_meta, download,
                    volume_names, force_download, skip_download_errors):
    """Get one combined task."""
    c_coros = []

    if not c.ready or update_meta:
        c_coros.append(c.get_info(loop))

    if download:
        c_coros.append(c.download(
            loop, volume_names, force_download, skip_download_errors))

    if len(c_coros) == 0:
        return _get_empty_coro()

    curl = c.meta['url']
    return _run_comic_coros_by_order(curl, c_coros)


def _get_main_task(loop, coll_dirpaths, urls, **oct_kwargs):
    """Get main task for loop."""
    urlcomics = cmgr.get_selected_url_comics(coll_dirpaths, urls)

    coros = [_one_comic_coro(loop, c, **oct_kwargs)
             for c in urlcomics.values()]
    filtered_coros = [coro for coro in coros if coro is not None]

    if len(filtered_coros) == 0:
        return _get_empty_coro()

    return asyncio.wait(filtered_coros)


def start(**gmt_kwargs):
    """Start core system."""
    loop = _init()
    sessions.init(loop)

    try:
        loop.run_until_complete(_get_main_task(loop=loop, **gmt_kwargs))
    except Exception as e:
        log.logger.critical('Critical Error: {}'.format(e),
                            exc_info=sys.exc_info())
        sys.exit(1)
    finally:
        sessions.close()
