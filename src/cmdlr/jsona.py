"""Cmdlr json access functions."""

import os
import json
from datetime import datetime

from .yamla import from_yaml_filepath


class _MetaEncoder(json.JSONEncoder):
    """Allow to encode extra object."""

    def default(self, o):
        try:
            return {
                '__type__': 'timestamp',
                '__value__': o.strftime('%Y-%m-%dT%H:%M:%S'),
            }

        except Exception:
            return super().default(o)


def _object_hook(dct):
    if dct.get('__type__', '') == 'timestamp':
        return datetime.strptime(dct.get('__value__'), '%Y-%m-%dT%H:%M:%S')

    return dct


def from_json_filepath(filepath):
    """Get json data from file."""
    with open(filepath, 'r', encoding='utf8') as f:
        return json.load(f, object_hook=_object_hook,) or dict()


def from_json_yaml_filepath(filepath):
    """Search .yaml as backup data source, for compatibility."""
    if os.path.isfile(filepath):
        data = from_json_filepath(filepath)

    else:
        yaml_filepath = os.path.splitext(filepath)[0] + '.yaml'
        data = from_yaml_filepath(yaml_filepath)

    return data


def to_json_filepath(data, filepath):
    """Save data to json file."""
    dirpath = os.path.dirname(filepath)

    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    with open(filepath, 'w', encoding='utf8') as f:
        json.dump(data,
                  f,
                  ensure_ascii=False,
                  indent=2,
                  cls=_MetaEncoder)


def get_json_line(data):
    """Get json string from data."""
    return json.dumps(data,
                      ensure_ascii=False,
                      sort_keys=True,
                      cls=_MetaEncoder)
