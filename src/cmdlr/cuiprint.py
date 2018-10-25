"""Cmdlr cui print support module."""

import functools
import textwrap

import wcwidth

from . import cvolume


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


def _print_standard(comic, name_max_width, nd_volnames):
    extra_info = {}
    meta = comic.meta

    extra_info['name_padding'] = _get_padding_space(
        meta['name'], name_max_width)
    extra_info['fin'] = '[F]' if meta['finished'] else '   '

    nd_vol_num = len(nd_volnames)
    extra_info['nd_vol_num_str'] = (
        '{:<+4}'.format(nd_vol_num) if nd_vol_num else '    ')

    print('{name}{name_padding} {fin} {nd_vol_num_str} {url}'
          .format(**meta, **extra_info))


def _print_detail(comic, nd_volnames):
    print('  => {dir}'.format(dir=comic.dir))

    nd_volnames_set = set(nd_volnames)
    vol_max_width = _get_max_width(comic.meta['volumes'].keys())

    for vname, vurl in sorted(comic.meta['volumes'].items()):
        info = {
            'vname': vname,
            'vurl': vurl,
            'no_exists': '+' if vname in nd_volnames_set else ' ',
            'vol_padding': _get_padding_space(vname, vol_max_width),
        }

        print('    {no_exists} {vname}{vol_padding} {vurl}'
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
        nd_volnames = cvolume.get_not_downloaded_volnames(
            comic.dir,
            comic.meta['name'],
            comic.meta['volumes'].keys(),
        )

        _print_standard(comic, name_max_width, nd_volnames)

        if detail_mode:
            _print_detail(comic, nd_volnames)


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

        print('Analyzer: "{}" are not exists or enabled.'.format(aname))
