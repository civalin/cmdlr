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

from datetime import datetime

from ..schema import meta_schema

from ..jsona import to_json_filepath
from ..jsona import from_json_yaml_filepath


class MetaToolkit:
    """Process anything relate comic meta."""

    @staticmethod
    def load(meta_filepath):
        """Get meta from filepath."""
        return from_json_yaml_filepath(meta_filepath)

    @staticmethod
    def save(meta_filepath, meta):
        """Save comic meta to meta_filepath."""
        normalized_meta = meta_schema(meta)

        to_json_filepath(normalized_meta, meta_filepath)

    @staticmethod
    def update(ori_meta, parsed_meta):
        """Get updated meta by ori_meta and incoming parsed_meta."""
        building_meta = ori_meta.copy()

        now = datetime.utcnow()
        authors = parsed_meta.get('authors')
        description = parsed_meta.get('description')
        finished = parsed_meta.get('finished')

        if authors:
            building_meta['authors'] = authors

        if description:
            building_meta['description'] = description

        if finished:
            building_meta['finished'] = finished

        building_meta['volumes_checked_time'] = now

        if building_meta.get('volumes') != parsed_meta['volumes']:
            building_meta['volumes'] = parsed_meta['volumes']
            building_meta['volumes_modified_time'] = now

        return building_meta

    @staticmethod
    def create(parsed_meta, url):
        """Generate a fully new meta by parsed result and source url."""
        building_meta = parsed_meta.copy()

        now = datetime.utcnow()

        building_meta['volumes_checked_time'] = now
        building_meta['volumes_modified_time'] = now
        building_meta['url'] = url

        return building_meta
