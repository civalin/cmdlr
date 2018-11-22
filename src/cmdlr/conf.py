"""Cmdlr config system."""

import os
import re

from .schema import config_schema

from .yamla import from_yaml_string
from .yamla import from_yaml_filepath
from .merge import merge_dict


_DEFAULT_CONFIG_YAML = """
## This is config file for cmdlr.



## The data directories should be scanning.
##
## The first entry of data_dirs also be considered as `incoming_dir`, and
## all the "new / incoming" comics will be settled down in the `incoming_dir`
data_dirs:
- '~/comics'



## Set the logging level, is the one of DEBUG, INFO, WARNING, ERROR, CRITICAL
logging_level: INFO



## The directory be used to save the logs.
##
## if null, stop logging any messages into filesystem.
logging_dir: null



## global network settings
##
## ATTENTION: network settings only affect build-in network modules.
##            Currently, the only exception is `npm install` command for
##            extra js dependency when js subsystem initialization.
network:
  ## download delay
  ##
  ## each connection will random waiting:
  ##     max((0 ~ (delay * 2)), dynamic_delay) seconds
  ##
  ## Notice: the `dynamic_delay` only depending on network status.
  delay: 2.5

  timeout: 300               # timeout of a trying of a request
  max_try: 5                 # max try for a single request
  total_connections: 12      # all requests in the same time in whole system
  per_host_connections: 2    # all requests in the same time in a host

  ## assign a socks proxy configuration
  ##
  ## the configuration look like:
  ##   socks5://username:password@127.0.0.1:1080
  ##
  ## if null, stop to using any socks proxy
  socks_proxy: null



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
##     system:                  # any analyzers have a `system` area
##       enabled: true            # default: true
##       delay: 1.0               # default: <network.delay>
##       timeout: 120             # default: <network.timeout>
##       max_try: 5               # default: <network.max_try>
##       per_host_connections: 2  # default: <network.per_host_connections>
##       socks_proxy: null        # default: <network.socks_proxy>
##
##     # Optional
##     <analyzer1_pref1>: ...
##     <analyzer1_pref2>: ...
##
## Use `cmdlr -a` to find the name of analyzers. and use `cmdlr -a NAME`
## to check the analyzer's detail.
analyzer_pref: {}
""".strip()


def _normalize_path(path):
    return os.path.expanduser(path)


def _comment_out(string):
    """Comment out all lines if necessary in string."""
    converted_lines = []

    for line in string.strip().split('\n'):
        if line:
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
        network = self.__config['network']

        return {
            'system': {
                'enabled': True,
                'delay': network['delay'],
                'timeout': network['timeout'],
                'max_try': network['max_try'],
                'per_host_connections': network['per_host_connections'],
                'socks_proxy': network['socks_proxy'],
            },
        }

    def __init__(self):
        """Init the internal __config variable."""
        default_config = from_yaml_string(_DEFAULT_CONFIG_YAML)
        self.__config = config_schema(default_config)

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
            self.__config['data_dirs'][0]
        )

    @property
    def data_dirs(self):
        """Get all dirs."""
        return list(map(
            _normalize_path,
            self.__config['data_dirs'],
        ))

    @property
    def logging_dir(self):
        """Get logging dir."""
        logging_dir = self.__config['logging_dir']

        if logging_dir:
            return _normalize_path(logging_dir)

    @property
    def logging_level(self):
        """Get logging level."""
        return self.__config['logging_level']

    @property
    def analyzer_dir(self):
        """Get analyzer dir."""
        analyzer_dir = self.__config['analyzer_dir']

        if analyzer_dir:
            return _normalize_path(analyzer_dir)

    @property
    def total_connections(self):
        """Get total connection count."""
        return self.__config['network']['total_connections']

    @property
    def book_concurrent(self):
        """Get book concurrent count."""
        return self.__config['book_concurrent']

    def is_enabled_analyzer(self, analyzer_name):
        """Check a analyzer_name is enabled."""
        system = self.get_analyzer_system_pref(analyzer_name)

        return system['enabled']

    def get_raw_analyzer_pref(self, analyzer_name):
        """Get user setting for an analyzer, include "system"."""
        default_analyzer_pref = self.__get_default_analyzer_pref()
        user_analyzer_pref = (self
                              .__config['analyzer_pref']
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

        return raw_analyzer_pref['system']
