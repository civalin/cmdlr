"""Cmdlr analyzers holder and importer."""

import importlib
import pkgutil
import os
import sys
import re
from functools import lru_cache
from collections import namedtuple

from .exception import NoMatchAnalyzer
from .exception import ExtraAnalyzersDirNotExists
from .exception import AnalyzerRuntimeError


_AnalyzerInfo = namedtuple(
    'AnalyzerInfo',
    ['name', 'desc', 'default_pref', 'current_pref'],
)


class AnalyzerManager:
    """Import, active, dispatch and hold all analyzer."""

    analyzers_pkgpath = 'cmdlr.analyzers'

    def __init__(self, config):
        """Import all analyzers."""
        self.__analyzers = {}
        self.__analyzer_picker = None
        self.__analyzer_infos = []  # _AnalyzerInfo list
        self.config = config

        self.__import_all_analyzer()
        self.__build_analyzer_picker()

    def __get_analyzer_dirs(self):
        buildin_analyzer_dir = os.path.join(
            os.path.dirname(__file__),
            'analyzers',
        )

        extra_analyzer_dir = self.config.extra_analyzer_dir

        if extra_analyzer_dir and not os.path.isdir(extra_analyzer_dir):
            raise ExtraAnalyzersDirNotExists(
                'extra_analyzer_dir already be set but not exists, path: "{}"'
                .format(extra_analyzer_dir))

        elif extra_analyzer_dir:
            analyzer_dirs = [extra_analyzer_dir, buildin_analyzer_dir]

        else:
            analyzer_dirs = [buildin_analyzer_dir]

        return analyzer_dirs

    def __register_analyzer(self, module, analyzer_name):
        analyzer = module.Analyzer(
            pref=self.config.get_analyzer_pref(analyzer_name),
        )

        self.__analyzers[analyzer_name] = analyzer

        self.__analyzer_infos.append(_AnalyzerInfo(
            name=analyzer_name,
            desc=analyzer.__doc__,
            default_pref=analyzer.default_pref,
            current_pref={
                **analyzer.default_pref,
                **self.config.get_analyzer_pref(analyzer_name),
            },
        ))

    def __import_all_analyzer(self):
        disabled_analyzers = self.config.disabled_analyzers
        analyzer_dirs = self.__get_analyzer_dirs()

        for finder, module_name, ispkg in pkgutil.iter_modules(analyzer_dirs):
            if module_name not in disabled_analyzers:
                full_module_name = ''.join([
                    type(self).analyzers_pkgpath,
                    '.',
                    module_name,
                ])

                spec = finder.find_spec(full_module_name)
                module = importlib.util.module_from_spec(spec)
                sys.modules[full_module_name] = module
                spec.loader.exec_module(module)

                self.__register_analyzer(module, module_name)

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

    @lru_cache(maxsize=None, typed=True)
    def get_match_analyzer(self, curl):
        """Get a url matched analyzer."""
        return self.__analyzer_picker(curl)

    @lru_cache(maxsize=None, typed=True)
    def get_normalized_entry(self, curl):
        """Return the normalized entry url."""
        return self.get_match_analyzer(curl).entry_normalizer(curl)

    def get_analyzer_infos(self):
        """Return all analyzer info."""
        return sorted(self.__analyzer_infos, key=lambda item: item[0])
