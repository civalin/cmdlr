"""Cmdlr request pool."""

import asyncio

from .hostpool import HostPool
from .sesspool import SessionPool
from .req import build_request


class RequestPool:
    """Manager cmdlr's Request object."""

    def __init__(self, config, loop):
        """Init request pool."""
        self.config = config
        self.loop = loop

        self.host_pool = HostPool(loop)
        self.session_pool = SessionPool(loop)

        self.semaphore = asyncio.Semaphore(
            value=config.total_connection,
            loop=loop,
        )

        self.requests = {}

    def get_request(self, analyzer):
        """Get cmdlr request."""
        request = self.requests.get(analyzer)

        if not request:
            request = build_request(
                self.config.get_analyzer_system_pref(analyzer.name),
                self.session_pool.build_session(analyzer.session_init_kwargs),
                self.semaphore,
                self.host_pool,
            )
            self.requests[analyzer] = request

        return request

    async def close(self):
        """Close all resource."""
        await self.session_pool.close()
