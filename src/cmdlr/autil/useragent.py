"""Build fake useragent."""

import os
from functools import lru_cache

from fake_useragent import UserAgent


@lru_cache()
def _fake_useragent():
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, 'useragent.json')

    return UserAgent(path=path)


def get_random_useragent():
    """Get the random useragent string.

    The FakeUserAgent instance need extra network connection to fetch the
    recently user-agent usage statistic when __init__() by default.

    This behavior may cause two problems:
        1. If user-agent was fully unpredictable, some analyzer's behavior
           may also unpredictable and untestable.
        2. This request are not socksifible, this a potential security
           issue.

    This function basically try to used local database to avoid those problem.
    """
    return _fake_useragent().random
