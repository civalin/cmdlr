"""Cmdlr yaml access functions."""

import yaml


yaml.Dumper.ignore_aliases = lambda *args: True


def from_yaml_string(string):
    """Get yaml data from file."""
    return (yaml.load(
        string,
        Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader),
    ) or {})


def from_yaml_filepath(filepath):
    """Get yaml data from file."""
    with open(filepath, 'r', encoding='utf8') as f:
        return (yaml.load(
            f.read(),
            Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader),
        ) or {})
