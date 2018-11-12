"""Maintain host infos."""

import asyncio
from datetime import datetime
from urllib.parse import urlparse
from collections import deque
from statistics import mean
from random import gauss
from math import inf


def _clamp(value, _min=-inf, _max=inf):
    return min(max(value, _min), _max)


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

        user_delay = host['delay']
        user_random_delay = _clamp(
            gauss(
                mu=user_delay,
                sigma=user_delay * 0.33,
            ),
            _min=0,
            _max=user_delay * 2,
        )
        mean_elapsed = mean(host['recent_elapsed_seconds'])
        standard_delay = max(user_random_delay, mean_elapsed)

        should_delay = standard_delay + host['error_delay']

        already_pass = (
            datetime.utcnow()
            - host['previous_request_start']
        ).total_seconds()

        remained_delay = should_delay - already_pass

        return _clamp(remained_delay, _min=0)

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

        host['error_delay'] = _clamp(host['error_delay'] + 2, _max=600)

    def decrease_error_delay(self, url):
        """Decrease error delay."""
        host = self.__get_host(url)

        host['error_delay'] = _clamp(host['error_delay'] - 2, _min=0)

    async def wait_for_delay(self, url):
        """Wait for delay (based on host)."""
        delay_sec = self.__get_remain_delay_sec(url)

        if delay_sec > 0:
            await asyncio.sleep(delay_sec)

    def get_semaphore(self, url):
        """Return a semaphore (based on host)."""
        host = self.__get_host(url)

        return host['semaphore']
