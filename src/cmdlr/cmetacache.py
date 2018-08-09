"""Cmdlr meta file caching module.

This module try to cache a lot of metadata to a big file. Should improve
performance significantly due to avoid to load a lot of small files and
parsed the original format.
"""


import os
import pickle
import tempfile
import atexit

_protocol = 4
_cache_filepath = os.path.join(
        tempfile.gettempdir(), 'cmdlr-meta-cache.pickle')

_already_init = False
_cache = {}


def _init():
    global _already_init
    global _cache

    if _already_init:
        return

    if os.path.isfile(_cache_filepath):
        with open(_cache_filepath, 'rb') as f:
            _cache = pickle.load(f)

        _changed = False

    else:
        _changed = True

    def _save_back():
        if _changed is True:
            with open(_cache_filepath, mode='wb') as f:
                pickle.dump(_cache, f, protocol=_protocol)

    atexit.register(_save_back)
    _already_init = True


def load(metapath, mtime):
    """Load meta from cache."""
    _init()
    apath = os.path.abspath(metapath)

    if apath in _cache and mtime == _cache[apath]['mtime']:
        return _cache[apath]['meta']

    return None


def save(metapath, mtime, meta):
    """Save meta to cache."""
    _init()
    apath = os.path.abspath(metapath)

    global _changed
    _changed = True

    _cache[apath] = {
        'mtime': mtime,
        'meta': meta,
    }
