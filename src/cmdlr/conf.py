"""Cmdlr config system."""

import os

from .schema import config_schema

from .yamla import from_yaml_string
from .yamla import from_yaml_filepath
from .merge import merge_dict


def _normalize_path(path):
    return os.path.expanduser(path)


_DEFAULT_CONFIG_YAML = """
## This is config file for cmdlr.

## The data directories should be scanning.
##
## the first entry of data_dirs also be considered as `incoming_dir`
## all the "new / incoming" comics will be settled down in the `incoming_dir`
data_dirs:
- '~/comics'

## global network settings
network:
  ## download delay
  ##
  ## every connection will random waiting:
  ##     ((0 ~ delay) * 2) + `dynamic_delay` seconds
  ##
  ## Notice: the `dynamic_delay` only depending on network status.
  delay: 1.0

  max_try: 5               # max try for a single request
  total_connection: 10     # all requests count in the same time
  per_host_connection: 2   # all requests count in the same time & host

book_concurrent: 6   # how many books can processing parallel

## extra analyzer directory
##
## assign a exist directory and put analyzers module or package in here.
## Only useful if user want to develop or use a local analyzer.
analyzer_dir: null

## analyzer preference
##
## Example:
##
## analyzer_pref:
##   <analyzer1_name>:
##     system:                   # every analyzers has `system` area
##       enabled: true           # default: true
##       delay: 2                # default: <network.delay>
##       max_try: 5              # default: <network.max_retry>
##       per_host_connection: 2  # default: <network.per_host_connection>
##
##     # Optional
##     <analyzer1_pref1>: ...
##     <analyzer1_pref2>: ...
##
## Use `cmdlr -a` to find the name of analyzers. and use `cmdlr -a NAME`
## to check the analyzer's detail.
analyzer_pref: {}
""".strip()


def _comment_out(string):
    """Comment out all lines if necessary in string."""
    converted_lines = []

    for line in string.strip().split('\n'):
        if line:
            import re
            space = re.search('^\s*', line).group()
            no_lspace_line = line.strip()

            if no_lspace_line.startswith('#'):
                converted_line = line

            else:
                converted_line = space + '# ' + no_lspace_line

        else:
            converted_line = line

        converted_lines.append(converted_line)

    return '\n'.join(converted_lines) + '\n'


class Config:
    """Config maintainer object."""

    default_config = from_yaml_string(_DEFAULT_CONFIG_YAML)

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
        dirpath = os.path.dirname(filepath)

        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        with open(filepath, mode='w', encoding='utf8') as f:
            f.write(_comment_out(_DEFAULT_CONFIG_YAML))

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

            incoming_config = config_schema(from_yaml_filepath(filepath))
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
