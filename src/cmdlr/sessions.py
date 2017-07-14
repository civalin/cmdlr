"""Cmdlr clawler subsystem."""

import asyncio

import aiohttp

from . import amgr
from . import info
from . import config
from . import log


_semaphore = None
_session_pool = {}
_loop = None


def _get_session_init_kwargs(analyzer):
    analyzer_kwargs = getattr(analyzer, 'session_init_kwargs', {})
    default_kwargs = {'headers': {
                          'user-agent': '{}/{}'.format(
                              info.PROJECT_NAME, info.VERSION)
                          },
                      'read_timeout': 60,
                      'conn_timeout': 20}
    kwargs = {**default_kwargs,
              **analyzer_kwargs}

    if 'connector' not in kwargs:
        kwargs['connector'] = aiohttp.TCPConnector(limit_per_host=5)

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

    class request:
        """session.request contextmanager."""

        def __init__(self, **req_kwargs):
            """init."""
            self.req_kwargs = req_kwargs

        async def __aenter__(self):
            """async with enter."""
            for try_idx in range(max_try):
                try:
                    await _semaphore.acquire()
                    self.resp = await session.request(**{
                        **{'method': 'GET', 'proxy': proxy},
                        **self.req_kwargs,
                        })
                    self.resp.raise_for_status()
                    return self.resp
                except Exception as e:
                    _semaphore.release()
                    current_try = try_idx + 1
                    log.logger.error(
                            'Request Failed ({}/{}): {} => {}: {}'
                            .format(current_try, max_try,
                                    self.req_kwargs['url'],
                                    type(e).__name__, e))
                    if current_try == max_try:
                        raise e from None

        async def __aexit__(self, exc_type, exc, tb):
            """async with exit."""
            await self.resp.release()
            _semaphore.release()

    return request
