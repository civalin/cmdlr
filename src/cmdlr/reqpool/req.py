"""Define request cmdlr used."""

import sys
import asyncio

import aiohttp

from ..log import logger


def build_request(config, session, semaphore, host_pool):
    """Get the request class."""
    max_try = config.max_retry + 1

    class request:
        """session.request contextmanager."""

        def __init__(self, **req_kwargs):
            """init."""
            self.req_kwargs = req_kwargs
            self.url = req_kwargs['url']

            self.resp = None
            self.host_semaphore_acquired = False
            self.global_semaphore_acquired = False

        async def __acquire(self):
            self.host_semaphore_acquired = True
            await host_pool.acquire(self.url)

            self.global_semaphore_acquired = True
            await semaphore.acquire()

        def __release(self):
            if self.global_semaphore_acquired:
                self.global_semaphore_acquired = False
                semaphore.release()

            if self.host_semaphore_acquired:
                self.host_semaphore_acquired = False
                host_pool.release(self.url)

        async def __get_response(self):
            await self.__acquire()

            delay_sec = host_pool.get_delay_sec(self.url)
            await asyncio.sleep(delay_sec)

            real_req_kwargs = {
                **{'method': 'GET', 'proxy': config.proxy},
                **self.req_kwargs,
            }

            self.resp = await session.request(**real_req_kwargs)
            self.resp.raise_for_status()

            return self.resp

        async def __aenter__(self):
            """Async with enter."""
            for try_idx in range(max_try):
                try:
                    return await self.__get_response()

                except aiohttp.ClientError as e:
                    current_try = try_idx + 1

                    logger.error(
                        'Request Failed ({}/{}): {} => {}: {}'
                        .format(
                            current_try, max_try,
                            self.url,
                            type(e).__name__, e,
                        )
                    )

                    await self.__aexit__(*sys.exc_info())

                    if current_try == max_try:
                        raise e from None

        async def __aexit__(self, exc_type, exc, tb):
            """Async with exit."""
            if exc_type:
                if exc_type is not asyncio.CancelledError:
                    host_pool.increase_delay(self.url)

            else:
                host_pool.decrease_delay(self.url)

            if self.resp:
                await self.resp.release()

            self.__release()

    return request
