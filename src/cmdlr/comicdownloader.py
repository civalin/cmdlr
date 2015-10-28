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
import textwrap
import shutil
import queue
import collections
import zipfile

from . import downloader
from . import analyzersmanager as AM
from . import comicpath


class ComicDownloader():
    def __init__(self, cdb):
        self.__cdb = cdb
        self.__cpath = comicpath.get_cpath(cdb)
        self.__threads = cdb.get_option('threads')
        self.__cbz = cdb.get_option('cbz')
        self.am = AM.AnalyzersManager(cdb)

    @property
    def cdb(self):
        return self.__cdb

    def get_comic_info_text(self, comic_info, verbose=0):
        def get_data_package(comic_info):
            stat = self.__cdb.get_comic_volumes_status(
                comic_info['comic_id'])
            volumes_infos = stat['volume_infos']
            total = len(volumes_infos)
            data = {
                'comic_id': comic_info['comic_id'],
                'title': self.__cpath.sp.hanziconv(comic_info['title']),
                'desc': self.__cpath.sp.hanziconv(comic_info['desc']),
                'total': total,
                'no_downloaded_count': total - stat['downloaded_count'],
                'downloaded_count': stat['downloaded_count'],
                'gone_count': stat['gone_count'],
                'last_incoming_time': stat['last_incoming_time'],
                'v_infos': volumes_infos,
                }
            return data

        def get_text_string(data, verbose):
            texts = []
            texts.append('{comic_id:<15} {title}')
            if verbose >= 1:
                texts.append(' ({downloaded_count}/{total})')
                if data['no_downloaded_count'] != 0:
                    texts.insert(0, '{no_downloaded_count:<+4} ')
                else:
                    texts.insert(0, '     ')
                if data['gone_count'] != 0:
                    texts.append(' [{gone_count}]')
            text = ''.join(texts).format(**data)
            if verbose >= 2:
                text = '\n'.join([
                    text,
                    textwrap.indent(
                        textwrap.fill('{desc}'.format(**data), 35),
                        '    ')])
                if verbose >=3:
                    texts2 = []
                    for v in data['v_infos']:
                        texts2.append('      - {name} {down} {gone}'.format(
                            name=v['name'],
                            down='' if v['is_downloaded'] else
                                '[no downloaded]',
                            gone='[disappeared]' if v['gone'] else '',
                            ))
                    text2 = '\n'.join(texts2)
                    text = '\n'.join([text, text2])
                text = text + '\n'
            return text

        verbose = verbose % 4
        data = get_data_package(comic_info)
        return get_text_string(data, verbose)

    def get_comic_info(self, comic_entry):
        azr, comic_id = self.am.get_analyzer_and_comic_id(comic_entry)
        if azr is None:
            print('"{}" not fits any analyzers.'.format(comic_entry))
            comic_id = comic_entry
        comic_info = self.__cdb.get_comic(comic_id)
        return comic_info

    def print_comic_info(self, comic_entry, verbose):
        comic_info = self.get_comic_info(comic_entry)
        if comic_info is None:
            print('"{}" are not exists.'.format(comic_entry))
            return None
        text = self.get_comic_info_text(comic_info, verbose)
        print(text)

    def subscribe(self, comic_entry, verbose):
        def try_revive_from_backup(comic_info):
            def merge_dir(root_src_dir, root_dst_dir):
                for src_dir, dirs, files in os.walk(root_src_dir):
                    dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
                    if not os.path.exists(dst_dir):
                        os.makedirs(dst_dir)
                    for file in files:
                        src_file = os.path.join(src_dir, file)
                        dst_file = os.path.join(dst_dir, file)
                        if os.path.exists(dst_file):
                            os.remove(dst_file)
                        shutil.move(src_file, dst_dir)

            backup_comic_dir = self.__cpath.get_backup_comic_dir(
                comic_info)
            comic_dir = self.__cpath.get_comic_dir(comic_info)
            if backup_comic_dir.exists():
                merge_dir(str(backup_comic_dir), str(comic_dir))
                shutil.rmtree(str(backup_comic_dir))

        azr, comic_id = self.am.get_analyzer_and_comic_id(comic_entry)
        if azr is None:
            print('"{}" not fits any analyzers.'.format(comic_entry))
            return None
        comic_info = azr.get_comic_info(comic_id)

        self.__cdb.upsert_comic(comic_info)
        try_revive_from_backup(comic_info)
        text = self.get_comic_info_text(comic_info, verbose)
        print('[SUBSCRIBED]  ' + text)

    def unsubscribe(self, comic_entry, request_backup, verbose):
        def backup_or_remove_data(comic_info, request_backup):
            comic_dir = self.__cpath.get_comic_dir(comic_info)
            if comic_dir.exists():
                if request_backup:
                    os.makedirs(str(self.__cpath.backup_dir),
                                exist_ok=True)
                    backup_comic_dir = self.__cpath.get_backup_comic_dir(
                        comic_info)
                    if backup_comic_dir.exists():
                        os.rmtree(str(backup_comic_dir))
                    shutil.move(str(comic_dir), str(backup_comic_dir))
                else:
                    shutil.rmtree(str(comic_dir), ignore_errors=True)

        def get_info_text(comic_info, request_backup, verbose):
            text = self.get_comic_info_text(comic_info, verbose)
            if request_backup:
                text = '[UNSUB & BAK] ' + text
            else:
                text = '[UNSUB & DEL] ' + text
            return text

        comic_info = self.get_comic_info(comic_entry)
        if comic_info is None:
            print('"{}" are not exists.'.format(comic_entry))
            return None
        text = get_info_text(comic_info, request_backup, verbose)
        backup_or_remove_data(comic_info, request_backup)
        self.__cdb.delete_comic(comic_info['comic_id'])
        print(text)

    def list_info(self, verbose):
        def print_all_comics(all_comics, verbose):
            for comic_info in all_comics:
                text = self.get_comic_info_text(comic_info, verbose)
                print(text)

        def print_total(all_comics):
            print('    Total:              '
                  '{:>4} comics / {:>6} volumes'.format(
                      len(all_comics),
                      self.__cdb.get_volumes_count(),
                      ))

        def print_no_downloaded():
            no_downloaded_volumes = self.__cdb.get_no_downloaded_volumes()
            print('    No Downloaded:      '
                  '{:>4} comics / {:>6} volumes'.format(
                      len(set(v['comic_id'] for v in no_downloaded_volumes)),
                      len(no_downloaded_volumes),
                      ))

        def print_last_refresh():
            last_refresh_time = self.__cdb.get_option('last_refresh_time')
            if type(last_refresh_time) == DT.datetime:
                lrt_str = DT.datetime.strftime(
                    last_refresh_time, '%Y-%m-%d %H:%M:%S')
            else:
                lrt_str = 'none'
            print('    Last refresh:       {}'.format(lrt_str))

        def print_download_directory():
            print('    Download Directory: "{}"'.format(
                self.__cpath.output_dir))

        def print_analyzers_used():
            counter = collections.Counter([
                self.am.get_analyzer_by_comic_id(comic_info['comic_id'])
                for comic_info in all_comics])
            print('    Used Analyzers:     {}'.format(
                ', '.join(['{} ({}): {}'.format(
                    azr.name(), azr.codename(), count)
                           for azr, count in counter.items()
                           if azr is not None])))

        all_comics = self.__cdb.get_all_comics()
        print_all_comics(all_comics, verbose)
        print('  ------------------------------------------')
        print_total(all_comics)
        print_no_downloaded()
        print_last_refresh()
        print_download_directory()
        print_analyzers_used()

    def refresh_all(self, verbose):
        que = queue.Queue()

        def get_data_one(comic_info):
            azr = self.am.get_analyzer_by_comic_id(comic_info['comic_id'])
            if azr is None:
                print(('Skip: Analyzer not exists / disabled ->'
                       ' {title} ({comic_id})').format(**comic_info))
                que.put(None)
                return
            try:
                comic_info = azr.get_comic_info(comic_info['comic_id'])
                que.put(comic_info)
                return
            except:
                print('Skip: Refresh failed -> {title} ({url})'.format(
                    url=azr.comic_id_to_url(comic_info['comic_id']),
                    title=comic_info['title']))
                que.put(None)
                return

        def post_process(length, verbose):
            for index in range(1, length + 1):
                comic_info = que.get()
                if comic_info is None:
                    continue
                else:
                    self.__cdb.upsert_comic(comic_info)
                    text = ''.join([
                        ' {:>5} '.format(
                            '{}/{}'.format(index, length)),
                        self.get_comic_info_text(comic_info, verbose)
                        ])
                    print(text)
            self.__cdb.set_option(
                'last_refresh_time', DT.datetime.now())

        with CF.ThreadPoolExecutor(
                max_workers=self.__threads) as executor:
            all_comics = self.__cdb.get_all_comics()
            for comic_info in all_comics:
                executor.submit(get_data_one, comic_info)
            post_process(len(all_comics), verbose)

    def download_subscribed(self, skip_exists):
        def download_file(url, filepath, **kwargs):
            try:
                downloader.save(url, filepath)
                print('OK: "{}"'.format(filepath))
            except downloader.DownloadError:
                pass

        def convert_cbz_to_dir_if_cbz_exists(cv_info):
            volume_cbz_path = self.__cpath.get_volume_cbz(cv_info, cv_info)
            comic_dir_path = self.__cpath.get_comic_dir(cv_info)
            if not volume_cbz_path.exists():
                return
            else:
                with zipfile.ZipFile(str(volume_cbz_path), 'r') as zfile:
                    zfile.extractall(str(comic_dir_path))
                os.remove(str(volume_cbz_path))

        def convert_to_cbz(cv_info):
            volume_cbz_path = self.__cpath.get_volume_cbz(cv_info, cv_info)
            volume_dir_path = self.__cpath.get_volume_dir(cv_info, cv_info)
            comic_dir_path = self.__cpath.get_comic_dir(cv_info)
            with zipfile.ZipFile(str(volume_cbz_path), 'w') as zfile:
                for path in volume_dir_path.glob('**/*'):
                    in_zip_path = path.relative_to(comic_dir_path)
                    zfile.write(str(path), str(in_zip_path))
            shutil.rmtree(str(volume_dir_path))
            return volume_cbz_path

        def volume_process(cv_info, skip_exists):
            def page_process(executor, page_info, skip_exists):
                pagepath = self.__cpath.get_page_path(
                    cv_info, cv_info, page_info)
                if skip_exists and pagepath.exists():
                    return
                else:
                    executor.submit(download_file,
                                    page_info['url'],
                                    filepath=str(pagepath))

            def download_volume(cv_info, azr):
                with CF.ThreadPoolExecutor(
                        max_workers=self.__threads) as executor:
                    for page_info in azr.get_volume_pages(
                            cv_info['comic_id'],
                            cv_info['volume_id'],
                            cv_info['extra_data']):
                        page_process(executor, page_info, skip_exists)

                self.__cdb.set_volume_is_downloaded(
                    cv_info['comic_id'], cv_info['volume_id'], True)

            azr = self.am.get_analyzer_by_comic_id(cv_info['comic_id'])
            if azr is None:
                print(('Skip: Analyzer not exists / disabled -> '
                       '{title} ({comic_id}): {name}').format(**cv_info))
                return

            volume_dir = self.__cpath.get_volume_dir(cv_info, cv_info)
            os.makedirs(str(volume_dir), exist_ok=True)
            convert_cbz_to_dir_if_cbz_exists(cv_info)
            download_volume(cv_info, azr)
            if self.__cbz:
                cbz_path = convert_to_cbz(cv_info)
                print('## Archived: "{}"'.format(cbz_path))

        for cv_info in self.__cdb.get_no_downloaded_volumes():
            volume_process(cv_info, skip_exists)

    def as_new(self, comic_entry, verbose):
        azr, comic_id = self.am.get_analyzer_and_comic_id(comic_entry)
        if azr is None:
            print('"{}" not fits any analyzers.'.format(comic_entry))
            return None
        comic_info = self.__cdb.get_comic(comic_id)
        if comic_info is None:
            print('"{}" are not exists.'.format(comic_entry))
            return None

        self.__cdb.set_all_volumes_no_downloaded(comic_id)
        text = self.get_comic_info_text(comic_info, verbose)
        print('[AS NEW]     ' + text)

    def move_cpath(self, dst_cpath):
        def move_path(src, dst):
            if not dst.parent.exists():
                dst.parent.mkdir(parents=True)
            try:
                src.replace(dst)
            except:
                src.rmdir()

        def move_output_dir(src_cpath, dst_cpath):
            if src_cpath.output_dir.exists():
                for src_path in sorted(
                        src_cpath.output_dir.glob('**/*'), reverse=True):
                    relative_src_path = src_path.relative_to(
                        src_cpath.output_dir)
                    relative_dst_path_str = dst_cpath.sp.path_modified(
                        str(relative_src_path))
                    dst_path = dst_cpath.output_dir / relative_dst_path_str
                    move_path(src_path, dst_path)
                try:
                    src_cpath.output_dir.rmdir()
                except OSError:
                    pass

        def move_backup_dir(src_cpath, dst_cpath):
            if src_cpath.backup_dir.exists():
                for src_path in sorted(
                        src_cpath.backup_dir.glob('**/*'), reverse=True):
                    relative_src_path = src_path.relative_to(
                        src_cpath.backup_dir)
                    relative_dst_path_str = dst_cpath.sp.path_modified(
                        str(relative_src_path))
                    dst_path = dst_cpath.backup_dir / relative_dst_path_str
                    move_path(src_path, dst_path)
                try:
                    src_cpath.backup_dir.rmdir()
                except OSError:
                    pass

        src_cpath = self.__cpath
        move_output_dir(src_cpath, dst_cpath)
        move_backup_dir(src_cpath, dst_cpath)
        self.__cpath = dst_cpath
