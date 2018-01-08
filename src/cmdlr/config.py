"""Cmdlr config system."""

import os

from . import yamla
from . import schema


_default_config = {
        'book_concurrent': 10,
        'delay': 1.0,
        'dirs': ['~/comics'],
        'disabled_analyzers': [],
        'extra_analyzer_dir': None,
        'max_retry': 4,
        'per_host_concurrent': 2,
        'proxy': None,
        }

_config_filepath = os.path.join(
        os.getenv(
            'XDG_CONFIG_HOME',
            os.path.join(os.path.expanduser('~'), '.config'),
            ),
        'cmdlr',
        'config.yaml',
        )

_config = None


def _normalize_path(path):
    return os.path.expanduser(path)


def _create_default(filepath):
    """Create default config on `filepath` location."""
    yamla.to_file(filepath, _default_config, comment_out=True)


def _init():
    if not os.path.exists(_config_filepath):
        _create_default(_config_filepath)

    global _config
    _config = schema.config(yamla.from_file(_config_filepath))


def get_incoming_dir():
    """Get incoming dir."""
    return _normalize_path(
            _config.get('dirs', _default_config.get('dirs'))[0]
            )


def get_all_dirs():
    """Get all dirs."""
    return list(map(
        _normalize_path,
        _config.get('dirs', _default_config.get('dirs')),
        ))


def get_extra_analyzer_dir():
    """Get extra analyzer dir."""
    extra_analyzer_dir = _config.get('extra_analyzer_dir',
                                     _default_config.get('extra_analyzer_dir'))
    if extra_analyzer_dir:
        return _normalize_path(extra_analyzer_dir)


def get_disabled_analyzers():
    """Get disabled analyzers."""
    return _config.get('disabled_analyzers',
                       _default_config.get('disabled_analyzers'))


def get_per_host_concurrent():
    """Get per-host concurrent number."""
    return _config.get('per_host_concurrent',
                       _default_config.get('per_host_concurrent'))


def get_book_concurrent():
    """Get per-host concurrent number."""
    return _config.get('book_concurrent',
                       _default_config.get('book_concurrent'))


def get_max_retry():
    """Get max retry number."""
    return _config.get('max_retry', _default_config.get('max_retry'))


def get_delay():
    """Get global download delay."""
    return _config.get('delay', _default_config.get('delay'))


def get_proxy():
    """Get extra analyzer dir."""
    return _config.get('proxy', _default_config.get('proxy'))


def get_customization(analyzer_name):
    """Get user setting for an analyzer."""
    return _config.get('customization', {}).get(analyzer_name, {})


_init()
