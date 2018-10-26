"""Comic meta processing module.

Following show what the comic meta file data structure look like.

    {

        'url': (str) comic url which this comic come from.
        'name': (str) comic title.
        'description': (str) comic description, pure text.
        'authors': (list of str) authors name list.
        'finished': (bool) is finished or not.

        'volumes_checked_time': (datetime) volumes set checked time.
        'volumes_modified_time': (datetime) volumes set modified time.

        'volumes': (dict)
            key (str): a unique, sortable, and human readable volume name.
            value (str): a unique volume url.
    }
"""

import os
import datetime as DT
import pickle
import tempfile
import atexit

from .. import schema
from .. import yamla


_CACHE_USE = True


class MetaToolkit:
    """Process anything relate comic meta."""

    cache_filename = 'cmdlr-meta-cache.pickle'
    pickle_protocol = 4

    def __init_cache(self):
        if os.path.isfile(self.cache_filepath):
            with open(self.cache_filepath, 'rb') as f:
                self.cache = pickle.load(f)

            self.cache_changed = False

        else:
            self.cache_changed = True

        def save_back_hook():
            if self.cache_changed is True:
                with open(self.cache_filepath, mode='wb') as f:
                    pickle.dump(self.cache, f, protocol=self.pickle_protocol)

        atexit.register(save_back_hook)

    def __meta_from_cache(self, meta_filepath, mtime):
        abspath = os.path.abspath(meta_filepath)

        if abspath in self.cache and mtime == self.cache[abspath]['mtime']:
            return self.cache[abspath]['meta']

        return None

    def __meta_to_cache(self, meta_filepath, mtime, meta):
        abspath = os.path.abspath(meta_filepath)

        self.cache[abspath] = {
            'mtime': mtime,
            'meta': meta,
        }
        self.cache_changed = True

    def __init__(self, config):
        """Init whole meta system, include cache."""
        self.cache_changed = False
        self.cache_filepath = os.path.join(
            tempfile.gettempdir(),
            self.cache_filename,
        )
        self.cache = None

        if _CACHE_USE:
            self.__init_cache()

    def load(self, meta_filepath):
        """Get meta from filepath."""
        if _CACHE_USE:
            meta_mtime = os.path.getmtime(meta_filepath)
            meta_from_cache = self.__meta_from_cache(
                meta_filepath, meta_mtime)

            if meta_from_cache:
                meta = meta_from_cache

            else:
                meta = yamla.from_file(meta_filepath)
                self.__meta_to_cache(meta_filepath, meta_mtime, meta)

        else:
            meta = yamla.from_file(meta_filepath)

        return meta

    def save(self, meta_filepath, meta):
        """Save comic meta to meta_filepath."""
        normalized_meta = schema.meta(meta)

        meta_dirpath = os.path.dirname(meta_filepath)
        os.makedirs(meta_dirpath, exist_ok=True)

        yamla.to_file(meta_filepath, normalized_meta)

        if _CACHE_USE:
            meta_mtime = os.path.getmtime(meta_filepath)
            self.__meta_to_cache(meta_filepath, meta_mtime, normalized_meta)

    @staticmethod
    def update(ori_meta, volumes, finished):
        """Get updated meta data by original meta and new incoming info."""
        ret_meta = ori_meta.copy()

        now = DT.datetime.now(DT.timezone.utc)

        ret_meta['volumes_checked_time'] = now
        ret_meta['finished'] = finished

        if volumes != ret_meta.get('volumes'):
            ret_meta['volumes'] = volumes
            ret_meta['volumes_modified_time'] = now

        return ret_meta

    @staticmethod
    def create(parsed_meta, url):
        """Generate a fully new meta by parsed result and source url."""
        ret_meta = parsed_meta.copy()

        now = DT.datetime.now(DT.timezone.utc)
        ret_meta['volumes_checked_time'] = now
        ret_meta['volumes_modified_time'] = now
        ret_meta['url'] = url

        return ret_meta
