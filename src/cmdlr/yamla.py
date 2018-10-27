"""Cmdlr yaml access functions."""

import os

import yaml


yaml.Dumper.ignore_aliases = lambda *args: True


def from_yaml_file(filepath):
    """Get yaml data from file."""
    with open(filepath, 'r', encoding='utf8') as f:
        return (yaml.load(
            f.read(),
            Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader),
        ) or {})


def to_yaml_file(filepath, data, comment_out=False):
    """Save data to yaml file."""
    dirpath = os.path.dirname(filepath)

    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    with open(filepath, 'w', encoding='utf8') as f:
        content = yaml.dump(data,
                            default_flow_style=False,
                            allow_unicode=True,
                            width=78,
                            indent=4)

        if comment_out:
            content = '\n'.join('# ' + line for line in content.split('\n'))

        f.write(content)
