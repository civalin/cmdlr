"""Maintain aiohttp sessions."""

from datetime import datetime

from aiohttp import ClientSession
from aiohttp import ClientTimeout
from aiohttp import TraceConfig

from aiohttp_socks import SocksConnector


def _get_timing_trace_config(host_pool):
    """Get trace config to log and calculate request delay."""
    async def on_request_start(session, trace_config_ctx, params):
        url = str(params.url)

        host_pool.update_previous_request_start(url)

        trace_config_ctx.start = session.loop.time()

    async def on_request_end(session, trace_config_ctx, params):
        url = str(params.url)

        if params.response.status != 200:
            host_pool.increase_error_delay(url)

        else:
            elapsed = session.loop.time() - trace_config_ctx.start
            host_pool.add_an_elapsed(url, elapsed)

            host_pool.decrease_error_delay(url)

    async def on_request_exception(session, trace_config_ctx, params):
        url = str(params.url)

        host_pool.increase_error_delay(url)

    trace_config = TraceConfig()

    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)
    trace_config.on_request_exception.append(on_request_exception)

    return trace_config


class SessionPool:
    """Maintain a aiohttp client session pool."""

    def __init__(self):
        """Session pool init."""
        self.sessions = []

    def build_session(self, analyzer_system, host_pool):
        """Build a new session."""
        timing_trace_config = _get_timing_trace_config(host_pool)

        session_init_kwargs = {
            'timeout': ClientTimeout(total=analyzer_system['timeout']),
            'trace_configs': [timing_trace_config],
        }

        if analyzer_system['socks_proxy']:
            session_init_kwargs['connector'] = SocksConnector.from_url(
                analyzer_system['socks_proxy'],
                rdns=True,
            )

        session = ClientSession(
            **session_init_kwargs,
        )

        self.sessions.append(session)

        return session

    async def close(self):
        """Close all dispatched sessions."""
        for session in self.sessions:
            await session.close()

        self.sessions.clear()
