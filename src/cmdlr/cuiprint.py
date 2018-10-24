"""Cmdlr cui print support module."""

import functools
import textwrap

import wcwidth

from . import cvolume


def _get_max_dw(strings):
    """Get max display width."""
    return functools.reduce(
        lambda acc, s: max(acc, wcwidth.wcswidth(s)),
        strings,
        0,
    )


def _get_column_width(string, max_width):
    len_diff = wcwidth.wcswidth(string) - len(string)

    return max_width - len_diff


def _print_standard(c, max_ndw):
    cname = c.meta['name']
    fin = '[F]' if c.meta['finished'] else '   '
    name_cw = _get_column_width(cname, max_ndw)
    nd_volnames = cvolume.get_not_downloaded_volnames(
        c.dir, cname, c.meta['volumes'].keys())
    ndlen = len(nd_volnames)
    ndlenstr = '{:<+4}'.format(ndlen) if ndlen else '    '

    tpl = ('{{name:<{name_cw}}} {{fin}} {{ndlenstr}} {{url}}'
           .format(name_cw=name_cw))
    print(tpl.format(**c.meta, fin=fin, ndlenstr=ndlenstr))

    return nd_volnames


def _print_detail(c, nd_volnames):
    print('  => {dir}'.format(dir=c.dir))

    nd_volnames_set = set(nd_volnames)
    max_vndw = _get_max_dw(c.meta['volumes'].keys())

    for vname, vurl in sorted(c.meta['volumes'].items()):
        no_exists = '+' if vname in nd_volnames_set else ' '
        vn_cw = _get_column_width(vname, max_vndw)

        tpl = ('    {{no_exists}} {{vname:<{vn_cw}}} {{vurl}}'
               .format(vn_cw=vn_cw))
        print(tpl.format(vname=vname, no_exists=no_exists, vurl=vurl))

    print()


def print_comic_info(url_to_comics, detail_mode):
    """Print comics in comic's pool with selected urls."""
    names = [c.meta['name'] for c in url_to_comics.values()]
    max_ndw = _get_max_dw(names)

    for _, c in sorted([(c.meta['name'], c) for c in url_to_comics.values()]):
        nd_volnames = _print_standard(c, max_ndw)

        if detail_mode:
            _print_detail(c, nd_volnames)


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
                print(textwrap.indent(desc, ' ' * 4))

                return

        print('Analyzer: "{}" are not exists or enabled.'.format(aname))
