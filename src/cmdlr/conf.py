"""Cmdlr config system."""

import os

from .schema import config_schema

from .yamla import from_yaml_file
from .yamla import to_yaml_file
from .merge import merge_dict


def _normalize_path(path):
    return os.path.expanduser(path)


class Config:
    """Config maintainer object."""

    default_config = {
        'data_dirs': [
            '~/comics',
        ],
        'network': {
            'delay': 1.0,
            'max_try': 5,
            'total_connection': 10,
            'per_host_connection': 2,
        },
        'book_concurrent': 6,
        'analyzer_dir': None,
        'analyzer_pref': {},
    }

    default_config_filepath = os.path.join(
        os.getenv(
            'XDG_CONFIG_HOME',
            os.path.join(os.path.expanduser('~'), '.config'),
        ),
        'cmdlr',
        'config.yaml',
    )

    @classmethod
    def __build_config_file(cls, filepath):
        """Create a config file template at specific filepath."""
        to_yaml_file(filepath, cls.default_config, comment_out=True)

    def __get_default_analyzer_pref(self):
        network = self.__config.get('network')

        return {
            'system': {
                'enabled': True,
                'max_try': network['max_try'],
                'per_host_connection': network['per_host_connection'],
                'delay': network['delay'],
            },
        }

    def __init__(self):
        """Init the internal __config variable."""
        self.__config = config_schema(type(self).default_config)

    def load_or_build(self, *filepaths):
        """Load and update internal config from specific filepaths.

        If filepath in filepaths not exists, build it with default
        configuration.
        """
        for filepath in filepaths:
            if not os.path.exists(filepath):
                type(self).__build_config_file(filepath)

            incoming_config = config_schema(from_yaml_file(filepath))
            merged_config = merge_dict(self.__config, incoming_config)

            self.__config = config_schema(merged_config)

    @property
    def incoming_data_dir(self):
        """Get incoming dir."""
        return _normalize_path(
            self.__config.get('data_dirs')[0]
        )

    @property
    def data_dirs(self):
        """Get all dirs."""
        return list(map(
            _normalize_path,
            self.__config.get('data_dirs'),
        ))

    @property
    def analyzer_dir(self):
        """Get analyzer dir."""
        analyzer_dir = self.__config.get('analyzer_dir')

        if analyzer_dir:
            return _normalize_path(analyzer_dir)

    @property
    def total_connection(self):
        """Get total connection count."""
        return self.__config.get('network').get('total_connection')

    @property
    def book_concurrent(self):
        """Get book concurrent count."""
        return self.__config.get('book_concurrent')

    def is_enabled_analyzer(self, analyzer_name):
        """Check a analyzer_name is enabled."""
        system = self.get_analyzer_system_pref(analyzer_name)

        return system.get('enabled')

    def get_raw_analyzer_pref(self, analyzer_name):
        """Get user setting for an analyzer, include "system"."""
        default_analyzer_pref = self.__get_default_analyzer_pref()
        user_analyzer_pref = (self
                              .__config.get('analyzer_pref', {})
                              .get(analyzer_name, {}))

        raw_analyzer_pref = merge_dict(
            default_analyzer_pref,
            user_analyzer_pref,
        )

        return raw_analyzer_pref

    def get_analyzer_pref(self, analyzer_name):
        """Get user setting for analyzer, without "system"."""
        analyzer_pref = self.get_raw_analyzer_pref(analyzer_name)
        analyzer_pref.pop('system')

        return analyzer_pref

    def get_analyzer_system_pref(self, analyzer_name):
        """Get "system" part of user setting for analyzer."""
        raw_analyzer_pref = self.get_raw_analyzer_pref(analyzer_name)

        return raw_analyzer_pref.get('system')
