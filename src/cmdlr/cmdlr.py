#!/usr/bin/env python3

#########################################################################
#  The MIT License (MIT)
#
#  Copyright (c) 2014~2015 CIVA LIN (林雪凡)
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##########################################################################

import concurrent.futures as CF
import datetime as DT
import os
import sys
import argparse
import pathlib
import textwrap
import shutil
import queue
import collections

from . import comicdb
from . import comicanalyzer
from . import downloader

from . analyzers import *


VERSION = '2.0.0'
_ANALYZERS = []


def get_custom_data_key(azr):
    return 'analyzer_custom_data_' + azr.codename()


def set_custom_data(cdb, custom_data):
    try:
        (codename, data) = custom_data.split('/', 1)
        if data == '':
            data = {}
        else:
            pairs = [pair.split('=', 1) for pair in data.split(',')]
            data = {key: value for key, value in pairs}
    except ValueError:
        print('"{}" cannot be parsed. Cancel.'.format(
            custom_data))
        return
    for cls in comicanalyzer.ComicAnalyzer.__subclasses__():
        if cls.codename() == codename:
            try:
                cls(data)
                key = get_custom_data_key(cls)
                print('{} <= {}'.format(cls.name(), data))
                cdb.set_option(key, data)
                print('Updated done!')
            except:
                print('Custom data test failed. Cancel.')
            return
    print('Analyzer codename: "{}" not found. Cancel.'.format(codename))


def get_custom_data_in_cdb(cdb, cls):
    key = get_custom_data_key(cls)
    data = cdb.get_option(key)
    if not (data and type(data) == dict):
        data = {}
    return data


def initial_analyzers(cdb):
    for cls in comicanalyzer.ComicAnalyzer.__subclasses__():
        data = get_custom_data_in_cdb(cdb, cls)
        azr = cls(data)
        _ANALYZERS.append(azr)


def get_analyzer_by_comic_id(comic_id):
    for azr in _ANALYZERS:
        if comic_id.split('/')[0] == azr.codename():
            return azr
    return None


def get_analyzer_and_comic_id(comic_entry):
    def get_analyzer_by_url(url):
        for analyzer in _ANALYZERS:
            comic_id = analyzer.url_to_comic_id(url)
            if comic_id:
                return analyzer
        return None

    azr = get_analyzer_by_url(comic_entry)
    if azr is None:
        azr = get_analyzer_by_comic_id(comic_entry)
        if azr is None:
            print('"{}" not fits any analyzers.'.format(comic_entry))
            return (None, None)
        else:
            comic_id = comic_entry
    else:
        comic_id = azr.url_to_comic_id(comic_entry)
    return (azr, comic_id)


def get_comic_info_text(cdb, comic_info, verbose=0):
    volumes_status = cdb.get_comic_volumes_status(
        comic_info['comic_id'])
    data = {'comic_id': comic_info['comic_id'],
            'title': comic_info['title'],
            'desc': comic_info['desc'],
            'no_downloaded_count': volumes_status['no_downloaded_count'],
            'no_downloaded_names': ','.join(
                [name.lstrip('w') for name in
                 volumes_status['no_downloaded_names'][:2]]),
            'downloaded_count': volumes_status['downloaded_count'],
            'total': volumes_status['total'],
            }
    texts = []
    texts.append('{comic_id:<15} {title}')
    if verbose >= 1:
        texts.append(' ({downloaded_count}/{total})')
        if data['no_downloaded_count'] != 0:
            texts.insert(0, '{no_downloaded_count:<+4} ')
        else:
            texts.insert(0, '     ')
    if verbose >= 2:
        if data['no_downloaded_count'] > 0:
            texts.append(' + {no_downloaded_names}')
        if data['no_downloaded_count'] > 2:
            texts.append(',...')
    text = ''.join(texts).format(**data)
    if verbose >= 3:
        text = '\n'.join([text,
                          textwrap.indent(
                              textwrap.fill('{desc}'.format(**data), 35),
                              '    '),
                          ''])
    return text


def subscribe(cdb, comic_entry, verbose):
    azr, comic_id = get_analyzer_and_comic_id(comic_entry)
    if azr is None:
        return None
    comic_info = azr.get_comic_info(comic_id)
    cdb.upsert_comic(comic_info)
    text = get_comic_info_text(cdb, comic_info, verbose)
    print('[subscribed]  ' + text)


def unsubscribe(cdb, comic_entry, verbose):
    azr, comic_id = get_analyzer_and_comic_id(comic_entry)
    if azr is None:
        return None
    comic_info = cdb.get_comic(comic_id)
    if comic_info is None:
        print('"{}" are not exists.'.format(comic_entry))
        return None
    text = get_comic_info_text(cdb, comic_info, verbose)
    cdb.delete_comic(comic_id)
    comic_dir = pathlib.Path(
        cdb.get_option('output_dir')) / comic_info['title']
    shutil.rmtree(str(comic_dir), ignore_errors=True)
    print('[removed]     ' + text)


def list_info(cdb, verbose):
    all_comics = cdb.get_all_comics()
    for comic_info in all_comics:
        text = get_comic_info_text(cdb, comic_info, verbose)
        print(text)
    print('  ------------------------------------------')
    print('    Total:              {:>4} comics / {:>6} volumes'.format(
        len(all_comics),
        cdb.get_volumes_count(),
        ))
    no_downloaded_volumes = cdb.get_no_downloaded_volumes()
    print('    No Downloaded:      {:>4} comics / {:>6} volumes'.format(
        len(set(v['comic_id'] for v in no_downloaded_volumes)),
        len(no_downloaded_volumes),
        ))
    last_refresh_time = cdb.get_option('last_refresh_time')
    print('    Last refresh:       {}'.format(
        DT.datetime.strftime(last_refresh_time, '%Y-%m-%d %H:%M:%S')))
    print('    Download Directory: "{}"'.format(
        cdb.get_option('output_dir')))
    counter = collections.Counter([
        get_analyzer_by_comic_id(comic_info['comic_id'])
        for comic_info in all_comics])
    print('    Used Analyzers:     {}'.format(
        ', '.join(['{}({}):{}'.format(azr.name(), azr.codename(), count)
                   for azr, count in counter.items()])))


def refresh_all(cdb, verbose):
    que = queue.Queue()

    def get_data_one(comic_info):
        azr = get_analyzer_by_comic_id(comic_info['comic_id'])
        try:
            comic_info = azr.get_comic_info(comic_info['comic_id'])
            que.put(comic_info)
        except:
            print(
                'Error: refresh failed\n  {title} ({url})'.format(
                    url=azr.comic_id_to_url(comic_info['comic_id']),
                    title=comic_info['title']))
            que.put(None)

    def post_process(cdb, length, verbose):
        for index in range(length):
            comic_info = que.get()
            cdb.upsert_comic(comic_info)
            text = ''.join([
                ' {:>5} '.format('{}/{}'.format(index + 1, length)),
                get_comic_info_text(cdb, comic_info, verbose)])
            print(text)
            cdb.set_option('last_refresh_time', DT.datetime.now())

    with CF.ThreadPoolExecutor(
            max_workers=cdb.get_option('threads')) as executor:
        all_comics = cdb.get_all_comics()
        for comic_info in all_comics:
            executor.submit(get_data_one, comic_info)
        post_process(cdb, len(all_comics), verbose)


def download_subscribed(cdb, verbose):
    def download(url, filepath, **kwargs):
        try:
            downloader.save(url, filepath, **kwargs)
            print('OK: "{}"'.format(filepath))
        except downloader.DownloadError:
            pass

    output_dir = cdb.get_option('output_dir')
    threads = cdb.get_option('threads')
    for volume in cdb.get_no_downloaded_volumes():
        volume_dir = pathlib.Path(
            output_dir) / volume['title'] / volume['name']
        os.makedirs(str(volume_dir), exist_ok=True)
        azr = get_analyzer_by_comic_id(volume['comic_id'])
        with CF.ThreadPoolExecutor(max_workers=threads) as executor:
            for data in azr.get_volume_pages(volume['comic_id'],
                                             volume['volume_id'],
                                             volume['extra_data']):
                path = volume_dir / data['local_filename']
                if not (path.exists() and path.stat().st_size):
                    executor.submit(
                        download, filepath=str(path), **data)
        cdb.set_volume_is_downloaded(
            volume['comic_id'], volume['volume_id'], True)


def get_args(cdb):
    def parse_args():
        analyzers_desc_text = '\n'.join([
            '    {}({}) - {}'.format(
                azr.name(), azr.codename(), azr.site())
            for azr in _ANALYZERS])

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Subscribe and download your comic books!\n'
                        '\n'
                        '  Enabled analyzers:\n' + analyzers_desc_text
            )

        parser.add_argument(
            '-s', '--subscribe', metavar='COMIC',
            dest='subscribe_comic_entrys', type=str, nargs='+',
            help='Subscribe some comic books.\n'
                 'COMIC can be a url or comic_id.')

        parser.add_argument(
            '-u', '--unsubscribe', metavar='COMIC',
            dest='unsubscribe_comic_entrys', type=str, nargs='+',
            help='Unsubscribe some comic books.')

        parser.add_argument(
            '-l', '--list-info', dest='list_info',
            action='store_const', const=True, default=False,
            help='List all subscribed books info.')

        parser.add_argument(
            '-r', '--refresh', dest='refresh',
            action='store_const', const=True, default=False,
            help='Update all subscribed comic info.')

        parser.add_argument(
            '-d', '--download', dest='download',
            action='store_const', const=True, default=False,
            help='Download subscribed comic books.')

        parser.add_argument(
            "-v", action="count", dest='verbose',
            default=0, help="Increase output verbosity. E.g., -v, -vvv")

        parser.add_argument(
            '--output-dir', metavar='DIR', dest='output_dir',
            type=str, default=None,
            help='Set download folder.'
                 '\n(Current value: {})'.format(
                     cdb.get_option('output_dir')))

        parser.add_argument(
            '--threads', metavar='NUM', dest='threads',
            type=int, default=None, choices=range(1, 11),
            help='Set download threads count.'
                 '\n(Current value: {})'.format(
                     cdb.get_option('threads')))

        # parser.add_argument(
        #     '--cbz', metavar='BOOLEAN', dest='cbz',
        #     type=bool, default=None,
        #     help='Switch .'
        #          '\n(Current value: {})'.format(cdb.cbz))

        parser.add_argument(
            '--azr', metavar='CODENAME', dest='analyzer_info',
            type=str, default=None,
            choices=[azr.codename() for azr in _ANALYZERS],
            help='Show the analyzer\'s info message.')

        parser.add_argument(
            '--azr-custom', metavar='DATA', dest='analyzer_custom',
            type=str, default=None,
            help='Set analyzer\'s custom data.\n'
                 'Format: "codename/key1=value1,key2=value2"\n'
                 'Check the analyzer\'s help message for more info.')

        parser.add_argument(
            '--version', action='version', version=VERSION)

        args = parser.parse_args()
        return args

    args = parse_args()
    return args


def main():
    cdb = comicdb.ComicDB(dbpath=os.path.expanduser('~/.cmdlr.db'))
    initial_analyzers(cdb)
    args = get_args(cdb)

    if args.analyzer_info:
        for azr in _ANALYZERS:
            if azr.codename() == args.analyzer_info:
                print(textwrap.dedent(azr.info()).strip(' \n'))
                print('  Current Custom Data: {}'.format(
                    get_custom_data_in_cdb(cdb, azr)))
                sys.exit(0)
    if args.analyzer_custom:
        set_custom_data(cdb, args.analyzer_custom)
        sys.exit(0)
    if args.output_dir:
        cdb.set_option('output_dir', args.output_dir)
    if args.threads is not None:
        cdb.set_option('threads', args.threads)
    if args.unsubscribe_comic_entrys:
        for comic_entry in args.unsubscribe_comic_entrys:
            unsubscribe(cdb, comic_entry, args.verbose)
    if args.subscribe_comic_entrys:
        for entry in args.subscribe_comic_entrys:
            subscribe(cdb, entry, args.verbose)
    if args.refresh:
        refresh_all(cdb, args.verbose + 1)
    if args.download:
        download_subscribed(cdb, args.verbose)
    if args.list_info:
        list_info(cdb, args.verbose + 1)


if __name__ == "__main__":
    main()
