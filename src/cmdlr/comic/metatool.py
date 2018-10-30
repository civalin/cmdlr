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

from ruamel.yaml.comments import CommentedMap

from ..schema import meta_schema

from ..yamla import from_yaml_filepath
from ..yamla import to_yaml_filepath


_CACHE_USE = True


def _get_ordered_meta(meta):
    """Return a ordered base meta."""
    ordered_keys = [
        'name',
        'authors',
        'descriptions',
        'finished',
        'volumes',
        'url',
        'volumes_checked_time',
        'volumes_modified_time',
    ]

    ordered_meta = CommentedMap([
        (key, meta[key])
        for key in ordered_keys if key in meta
    ])

    for key in meta.keys():
        if key not in ordered_meta:
            ordered_meta[key] = meta[key]

    ordered_meta['volumes'] = CommentedMap(sorted(
        [(vname, url) for vname, url in ordered_meta['volumes'].items()],
        key=lambda item: item[0]
    ))

    return ordered_meta


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
            self.cache = {}
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
                meta = from_yaml_filepath(meta_filepath)
                self.__meta_to_cache(meta_filepath, meta_mtime, meta)

        else:
            meta = from_yaml_filepath(meta_filepath)

        return meta

    def save(self, meta_filepath, meta):
        """Save comic meta to meta_filepath."""
        normalized_meta = meta_schema(meta)

        meta_dirpath = os.path.dirname(meta_filepath)
        os.makedirs(meta_dirpath, exist_ok=True)

        to_yaml_filepath(normalized_meta, meta_filepath)

        if _CACHE_USE:
            meta_mtime = os.path.getmtime(meta_filepath)
            self.__meta_to_cache(meta_filepath, meta_mtime, normalized_meta)

    @staticmethod
    def update(ori_meta, parsed_meta):
        """Get updated meta by ori_meta and incoming parsed_meta."""
        building_meta = ori_meta.copy()

        now = DT.datetime.now(DT.timezone.utc)

        # building_meta['name'] = parsed_meta['name']  # cause filename change
        building_meta['finished'] = parsed_meta['finished']

        authors = parsed_meta.get('authors')
        description = parsed_meta.get('description')

        if authors:
            building_meta['authors'] = authors

        if description:
            building_meta['description'] = description

        building_meta['volumes_checked_time'] = now

        if parsed_meta['volumes'] != building_meta.get('volumes'):
            building_meta['volumes'] = parsed_meta['volumes']
            building_meta['volumes_modified_time'] = now

        return _get_ordered_meta(building_meta)

    @staticmethod
    def create(parsed_meta, url):
        """Generate a fully new meta by parsed result and source url."""
        building_meta = parsed_meta.copy()

        now = DT.datetime.now(DT.timezone.utc)

        building_meta['volumes_checked_time'] = now
        building_meta['volumes_modified_time'] = now
        building_meta['url'] = url

        return _get_ordered_meta(building_meta)
