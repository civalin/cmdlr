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
import argparse
import textwrap
import shutil
import queue
import collections
import zipfile

from . import comicdb
from . import downloader
from . import azrmanager as azrm
from . import comicpath

VERSION = '2.0.0'
DBPATH = '~/.cmdlr.db'


def get_comic_info_text(cdb, comic_info, verbose=0):
    verbose = verbose % 4

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
            'last_incoming_time': volumes_status['last_incoming_time'],
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
    cpath = comicpath.get_cpath(cdb)

    def try_revive_from_backup(comic_info):
        def merge_dir(root_src_dir, root_dst_dir):
            for src_dir, dirs, files in os.walk(root_src_dir):
                dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
                if not os.path.exists(dst_dir):
                    os.mkdir(dst_dir)
                for file in files:
                    src_file = os.path.join(src_dir, file)
                    dst_file = os.path.join(dst_dir, file)
                    if os.path.exists(dst_file):
                        os.remove(dst_file)
                    shutil.move(src_file, dst_dir)

        if cpath.backup_dir is not None:
            backup_comic_dir = cpath.get_backup_comic_dir(comic_info)
            comic_dir = cpath.get_comic_dir(comic_info)
            if backup_comic_dir.exists():
                merge_dir(str(backup_comic_dir), str(comic_dir))
                shutil.rmtree(str(backup_comic_dir))

    azr, comic_id = azrm.get_analyzer_and_comic_id(comic_entry)
    if azr is None:
        return None

    comic_info = azr.get_comic_info(comic_id)
    cdb.upsert_comic(comic_info)
    try_revive_from_backup(comic_info)
    text = get_comic_info_text(cdb, comic_info, verbose)
    print('[SUBSCRIBED]  ' + text)


def unsubscribe(cdb, comic_entry, verbose):
    cpath = comicpath.get_cpath(cdb)

    def backup_or_remove_data(cdb, comic_info):
        comic_dir = cpath.get_comic_dir(comic_info)
        if comic_dir.exists():
            if cpath.backup_dir is None:
                shutil.rmtree(str(comic_dir), ignore_errors=True)
            else:
                os.makedirs(str(cpath.backup_dir), exist_ok=True)
                backup_comic_dir = cpath.get_backup_comic_dir(comic_info)
                if backup_comic_dir.exists():
                    os.rmtree(str(backup_comic_dir))
                shutil.move(str(comic_dir), str(backup_comic_dir))

    azr, comic_id = azrm.get_analyzer_and_comic_id(comic_entry)
    if azr is None:
        comic_id = comic_entry
    comic_info = cdb.get_comic(comic_id)
    if comic_info is None:
        print('"{}" are not exists.'.format(comic_entry))
        return None

    text = get_comic_info_text(cdb, comic_info, verbose)
    backup_or_remove_data(cdb, comic_info)
    cdb.delete_comic(comic_id)
    print('[DELETED]     ' + text)


def list_info(cdb, verbose):
    cpath = comicpath.get_cpath(cdb)

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
    if last_refresh_time:
        lrt_str = DT.datetime.strftime(
            last_refresh_time, '%Y-%m-%d %H:%M:%S')
    else:
        lrt_str = None
    print('    Last refresh:       {}'.format(lrt_str))
    print('    Download Directory: "{}"'.format(cpath.output_dir))
    counter = collections.Counter([
        azrm.get_analyzer_by_comic_id(comic_info['comic_id'])
        for comic_info in all_comics])
    print('    Used Analyzers:     {}'.format(
        ', '.join(['{} ({}): {}'.format(
            azr.name(), azr.codename(), count)
                   for azr, count in counter.items()
                   if azr is not None])))


def refresh_all(cdb, verbose):
    que = queue.Queue()

    def get_data_one(comic_info):
        azr = azrm.get_analyzer_by_comic_id(comic_info['comic_id'])
        if azr is None:
            print(('Skip: Analyzer not exists -> {title} ({comic_id})'
                   ).format(**comic_info))
            que.put(None)
            return
        try:
            comic_info = azr.get_comic_info(comic_info['comic_id'])
            que.put(comic_info)
            return
        except:
            print(
                'Skip: refresh failed -> {title} ({url})'.format(
                    url=azr.comic_id_to_url(comic_info['comic_id']),
                    title=comic_info['title']))
            que.put(None)
            return

    def post_process(cdb, length, verbose):
        for index in range(length):
            comic_info = que.get()
            if comic_info is None:
                continue
            else:
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


def download_subscribed(cdb, skip_exists, verbose):
    cpath = comicpath.get_cpath(cdb)

    def download(url, filepath, **kwargs):
        try:
            downloader.save(url, filepath)
            print('OK: "{}"'.format(filepath))
        except downloader.DownloadError:
            pass

    def convert_cbz_to_dir_if_cbz_exists(cv_info):
        volume_cbz_path = cpath.get_volume_cbz(cv_info, cv_info)
        comic_dir_path = cpath.get_comic_dir(cv_info)
        if not volume_cbz_path.exists():
            return
        else:
            with zipfile.ZipFile(str(volume_cbz_path), 'r') as zfile:
                zfile.extractall(str(comic_dir_path))
            os.remove(str(volume_cbz_path))

    def convert_to_cbz(cv_info):
        volume_cbz_path = cpath.get_volume_cbz(cv_info, cv_info)
        volume_dir_path = cpath.get_volume_dir(cv_info, cv_info)
        comic_dir_path = cpath.get_comic_dir(cv_info)
        with zipfile.ZipFile(str(volume_cbz_path), 'w') as zfile:
            for path in volume_dir_path.glob('**/*'):
                in_zip_path = path.relative_to(comic_dir_path)
                zfile.write(str(path), str(in_zip_path))
        shutil.rmtree(str(volume_dir_path))
        return volume_cbz_path

    threads = cdb.get_option('threads')
    cbz = cdb.get_option('cbz')

    for cv_info in cdb.get_no_downloaded_volumes():
        azr = azrm.get_analyzer_by_comic_id(cv_info['comic_id'])
        if azr is None:
            print(('Skip: Analyzer not exists -> '
                   '{title} ({comic_id}): {name}').format(**cv_info))
            continue
        volume_dir = cpath.get_volume_dir(cv_info, cv_info)
        os.makedirs(str(volume_dir), exist_ok=True)
        convert_cbz_to_dir_if_cbz_exists(cv_info)
        with CF.ThreadPoolExecutor(max_workers=threads) as executor:
            for pagedata in azr.get_volume_pages(cv_info['comic_id'],
                                                 cv_info['volume_id'],
                                                 cv_info['extra_data']):
                pagepath = cpath.get_page_path(cv_info, cv_info, pagedata)
                if skip_exists and pagepath.exists():
                    continue
                else:
                    executor.submit(
                        download, pagedata['url'], filepath=str(pagepath))
        cdb.set_volume_is_downloaded(
            cv_info['comic_id'], cv_info['volume_id'], True)
        if cbz:
            cbz_path = convert_to_cbz(cv_info)
            print('## Archived: "{}"'.format(cbz_path))


def as_new(cdb, comic_entry, verbose):
    azr, comic_id = azrm.get_analyzer_and_comic_id(comic_entry)
    if azr is None:
        return None
    comic_info = cdb.get_comic(comic_id)
    if comic_info is None:
        print('"{}" are not exists.'.format(comic_entry))
        return None
    cdb.set_all_volumes_no_downloaded(comic_id)
    text = get_comic_info_text(cdb, comic_info, verbose)
    print('[AS NEW]     ' + text)


def print_analyzer_info(cdb, codename):
    for azr in azrm.get_all_analyzers():
        if azr.codename() == codename:
            print(textwrap.dedent(azr.info()).strip(' \n'))
            print('  Current Custom Data: {}'.format(
                azrm.get_custom_data_in_cdb(cdb, azr)))


def get_args(cdb):
    def parse_args():
        cpath = comicpath.get_cpath(cdb)

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Subscribe and download your comic books!')

        parser.add_argument(
            "-v", action="count", dest='verbose', default=0,
            help="Change output verbosity. E.g., -v, -vvv")

        parser.add_argument(
            '--version', action='version', version=VERSION)

        analyzers_desc_text = '\n'.join([
            '    {} ({})   - {}'.format(
                azr.name(), azr.codename(), azr.site())
            for azr in azrm.get_all_analyzers()])

        azg = parser.add_argument_group(
            'Analyzers Management',
            '\n## Current enabled analyzers ##\n' + analyzers_desc_text)

        azg.add_argument(
            '--azr', metavar='CODENAME', dest='analyzer_info',
            type=str, default=None,
            choices=[azr.codename() for azr in azrm.get_all_analyzers()],
            help='Show the analyzer\'s info message.')

        azg.add_argument(
            '--azr-custom', metavar='DATA', dest='analyzer_custom',
            type=str, default=None,
            help='Set analyzer\'s custom data.\n'
                 'Format: "codename/key1=value1,key2=value2"\n'
                 'Check analyzer\'s info message for more detail.')

        smg = parser.add_argument_group('Subscription Management')

        smg.add_argument(
            '-s', '--subscribe', metavar='COMIC',
            dest='subscribe_comic_entrys', type=str, nargs='+',
            help='Subscribe some comic books.\n'
                 'COMIC can be a url or comic_id.')

        smg.add_argument(
            '-u', '--unsubscribe', metavar='COMIC',
            dest='unsubscribe_comic_entrys', type=str, nargs='+',
            help='Unsubscribe some comic books.\n'
                 'It will *DELETE* all files about this comic.')

        smg.add_argument(
            '-l', '--list-info', dest='list_info', action='store_true',
            help='List all subscribed books info.')

        smg.add_argument(
            '-r', '--refresh', dest='refresh', action='store_true',
            help='Update all subscribed comic info.')

        smg.add_argument(
            '--as-new', metavar='COMIC',
            dest='as_new_comics', type=str, nargs='+',
            help='Set all volumes to "no downloaded" status.\n')

        downloading_group = parser.add_argument_group('Downloading')

        downloading_group.add_argument(
            '-d', '--download', dest='download', action='store_true',
            help='Download all no downloaded volumes.')

        downloading_group.add_argument(
            '--skip-exists', dest='skip_exists', action='store_true',
            help='Do not re-download when localfile exists.\n'
                 'Must use with "-d" option.')

        options_setting_group = parser.add_argument_group('Options Setting')

        options_setting_group.add_argument(
            '--output-dir', metavar='DIR', dest='output_dir', type=str,
            help='Set comics directory.\n'
                 '(= "{}")'.format(cpath.output_dir))

        if cpath.backup_dir is None:
            backup_dir_str = 'None'
        else:
            backup_dir_str = '"{}"'.format(cpath.backup_dir)

        options_setting_group.add_argument(
            '--backup-dir', metavar='DIR', dest='backup_dir', type=str,
            nargs='?', default=False,  # False == Not
            help='Set comics backup directory. Unsubscribed comics will\n'
                 'be moved in here. If blank (None) unsubscribed\n'
                 'comics will be *DELETE* forever.\n'
                 '(= {})'.format(backup_dir_str))

        options_setting_group.add_argument(
            '--threads', metavar='NUM', dest='threads', type=int,
            choices=range(1, 11),
            help='Set download threads count. (= {})'.format(
                 cdb.get_option('threads')))

        options_setting_group.add_argument(
            '--cbz', dest='cbz', action='store_true',
            help='Toggle new incoming volumes to cbz format.'
                 ' (= {})'.format(cdb.get_option('cbz')))

        args = parser.parse_args()
        return args

    args = parse_args()
    return args


def main():
    cdb = comicdb.ComicDB(dbpath=os.path.expanduser(DBPATH))
    azrm.initial_analyzers(cdb)
    args = get_args(cdb)

    if args.analyzer_info:
        print_analyzer_info(cdb, args.analyzer_info)
    if args.analyzer_custom:
        azrm.set_custom_data(cdb, args.analyzer_custom)
    if args.output_dir is not None:
        cdb.set_option('output_dir', args.output_dir)
        print('Output directory: {}'.format(
            cdb.get_option('output_dir')))
    if args.backup_dir is not False:  # False == Not set, None == blank
        cdb.set_option('backup_dir', args.backup_dir)
        print('Backup directory: {}'.format(
            cdb.get_option('backup_dir')))
    if args.threads is not None:
        cdb.set_option('threads', args.threads)
        print('Thread count: {}'.format(cdb.get_option('thread')))
    if args.cbz:
        cdb.set_option('cbz', not cdb.get_option('cbz'))
        print('Cbz mode: {}'.format(cdb.get_option('cbz')))
    if args.as_new_comics:
        for comic_entry in args.as_new_comics:
            as_new(cdb, comic_entry, args.verbose)
    if args.unsubscribe_comic_entrys:
        for comic_entry in args.unsubscribe_comic_entrys:
            unsubscribe(cdb, comic_entry, args.verbose)
    if args.subscribe_comic_entrys:
        for entry in args.subscribe_comic_entrys:
            subscribe(cdb, entry, args.verbose)
    if args.refresh:
        refresh_all(cdb, args.verbose + 1)
    if args.download:
        download_subscribed(cdb, args.skip_exists, args.verbose)
    elif args.skip_exists:
        print('Warning: The "--skip-exists" only work with "--download".')
    if args.list_info:
        list_info(cdb, args.verbose + 1)


if __name__ == "__main__":
    main()
