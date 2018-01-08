"""Cmdlr clawler subsystem."""

import asyncio
import random
import collections
import urllib.parse as UP

import aiohttp

from . import amgr
from . import info
from . import config
from . import log


def _get_default_host():
    return {'dyn_delay_factor': 0}


_semaphore = None
_session_pool = {}
_host_pool = collections.defaultdict(_get_default_host)
_loop = None


def _get_session_init_kwargs(analyzer):
    analyzer_kwargs = getattr(analyzer, 'session_init_kwargs', {})
    default_kwargs = {'headers': {
                          'user-agent': '{}/{}'.format(
                              info.PROJECT_NAME, info.VERSION)
                          },
                      'read_timeout': 60 * 5,
                      'conn_timeout': 120}
    kwargs = {**default_kwargs,
              **analyzer_kwargs}

    if 'connector' not in kwargs:
        kwargs['connector'] = aiohttp.TCPConnector(limit_per_host=2)

    return kwargs


def _clear_session_pool():
    """Close and clear all sessions in pool."""
    for session in _session_pool.values():
        session.close()

    _session_pool.clear()


def _get_session(curl):
    """Get session from session pool by comic url."""
    analyzer = amgr.get_match_analyzer(curl)
    aname = amgr.get_analyzer_name(analyzer)
    if aname not in _session_pool:
        session_init_kwargs = _get_session_init_kwargs(analyzer)
        _session_pool[aname] = aiohttp.ClientSession(loop=_loop,
                                                     **session_init_kwargs)

    return _session_pool[aname]


def _get_host(url):
    netloc = UP.urlparse(url).netloc
    return _host_pool[netloc]


def _get_delay_sec(dyn_delay_factor, delay):
    if dyn_delay_factor == 0:
        dyn_delay_sec = 0
    else:
        dyn_delay_sec = min(3600, 5 ** dyn_delay_factor)

    static_delay_sec = random.random() * delay

    return dyn_delay_sec + static_delay_sec


def _enlarge_dyn_delay_factor(old_dyn_delay_factor):
    return min(6, old_dyn_delay_factor + 1)


def _decrease_dyn_delay_factor(old_dyn_delay_factor):
    return max(0, old_dyn_delay_factor - 1)


def init(loop):
    """Init the crawler module."""
    global _loop
    _loop = loop

    global _semaphore
    _semaphore = asyncio.Semaphore(value=config.get_max_concurrent(),
                                   loop=loop)


def close():
    """Do recycle."""
    _clear_session_pool()


def get_request(curl):
    """Get the request class."""
    session = _get_session(curl)
    proxy = config.get_proxy()
    max_try = config.get_max_retry() + 1
    delay = config.get_delay()

    class request:
        """session.request contextmanager."""

        def __init__(self, **req_kwargs):
            """init."""
            self.req_kwargs = req_kwargs
            self.host = _get_host(req_kwargs['url'])

        async def __aenter__(self):
            """Async with enter."""
            for try_idx in range(max_try):
                try:
                    await _semaphore.acquire()
                    dyn_delay_factor = self.host['dyn_delay_factor']
                    delay_sec = _get_delay_sec(dyn_delay_factor, delay)
                    await asyncio.sleep(delay_sec)
                    self.resp = await session.request(**{
                        **{'method': 'GET', 'proxy': proxy},
                        **self.req_kwargs,
                        })
                    self.resp.raise_for_status()
                    self.host['dyn_delay_factor'] = _decrease_dyn_delay_factor(
                            dyn_delay_factor)
                    return self.resp
                except Exception as e:
                    current_try = try_idx + 1
                    log.logger.error(
                            'Request Failed ({}/{}): {} => {}: {}'
                            .format(current_try, max_try,
                                    self.req_kwargs['url'],
                                    type(e).__name__, e))
                    self.host['dyn_delay_factor'] = _enlarge_dyn_delay_factor(
                            dyn_delay_factor)
                    if current_try == max_try:
                        raise e from None
                    else:
                        _semaphore.release()

        async def __aexit__(self, exc_type, exc, tb):
            """Async with exit."""
            await self.resp.release()
            _semaphore.release()

    return request
