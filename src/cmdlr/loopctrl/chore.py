"""The choreographer for awaiting books."""

import asyncio
from math import ceil

from itertools import chain


class Choreographer:
    """Choreograph for awaiting books."""

    def __init__(self, config, loop, aname_to_runners):
        """Prepare this choreographer."""
        self.loop = loop

        self.total_channel = config.book_concurrent

        self.pending_aname_to_runners = aname_to_runners
        self.running_aname_to_tasks = {}

    def __get_analyzer_count(self):
        return len(self.pending_aname_to_runners)

    def __get_analyzer_channel_count(self):
        return ceil(self.total_channel / self.__get_analyzer_count())

    def __get_analyzer_channel_idle_count(self, aname):
        analyzer_channel_count = self.__get_analyzer_channel_count()
        analyzer_running_tasks = self.running_aname_to_tasks.get(aname, [])

        return analyzer_channel_count - len(analyzer_running_tasks)

    def __clearup_running_tasks(self):
        for aname, tasks in self.running_aname_to_tasks.items():
            new_tasks = [
                task for task in tasks
                if not task.done()]

            if tasks:
                self.running_aname_to_tasks[aname] = new_tasks

    def __runup_new_tasks(self):
        for aname, runners in self.pending_aname_to_runners.items():
            idle_count = self.__get_analyzer_channel_idle_count(aname)

            if idle_count >= 1:
                for _ in range(idle_count):
                    if runners:
                        runner = runners.pop()
                        task = self.loop.create_task(runner)

                        if aname not in self.running_aname_to_tasks:
                            self.running_aname_to_tasks[aname] = []

                        self.running_aname_to_tasks[aname].append(task)

    def __concat_running_tasks(self):
        return list(chain.from_iterable(
            tasks for tasks in self.running_aname_to_tasks.values()
        ))

    async def run(self):
        """Run this choreographer."""
        while True:
            self.__clearup_running_tasks()
            self.__runup_new_tasks()

            running_tasks = self.__concat_running_tasks()

            if running_tasks:
                await asyncio.wait(running_tasks,
                                   return_when=asyncio.FIRST_COMPLETED,
                                   loop=self.loop)

            else:
                return
