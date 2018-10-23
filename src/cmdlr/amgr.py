"""Cmdlr analyzers holder and importer."""

import importlib
import pkgutil
import os
import sys
import functools

from . import exceptions
from . import analyzers as _analyzers  # NOQA


class AnalyzerManager:
    """Import, active, dispatch and hold all analyzer."""

    analyzers_pkgpath = 'cmdlr.analyzers'

    def __init__(self, extra_analyzer_dir, disabled_analyzers=None):
        """Import all analyzers."""
        self.__analyzers = {}

        self.__import_all_analyzer(extra_analyzer_dir, disabled_analyzers)

    def __import_all_analyzer(self, extra_analyzer_dir, disabled_analyzers):
        analyzer_dirs = [os.path.join(os.path.dirname(__file__), 'analyzers')]

        if extra_analyzer_dir and not os.path.isdir(extra_analyzer_dir):
            raise exceptions.ExtraAnalyzersDirNotExists(
                'extra_analyzer_dir already be set but not exists, path: "{}"'
                .format(extra_analyzer_dir))

        elif extra_analyzer_dir:
            analyzer_dirs[:0] = [extra_analyzer_dir]

        for finder, module_name, ispkg in pkgutil.iter_modules(analyzer_dirs):
            if module_name not in disabled_analyzers:
                full_module_name = (type(self).analyzers_pkgpath
                                    + '.'
                                    + module_name)

                spec = finder.find_spec(full_module_name)
                module = importlib.util.module_from_spec(spec)
                sys.modules[full_module_name] = module
                spec.loader.exec_module(module)
                self.__analyzers[module_name] = module

    @functools.lru_cache(maxsize=None, typed=True)
    def get_match_analyzer(self, curl):
        """Get a url matched analyzer."""
        for a in self.__analyzers.values():
            for pattern in a.entry_patterns:
                if pattern.search(curl):
                    return a

        raise exceptions.NoMatchAnalyzer(
            'No Matched Analyzer: {}'.format(curl),
        )

    def get_prop(self, entry_url, prop_name, default=None):
        """Get match analyzer's single prop by url and prop_name."""
        analyzer = self.get_match_analyzer(entry_url)

        return getattr(analyzer, prop_name, default)

    @functools.lru_cache(maxsize=None, typed=True)
    def get_normalized_entry(self, curl):
        """Return the normalized entry url."""
        entry_normalizer = self.get_prop(curl, 'entry_normalizer')

        if entry_normalizer:
            return entry_normalizer(curl)

        return curl

    def get_analyzer_infos(self):
        """Return all analyzer info."""
        def get_desc(analyzer):
            return analyzer.__doc__

        unsorted_infos = [
            (aname, get_desc(analyzer))
            for aname, analyzer in self.__analyzers.items()
        ]

        return sorted(unsorted_infos, key=lambda item: item[0])

    @functools.lru_cache(maxsize=None, typed=True)
    def get_analyzer_name(self, analyzer):
        """Get analyzer local name."""
        return analyzer.__name__.split('.')[-1]
