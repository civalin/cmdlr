"""Cmdlr yaml access functions."""

import os
import sys
from collections import OrderedDict

from ruamel.yaml import YAML


_yaml = YAML()
_yaml.default_flow_style = False
_yaml.allow_unicode = True
_yaml.width = 78


def from_yaml_string(string):
    """Get yaml data from string."""
    return _yaml.load(string)


def from_yaml_filepath(filepath):
    """Get yaml data from file."""
    with open(filepath, 'r', encoding='utf8') as f:
        return _yaml.load(f) or OrderedDict()


def to_yaml_stream(data, stream=sys.stdout, **kwargs):
    """Dump to stream in yaml format."""
    _yaml.dump(data, stream, **kwargs)


def to_yaml_filepath(data, filepath, **kwargs):
    """Save data to yaml file."""
    dirpath = os.path.dirname(filepath)

    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    with open(filepath, 'w', encoding='utf8') as f:
        _yaml.dump(data, f, **kwargs)


def comment_out_transform(string):
    """As a transform of yaml.dump() for comment out all the line."""
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
