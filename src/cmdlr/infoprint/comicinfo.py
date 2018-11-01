"""Print comic(s) infomations."""

from functools import reduce

from wcwidth import wcswidth

from ..comic import ComicVolume
from ..jsona import get_json_line


def _pick_comics(urls, cmgr):
    """Pick comics by commandline url."""
    if not urls:
        comics = cmgr.get_all()

    else:
        comics, _ = cmgr.get_selected(urls)

    return comics


def _get_max_width(strings):
    """Get max display width."""
    return reduce(
        lambda acc, s: max(acc, wcswidth(s)),
        strings,
        0,
    )


def _get_padding_space(string, max_width):
    length = max_width - wcswidth(string)

    return ' ' * length


def _print_standard(comic, name_max_width, wanted_vol_names):
    extra_info = {}
    meta = comic.meta

    extra_info['name_padding'] = _get_padding_space(
        meta['name'],
        name_max_width,
    )

    wanted_vol_num = len(wanted_vol_names)
    extra_info['wanted_vol_num_str'] = (
        '{:<+4}'.format(wanted_vol_num) if wanted_vol_num
        else '    '
    )

    print('{name}{name_padding}  {wanted_vol_num_str} {url}'
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


def print_comic_info(cmgr, urls, detail_mode):
    """Print comics in comic's pool with selected urls."""
    comics = _pick_comics(urls, cmgr)

    if not comics:
        return

    names, comics = zip(*sorted([
        (comic.meta['name'], comic)
        for comic in comics
    ]))

    name_max_width = _get_max_width(names)

    for comic in comics:
        wanted_vol_names = ComicVolume(comic).get_wanted_names()

        _print_standard(comic, name_max_width, wanted_vol_names)

        if detail_mode:
            _print_detail(comic, wanted_vol_names)


def print_comic_json(cmgr, urls):
    """Print all info in jsonline format."""
    comics = _pick_comics(urls, cmgr)

    for comic in comics:
        wanted_vol_names = sorted(ComicVolume(comic).get_wanted_names())
        wanted_vol_count = len(wanted_vol_names)

        data = {
            'meta': comic.meta,
            'dir': comic.dir,
            'volumes': {
                'wanted': {
                    'names': wanted_vol_names,
                    'count': wanted_vol_count,
                },
                'existed': {
                    'count': len(comic.meta['volumes']) - wanted_vol_count
                },
            }
        }

        print(get_json_line(data))
