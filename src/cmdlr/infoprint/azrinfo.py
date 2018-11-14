"""Cmdlr cui print support module."""

import sys
from textwrap import indent
from textwrap import dedent

import yaml

from ..exception import NoMatchAnalyzer


def _print_analyzer_list(analyzers):
    print('Enabled analyzers:')

    names = [analyzer.name for analyzer in analyzers]
    names_text = indent('\n'.join(names), '    - ') + '\n'

    print(names_text)


def _print_analyzer_detail(analyzer):
    def get_pref_text(title, pref, name):
        wrapped_pref = {'analyzer_pref': {name: pref}}
        content = indent(
            yaml.dump(wrapped_pref, allow_unicode=True),
            '    ',
        )

        return '\n\n'.join([title, content]).strip()

    def get_prefs_text(default_pref, current_pref, name):
        if not default_pref:
            return ''

        return '\n\n'.join([
            '--------------------',
            get_pref_text('[Preferences (default)]', default_pref, name),
            get_pref_text('[Preferences (current)]', current_pref, name),
        ]).strip()

    sections = []
    sections.append(dedent(analyzer.desc).strip())
    sections.append(get_prefs_text(
        analyzer.default_pref,
        analyzer.current_pref,
        analyzer.name,
    ))

    total_text = '\n\n'.join(sections).strip() + '\n'

    print('[{}]'.format(analyzer.name))
    print(indent(
        total_text,
        '    ',
    ))


def print_analyzer_info(amgr, aname_or_url):
    """Print analyzer info by analyzer name or url."""
    analyzers = sorted(amgr.get_all(), key=lambda analyzer: analyzer.name)

    if aname_or_url is None:
        _print_analyzer_list(analyzers)

    else:
        analyzer = None

        try:
            analyzer = amgr.get(aname_or_url)

        except NoMatchAnalyzer:
            for local_analyzer in analyzers:
                if aname_or_url == local_analyzer.name:
                    analyzer = local_analyzer

        if analyzer:
            _print_analyzer_detail(analyzer)

        else:
            print(('Analyzer: "{}" are not exists or enabled.'
                   .format(aname_or_url)),
                  file=sys.stderr)


def print_not_matched_urls(amgr, urls):
    """Print urls without a matched analyzer."""
    for url in urls:
        try:
            amgr.get(url)

        except NoMatchAnalyzer:
            print('No Matched Analyzer: {}'.format(url), file=sys.stderr)
