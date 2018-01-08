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


_semaphore_factory = None


def _get_default_host():
    return {'dyn_delay_factor': 0,
            'semaphore': _semaphore_factory()}


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


def _get_dyn_delay_callbacks(host):
    dyn_delay_factor = host['dyn_delay_factor']

    def success():
        if dyn_delay_factor == host['dyn_delay_factor']:
            host['dyn_delay_factor'] = max(0, dyn_delay_factor - 1)

    def fail():
        if dyn_delay_factor == host['dyn_delay_factor']:
            host['dyn_delay_factor'] = min(6, dyn_delay_factor + 1)

    return success, fail


def init(loop):
    """Init the crawler module."""
    def semaphore_factory():
        return asyncio.Semaphore(value=config.get_per_host_concurrent(),
                                 loop=loop)
    global _loop
    _loop = loop

    global _semaphore_factory
    _semaphore_factory = semaphore_factory


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
            await self.host['semaphore'].acquire()

            for try_idx in range(max_try):
                dd_success, dd_fail = _get_dyn_delay_callbacks(self.host)
                dyn_delay_factor = self.host['dyn_delay_factor']
                delay_sec = _get_delay_sec(dyn_delay_factor, delay)
                await asyncio.sleep(delay_sec)

                try:
                    self.resp = await session.request(**{
                        **{'method': 'GET', 'proxy': proxy},
                        **self.req_kwargs,
                        })
                    self.resp.raise_for_status()
                    dd_success()
                    return self.resp
                except Exception as e:
                    current_try = try_idx + 1
                    log.logger.error(
                            'Request Failed ({}/{}): {} => {}: {}'
                            .format(current_try, max_try,
                                    self.req_kwargs['url'],
                                    type(e).__name__, e))
                    dd_fail()
                    if current_try == max_try:
                        raise e from None

        async def __aexit__(self, exc_type, exc, tb):
            """Async with exit."""
            await self.resp.release()
            self.host['semaphore'].release()

    return request
