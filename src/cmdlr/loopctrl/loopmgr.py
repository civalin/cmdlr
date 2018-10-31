"""Cmdlr core module."""

import asyncio

from ..reqpool import RequestPool

from .chore import Choreographer
from .blueprint import get_aname_to_runners


class LoopManager:
    """Control the main loop."""

    def __init__(self, config, amgr, cmgr):
        """Init core loop manager."""
        self.config = config
        self.amgr = amgr
        self.cmgr = cmgr
        self.loop = asyncio.get_event_loop()

    async def __get_main_task(self, urls, ctrl):
        """Get main task for loop."""
        request_pool = RequestPool(self.config, self.loop)

        try:
            aname_to_runners = get_aname_to_runners(
                self.cmgr,
                self.amgr,
                request_pool,
                urls,
                ctrl,
            )
            choreographer = Choreographer(
                self.config,
                self.loop,
                aname_to_runners,
            )

            await choreographer.run()

        finally:
            await request_pool.close()

    def start(self, urls, ctrl):
        """Start main task."""
        main_task = self.__get_main_task(
            urls=urls,
            ctrl=ctrl,
        )

        self.loop.run_until_complete(main_task)
