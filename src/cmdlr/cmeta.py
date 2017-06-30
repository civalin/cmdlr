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

from . import schema
from . import yamla
from . import exceptions
from . import cmetacache


_COMIC_META_FILENAME = '.comic-meta.yaml'


def _get_meta_filepath(path):
    return os.path.join(path, _COMIC_META_FILENAME)


def _has_meta_file(path):
    meta_path = _get_meta_filepath(path)
    if os.path.isfile(meta_path):
        return True

    return False


def load_meta(path):
    """Load single comic meta dict form path.

    Args:
        path (str): dir path of the comic book.
    """
    if not _has_meta_file(path):
        raise exceptions.NotAComicDir(path)

    meta_filepath = _get_meta_filepath(path)

    meta_mtime = os.path.getmtime(meta_filepath)
    meta_from_cache = cmetacache.load(meta_filepath, meta_mtime)

    if meta_from_cache:
        meta = meta_from_cache
    else:
        meta = yamla.from_file(meta_filepath)
        cmetacache.save(meta_filepath, meta_mtime, meta)

    return meta


def save_meta(path, meta):
    """Save comic meta to meta filepath.

    Args:
        path (str): dir path of the comic book.
        meta (dict): the meta should be save.
    """
    normalized_meta = schema.meta(meta)

    os.makedirs(path, exist_ok=True)

    meta_filepath = _get_meta_filepath(path)
    yamla.to_file(meta_filepath, normalized_meta)

    meta_mtime = os.path.getmtime(meta_filepath)
    cmetacache.save(meta_filepath, meta_mtime, normalized_meta)


def get_updated_meta(ori_meta, volumes, finished):
    """Get updated meta data by original meta and new incoming info."""
    ret_meta = ori_meta.copy()

    now = DT.datetime.now(DT.timezone.utc)

    ret_meta['volumes_checked_time'] = now
    ret_meta['finished'] = finished

    if volumes != ret_meta.get('volumes'):
        ret_meta['volumes'] = volumes
        ret_meta['volumes_modified_time'] = now

    return ret_meta


def get_new_meta(parsing_meta, url):
    """Generate a fully new metadata by parsing result and source url."""
    ret_meta = parsing_meta.copy()

    now = DT.datetime.now(DT.timezone.utc)
    ret_meta['volumes_checked_time'] = now
    ret_meta['volumes_modified_time'] = now
    ret_meta['url'] = url

    return ret_meta
