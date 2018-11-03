"""Maintain host infos."""

import asyncio
import random
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlparse
from collections import deque


class HostPool:
    """Maintain host infos."""

    def __init__(self, loop):
        """Init host infos."""
        self.loop = loop

        self.hosts = {}

    def __get_host(self, url):
        netloc = urlparse(url).netloc

        return self.hosts[netloc]

    def register_host(self, url, per_host_connection, delay):
        """Initialize a host and config it."""
        netloc = urlparse(url).netloc

        if netloc not in self.hosts:
            self.hosts[netloc] = {
                'semaphore': asyncio.Semaphore(
                    value=per_host_connection,
                    loop=self.loop),

                'delay': delay,

                'previous_request_start': datetime.utcnow(),
                'recent_elapsed_seconds': deque([0.0], maxlen=10),
                'error_delay': 0,
            }

    def __get_remain_delay_sec(self, url):
        host = self.__get_host(url)

        delay = host['delay']
        static_delay_sec = random.random() * delay * 2

        recent_elapsed_sec = host['recent_elapsed_seconds']
        avg_elapsed_sec = sum(recent_elapsed_sec) / len(recent_elapsed_sec)

        should_delay_sec = (
            static_delay_sec
            + avg_elapsed_sec
            + host['error_delay']
        )
        should_delay = timedelta(seconds=should_delay_sec)

        previous_request_start = host['previous_request_start']
        now = datetime.utcnow()
        already_pass = now - previous_request_start
        remained = should_delay - already_pass

        return max(remained.total_seconds(), 0)

    def add_an_elapsed(self, url, elapsed):
        """Add a new elapsed seconds for further calculations."""
        host = self.__get_host(url)

        host['recent_elapsed_seconds'].append(elapsed)

    def update_previous_request_start(self, url):
        """Update a new start time."""
        host = self.__get_host(url)

        host['previous_request_start'] = datetime.utcnow()

    def increase_error_delay(self, url):
        """Increase error delay."""
        host = self.__get_host(url)

        host['error_delay'] = min(host['error_delay'] + 2, 600)

    def decrease_error_delay(self, url):
        """Decrease error delay."""
        host = self.__get_host(url)

        host['error_delay'] = max(host['error_delay'] - 2, 0)

    async def wait_for_delay(self, url):
        """Wait for delay (based on host)."""
        delay_sec = self.__get_remain_delay_sec(url)

        if delay_sec > 0:
            await asyncio.sleep(delay_sec)

    async def acquire(self, url):
        """Acquire semaphore for the url (based on host)."""
        host = self.__get_host(url)
        await host['semaphore'].acquire()

    def release(self, url):
        """Release semaphore for the url (based on host)."""
        host = self.__get_host(url)
        host['semaphore'].release()
