"""Maintain host infos."""

import asyncio
import collections
import random
import datetime as DT
import urllib.parse as UP


class HostPool:
    """Maintain host infos."""

    dyn_delay_table = {  # dyn_delay_factor -> second
        0: 0,
        1: 5,
        2: 10,
        3: 20,
        4: 30,
        5: 40,
        6: 50,
        7: 60,
        8: 90,
        9: 120,
        10: 180,
        11: 240,
        12: 300,
        13: 600,
        14: 900,
        15: 1200,
        16: 1500,
        17: 1800,
        18: 2100,
        19: 2400,
        20: 3600,
    }

    dyn_delay_inc_sensitivity = DT.timedelta(seconds=10)

    def __init__(self, config, loop):
        """Init host infos."""
        self.config = config
        self.loop = loop

        self.hosts = collections.defaultdict(self.__default_host_info)

    def __default_host_info(self):
        return {
            'dyn_delay_factor': 0,
            'dyn_delay_changed': DT.datetime.utcnow(),
            'semaphore': asyncio.Semaphore(
                value=self.config.per_host_concurrent,
                loop=self.loop),
        }

    def __get_host(self, url):
        netloc = UP.urlparse(url).netloc

        return self.hosts[netloc]

    def __get_dyn_delay_factor(self, url):
        host = self.__get_host(url)

        return host.get('dyn_delay_factor')

    def __increase_dyn_delay_factor(self, url):
        host = self.__get_host(url)

        now = DT.datetime.utcnow()
        active_time = (host['dyn_delay_changed']
                       + self.dyn_delay_inc_sensitivity)

        if now > active_time:
            host['dyn_delay_factor'] = min(20, host['dyn_delay_factor'] + 1)
            host['dyn_delay_changed'] = DT.datetime.utcnow()

    def __decrease_dyn_delay_factor(self, url):
        host = self.__get_host(url)

        host['dyn_delay_factor'] = max(0, host['dyn_delay_factor'] - 1)
        host['dyn_delay_changed'] = DT.datetime.utcnow()

    def get_delay_sec(self, url):
        """Get delay seconds for the url (based on host)."""
        dyn_delay_factor = self.__get_dyn_delay_factor(url)

        dyn_delay_sec = self.dyn_delay_table[dyn_delay_factor]
        static_delay_sec = random.random() * self.config.delay * 2

        return dyn_delay_sec + static_delay_sec

    def increase_delay(self, url):
        """Increase delay seconds for the url (based on host)."""
        self.__increase_dyn_delay_factor(url)

    def decrease_delay(self, url):
        """Decrease delay seconds for the url (based on host)."""
        self.__decrease_dyn_delay_factor(url)

    async def acquire(self, url):
        """Acquire semaphore for the url (based on host)."""
        host = self.__get_host(url)
        await host['semaphore'].acquire()

    def release(self, url):
        """Release semaphore for the url (based on host)."""
        host = self.__get_host(url)
        host['semaphore'].release()
