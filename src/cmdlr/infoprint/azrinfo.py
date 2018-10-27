"""Cmdlr cui print support module."""

import sys
from textwrap import indent
from textwrap import dedent

import yaml

from ..exception import NoMatchAnalyzer


def _print_analyzer_list(analyzer_infos):
    print('Enabled analyzers:')

    names, _, _, _ = zip(*analyzer_infos)
    names_text = indent('\n'.join(names), '    - ') + '\n'

    print(names_text)


def _print_analyzer_detail(analyzer_info):
    def get_pref_text(title, pref, name):
        wrapped_pref = {'analyzer_pref': {name: pref}}
        content = indent(yaml.dump(wrapped_pref), ' ' * 4)

        return '\n\n'.join([title, content]).strip()

    def get_prefs_text(default_pref, current_pref, name):
        if not default_pref:
            return None

        return '\n\n'.join([
            get_pref_text('[Preferences (default)]', default_pref, name),
            get_pref_text('[Preferences (current)]', current_pref, name),
        ]).strip()

    name, desc, default_pref, current_pref = analyzer_info

    nice_desc = (dedent(desc) if desc
                 else 'This analyzer has no description :(').strip()
    sections = [
        text for text
        in [nice_desc, get_prefs_text(default_pref, current_pref, name)]
        if text
    ]

    total_text = '\n\n'.join(sections).strip() + '\n'

    print('[{}]'.format(name))
    print(indent(
        total_text,
        '    ',
    ))


def print_analyzer_info(analyzer_infos, aname):
    """Print analyzer info by analyzer name."""
    if aname is None:
        _print_analyzer_list(analyzer_infos)

    else:
        for analyzer_info in analyzer_infos:
            local_name = analyzer_info[0]

            if aname == local_name:
                _print_analyzer_detail(analyzer_info)

                return

        print('Analyzer: "{}" are not exists or enabled.'.format(aname),
              file=sys.stderr)


def print_not_matched_urls(amgr, urls):
    """Print urls without a matched analyzer."""
    for url in urls:
        try:
            amgr.get_match_analyzer(url)
        except NoMatchAnalyzer as e:
            print('No Matched Analyzer: {}'.format(url), file=sys.stderr)
