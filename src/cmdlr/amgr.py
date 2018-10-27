"""Cmdlr analyzers holder and importer."""

import importlib
import pkgutil
import os
import sys
import functools
import re

from .exception import NoMatchAnalyzer
from .exception import ExtraAnalyzersDirNotExists
from .exception import AnalyzerRuntimeError


class AnalyzerManager:
    """Import, active, dispatch and hold all analyzer."""

    analyzers_pkgpath = 'cmdlr.analyzers'

    def __init__(self, config):
        """Import all analyzers."""
        self.__analyzers = {}
        self.__analyzer_picker = None
        self.config = config

        self.__import_all_analyzer()
        self.__build_analyzer_picker()

    def __import_all_analyzer(self):
        extra_analyzer_dir = self.config.extra_analyzer_dir
        disabled_analyzers = self.config.disabled_analyzers

        analyzer_dirs = [os.path.join(os.path.dirname(__file__), 'analyzers')]

        if extra_analyzer_dir and not os.path.isdir(extra_analyzer_dir):
            raise ExtraAnalyzersDirNotExists(
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

                aname = module_name
                self.__analyzers[aname] = module.Analyzer(
                    pref=self.config.get_analyzer_pref(aname),
                )
                self.__analyzers[aname].aname = aname

    def __build_analyzer_picker(self):
        retype = type(re.compile(''))
        mappers = []

        for aname, analyzer in self.__analyzers.items():
            for pattern in analyzer.entry_patterns:
                if isinstance(pattern, retype):
                    mappers.append((pattern, analyzer))

                elif isinstance(pattern, str):
                    mappers.append((re.compile(pattern), analyzer))

                else:
                    raise AnalyzerRuntimeError(
                        'some entry pattern in analyzer "{}"'
                        ' neither str nor re.compile type'
                        .format(aname)
                    )

        def analyzer_picker(curl):
            for pattern, analyzer in mappers:
                if pattern.search(curl):
                    return analyzer

            raise NoMatchAnalyzer(
                'No Matched Analyzer: {}'.format(curl),
            )

        self.__analyzer_picker = analyzer_picker

    @functools.lru_cache(maxsize=None, typed=True)
    def get_match_analyzer(self, curl):
        """Get a url matched analyzer."""
        return self.__analyzer_picker(curl)

    @functools.lru_cache(maxsize=None, typed=True)
    def get_normalized_entry(self, curl):
        """Return the normalized entry url."""
        return self.get_match_analyzer(curl).entry_normalizer(curl)

    def get_analyzer_infos(self):
        """Return all analyzer info."""
        def get_desc(analyzer):
            return analyzer.__doc__

        unsorted_infos = [
            (aname, get_desc(analyzer))
            for aname, analyzer in self.__analyzers.items()
        ]

        return sorted(unsorted_infos, key=lambda item: item[0])
