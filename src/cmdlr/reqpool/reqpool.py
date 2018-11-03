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
        self.session_pool = SessionPool()

        self.semaphore = asyncio.Semaphore(
            value=config.total_connections,
            loop=loop,
        )

        self.requests = {}

    def get_request(self, analyzer):
        """Get cmdlr request."""
        request = self.requests.get(analyzer)

        if not request:
            analyzer_system = self.config.get_analyzer_system_pref(
                analyzer.name
            )

            request = build_request(
                analyzer,
                analyzer_system,
                self.session_pool.build_session(
                    analyzer_system,
                    self.host_pool,
                ),
                self.semaphore,
                self.host_pool,
            )
            self.requests[analyzer] = request

        return request

    async def close(self):
        """Close all resource."""
        await self.session_pool.close()
