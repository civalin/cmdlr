"""Cmdlr cui print support module."""

import sys
import functools
import textwrap

import wcwidth

from .exception import NoMatchAnalyzer
from .volfile import ComicVolume


def _get_max_width(strings):
    """Get max display width."""
    return functools.reduce(
        lambda acc, s: max(acc, wcwidth.wcswidth(s)),
        strings,
        0,
    )


def _get_padding_space(string, max_width):
    length = max_width - wcwidth.wcswidth(string)

    return ' ' * length


def _print_standard(comic, name_max_width, wanted_vol_names):
    extra_info = {}
    meta = comic.meta

    extra_info['name_padding'] = _get_padding_space(
        meta['name'], name_max_width)
    extra_info['fin'] = '[F]' if meta['finished'] else '   '

    wanted_vol_num = len(wanted_vol_names)
    extra_info['wanted_vol_num_str'] = (
        '{:<+4}'.format(wanted_vol_num) if wanted_vol_num else '    ')

    print('{name}{name_padding} {fin} {wanted_vol_num_str} {url}'
          .format(**meta, **extra_info))


def _print_detail(comic, wanted_vol_names):
    print('  => {dir}'.format(dir=comic.dir))

    wanted_vol_names_set = set(wanted_vol_names)
    vol_max_width = _get_max_width(comic.meta['volumes'].keys())

    for vol_name, vurl in sorted(comic.meta['volumes'].items()):
        info = {
            'vol_name': vol_name,
            'vurl': vurl,
            'no_exists': '+' if vol_name in wanted_vol_names_set else ' ',
            'vol_padding': _get_padding_space(vol_name, vol_max_width),
        }

        print('    {no_exists} {vol_name}{vol_padding} {vurl}'
              .format(**info))

    print()


def print_comic_info(url_to_comics, detail_mode):
    """Print comics in comic's pool with selected urls."""
    names, comics = zip(*sorted([
        (comic.meta['name'], comic)
        for comic in url_to_comics.values()
    ]))

    name_max_width = _get_max_width(names)

    for comic in comics:
        wanted_vol_names = ComicVolume(comic).get_wanted_names()

        _print_standard(comic, name_max_width, wanted_vol_names)

        if detail_mode:
            _print_detail(comic, wanted_vol_names)


def print_analyzer_info(analyzer_infos, aname):
    """Print analyzer info by analyzer name."""
    if aname is None:
        print('Enabled analyzers:')

        for local_aname, _ in analyzer_infos:
            print(textwrap.indent(
                '- {}'.format(local_aname),
                ' ' * 4,
            ))

        print()

    else:
        for local_aname, desc in analyzer_infos:
            if aname == local_aname:
                print('[{}]'.format(aname))
                print(textwrap.indent(
                    desc,
                    ' ' * 4,
                ))

                return

        print('Analyzer: "{}" are not exists or enabled.'.format(aname),
              file=sys.stderr)


def print_useless_urls(amgr, urls):
    """Print urls without a matched analyzer."""
    for url in urls:
        try:
            amgr.get_match_analyzer(url)
        except NoMatchAnalyzer as e:
            print('No Matched Analyzer: {}'.format(url), file=sys.stderr)
