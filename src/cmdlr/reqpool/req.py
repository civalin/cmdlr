"""Define request cmdlr used."""

import asyncio
from functools import reduce

import aiohttp
from aiohttp_socks.errors import SocksError

from ..log import logger
from ..merge import merge_dict


def build_request(
        analyzer, analyzer_system, session, global_semaphore, host_pool):
    """Get the request class."""
    max_try = analyzer_system['max_try']
    per_host_connections = analyzer_system['per_host_connections']
    delay = analyzer_system['delay']

    class request:
        """session.request contextmanager."""

        def __init__(self, url, **req_kwargs):
            """init."""
            self.req_kwargs = req_kwargs
            self.url = url

            self.resp = None

            host_pool.register_host(url, per_host_connections, delay)

        async def __run_in_semaphore(self, async_func):
            async with host_pool.get_semaphore(self.url):
                async with global_semaphore:
                    return await async_func()

        async def __get_response(self):
            await host_pool.wait_for_delay(self.url)

            real_req_kwargs = reduce(
                merge_dict,
                [
                    analyzer.default_request_kwargs,
                    self.req_kwargs,
                    {'url': self.url},
                ]
            )

            self.resp = await session.request(**real_req_kwargs)
            self.resp.raise_for_status()

            await self.resp.read()  # preload for catch exception & retry

            return self.resp

        async def __aenter__(self):
            """Async with enter."""
            for try_idx in range(max_try):
                try:
                    return await self.__run_in_semaphore(self.__get_response)

                except (asyncio.TimeoutError,
                        aiohttp.ClientError,
                        SocksError) as e:
                    current_try = try_idx + 1

                    logger.error(
                        'Request Failed ({}/{}): {} => {}: {}'
                        .format(
                            current_try, max_try,
                            self.url,
                            type(e).__name__, e,
                        )
                    )

                    if current_try == max_try:
                        raise e from None

        async def __aexit__(self, exc_type, exc, tb):
            """Async with exit."""
            if self.resp:
                await self.resp.release()

    return request
