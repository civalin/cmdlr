#!/usr/bin/env python3

# import concurrent.futures as CF
import sys
import os
import argparse
import pathlib
# import importlib

from . import comicdb
from . import comicanalyzer
from .analyzers import eightcomic


VERSION = '2.0.0'
_ANALYZERS = []


def import_analyzers_modules():
    analyzers_dir = pathlib.Path(__file__).parent / 'analyzers'
    sys.path.append(str(analyzers_dir))
    # for path in analyzers_dir.glob('*.py'):
    #     if path.stem == '__init__':
    #         continue
    #     ANALYZER_MODULES.append(importlib.import_module(path.stem))
    # remove python editor unuse alert.
    (eightcomic, )
    _ANALYZERS.extend([
        cls() for cls in comicanalyzer.ComicAnalyzer.__subclasses__()])


def get_analyzer_by_url(url):
    for analyzer in _ANALYZERS:
        comic_id = analyzer.url_to_comic_id(url)
        if comic_id:
            return analyzer
    return None


def get_args(cdb):
    def parse_args():
        analyzers_desc_text = '\n'.join([
            '    ' + azr.codename + ' - ' + azr.desc
            for azr in _ANALYZERS])
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Subscribe and download your comic books!\n'
                        '\n'
                        '  Enabled analyzers:\n' + analyzers_desc_text
            )

        parser.add_argument(
            '-s', '--subscribe', metavar='comic_entry_url',
            dest='subscribe_comic_entry_urls', type=str, nargs='+',
            help='Subscribe some comic book.')

        # parser.add_argument(
        #     '-u', '--unsubscribe', metavar='comic_id',
        #     dest='unsubscribe_comic_ids', type=str, nargs='+',
        #     help='Unsubscribe some comic book.')

        # parser.add_argument(
        #     '-l', '--list-info', dest='list_info',
        #     action='store_const', const=True, default=False,
        #     help='List all subscribed books and other info.')

        # parser.add_argument(
        #     '-r', '--refresh', dest='refresh',
        #     action='store_const', const=True, default=False,
        #     help='Update all subscribed comic info.')

        # parser.add_argument(
        #     '-d', '--download', dest='download',
        #     action='store_const', const=True, default=False,
        #     help='Download subscribed comic books.')

        # parser.add_argument(
        #     '-o', '--output-dir', metavar='DIR', dest='output_dir', type=str,
        #     default=cdb.output_dir,
        #     help='Change download folder.'
        #          '\n(Current value: %(default)s)')

        # parser.add_argument(
        #     '--init', dest='init',
        #     action='store_const', const=True, default=False,
        #     help='Clear your whole comic book database!')

        parser.add_argument(
            '-v', '--version', action='version', version=VERSION)

        args = parser.parse_args()
        return args

    args = parse_args()
    return args


def main():
    import_analyzers_modules()
    cdb = comicdb.ComicDB(dbpath=os.path.expanduser('~/comicdb_test.db'))
    args = get_args(cdb)

    if args.subscribe_comic_entry_urls:
        for url in args.subscribe_comic_entry_urls:
            print(url)
            azr = get_analyzer_by_url(url)
            comic_id = azr.url_to_comic_id(url)
            data = azr.get_comic_info(comic_id)
            for volume in data['volumes']:
                print(azr.get_volume_pages(
                    comic_id, volume['volume_id'], data['extra_data']))
    # if args.refresh:
    #     cdb.refresh()
    # if args.output_dir:
    #     cdb.set_output_dir(args.output_dir)
    # if args.unsubscribe_comic_ids:
    #     print('Unsubscribe:')
    #     for comic_id in args.unsubscribe_comic_ids:
    #         cdb.unsubscribe(comic_id)
    # if args.subscribe_comic_ids:
    #     for comic_id in args.subscribe_comic_ids:
    #         cdb.subscribe(comic_id)
    # if args.list_info:
    #     cdb.list_info()
    # if args.download:
    #     cdb.download_subscribed(cdb.get_output_dir())
    # if args.init:
    #     cdb.purge_tables()


if __name__ == "__main__":
    main()
