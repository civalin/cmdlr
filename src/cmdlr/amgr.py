"""Cmdlr analyzers holder and importer."""

import importlib
import pkgutil
import os
import sys
import functools

from . import exceptions
from . import config
from . import analyzers as _analyzers  # NOQA

_analyzers_pkgpath = 'cmdlr.analyzers'

analyzers = {}


def _init(extra_analyzer_dir, disabled_analyzers=None):
    """Init all analyzers."""
    analyzers.clear()

    analyzer_dirs = [os.path.join(os.path.dirname(__file__), 'analyzers')]

    if extra_analyzer_dir and not os.path.isdir(extra_analyzer_dir):
        raise exceptions.ExtraAnalyzersDirNotExists(
            'extra_analyzer_dir already be set but not exists, path: "{}"'
            .format(extra_analyzer_dir))

    elif extra_analyzer_dir:
        analyzer_dirs[:0] = [extra_analyzer_dir]

    for finder, module_name, ispkg in pkgutil.iter_modules(analyzer_dirs):
        if module_name not in disabled_analyzers:
            full_module_name = _analyzers_pkgpath + '.' + module_name

            spec = finder.find_spec(full_module_name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_module_name] = module
            spec.loader.exec_module(module)
            analyzers[module_name] = module


@functools.lru_cache(maxsize=None, typed=True)
def get_match_analyzer(curl):
    """Get a url matched analyzer."""
    for a in analyzers.values():
        for pattern in a.entry_patterns:
            if pattern.search(curl):
                return a

    raise exceptions.NoMatchAnalyzer('No Matched Analyzer: {}'.format(curl))


@functools.lru_cache(maxsize=None, typed=True)
def get_analyzer_name(analyzer):
    """Get analyzer local name."""
    return analyzer.__name__.split('.')[-1]


def get_prop(entry_url, prop_name, default=None):
    """Get match analyzer's single prop by url and prop_name."""
    analyzer = get_match_analyzer(entry_url)

    return getattr(analyzer, prop_name, default)


@functools.lru_cache(maxsize=None, typed=True)
def get_normalized_entry(curl):
    """Return the normalized entry url."""
    entry_normalizer = get_prop(curl, 'entry_normalizer')

    if entry_normalizer:
        return entry_normalizer(curl)

    return curl


_init(
    extra_analyzer_dir=config.get_extra_analyzer_dir(),
    disabled_analyzers=config.get_disabled_analyzers(),
)
