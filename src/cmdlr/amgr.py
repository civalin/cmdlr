"""Cmdlr analyzers holder and importer."""

import importlib
import pkgutil
import os
import sys
import re
from functools import lru_cache
from collections import namedtuple
from .analyzer import ANALYZERS_PKGPATH

from .exception import NoMatchAnalyzer
from .exception import ExtraAnalyzersDirNotExists
from .exception import AnalyzerRuntimeError


_AnalyzerInfo = namedtuple(
    'AnalyzerInfo',
    ['name', 'desc', 'default_pref', 'current_pref'],
)


class AnalyzerManager:
    """Import, active, dispatch and hold all analyzer."""

    def __init__(self, config):
        """Import all analyzers."""
        self.__analyzers = {}
        self.__analyzer_picker = None
        self.config = config

        self.__import_all_analyzer()
        self.__build_analyzer_picker()

    def __get_analyzer_dirs(self):
        buildin_analyzer_dir = os.path.join(
            os.path.dirname(__file__),
            'analyzers',
        )

        analyzer_dir = self.config.analyzer_dir

        if analyzer_dir and not os.path.isdir(analyzer_dir):
            raise ExtraAnalyzersDirNotExists(
                'analyzer_dir be set but not exists, path: "{}"'
                .format(analyzer_dir))

        elif analyzer_dir:
            analyzer_dirs = [analyzer_dir, buildin_analyzer_dir]

        else:
            analyzer_dirs = [buildin_analyzer_dir]

        return analyzer_dirs

    def __register_analyzer(self, module, analyzer_name):
        analyzer = module.Analyzer(
            pref=self.config.get_analyzer_pref(analyzer_name),
        )

        self.__analyzers[analyzer_name] = analyzer

    def __import_all_analyzer(self):
        analyzer_dirs = self.__get_analyzer_dirs()

        for finder, module_name, ispkg in pkgutil.iter_modules(analyzer_dirs):
            if self.config.is_enabled_analyzer(module_name):
                full_module_name = ''.join([
                    ANALYZERS_PKGPATH,
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
    def get_normalized_entry(self, curl):
        """Return the normalized entry url."""
        return self.get(curl).entry_normalizer(curl)

    def get_normalized_entrys(self, curls):
        """Return all of the urls to a new url list.

        This returned url list make sure the following things:
            1. all urls are be normalized
            2. no duplicated
            3. all urls match at least one analyzers.
        """
        result = set()

        for url in set(curls):
            try:
                result.add(self.get_normalized_entry(url))

            except NoMatchAnalyzer as e:
                pass

        return result

    @lru_cache(maxsize=None, typed=True)
    def get(self, curl):
        """Get a url matched analyzer."""
        return self.__analyzer_picker(curl)

    def get_all(self):
        """Return all analyzers."""
        return list(self.__analyzers.values())
