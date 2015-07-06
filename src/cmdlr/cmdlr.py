#!/usr/bin/env python3

import urllib.request as UR
import urllib.error as UE
import os
import concurrent.futures as CF
import argparse
import queue

import tinydb
from tinydb import where

from . import eight_comic


VERSION = '1.1.0'


class ComicDB:
    def __init__(self, dbpath=os.path.expanduser('~/.cmdlrdb')):
        self.__db = tinydb.TinyDB(dbpath)
        self.__s_table = self.__db.table('subscribed')
        self.__c_table = self.__db.table('comic_index')

    def print_subscribed_comic_info(self, row):
        if row.get('status') == 'update':
            sign = '!'
        elif row.get('status') == 'new':
            sign = '+'
        else:
            sign = ' '
        info = ('{sign} {comic_id:<10}{title}'
                '  (Volumes: {volume_count})').format(
                    comic_id=row['comic_id'],
                    title=row['title'],
                    volume_count=len(row['volume_codes']),
                    sign=sign,
                    )
        print(info)

    def get_all_subscribed_rows(self):
        return sorted(self.__s_table.all(),
                      key=lambda row: (row['status'], row['title']))

    def list_subscribed_comics(self):
        for row in self.get_all_subscribed_rows():
            self.print_subscribed_comic_info(row)

    def refresh(self):
        def refresh_index():
            self.__c_table.purge()
            comic_index = eight_comic.get_comic_index()
            self.__c_table.insert_multiple(comic_index)
            print("Index rebuild complete. Comics count: {}\n".format(
                len(comic_index)))

        def refresh_subscribed():
            que = queue.Queue()
            length = len(self.__s_table)

            def to_queue(comic_id):
                comic_metadata = eight_comic.get_comic_metadata(comic_id)
                que.put(comic_metadata)

            def from_queue():
                for i in range(length):
                    comic_metadata = que.get()
                    row = self.upsert_subscribed(comic_metadata)
                    self.print_subscribed_comic_info(row)

            print("Update subscribed comics metadata ...\n")
            with CF.ThreadPoolExecutor(max_workers=10) as e:
                for row in self.__s_table.all():
                    e.submit(to_queue, row['comic_id'])
                from_queue()
            print("\nMetadata update complete.")

        refresh_index()
        refresh_subscribed()

    def search(self, query):
        if not len(self.__c_table):
            self.refresh()
        matches = self.__c_table.search(
            where('title').matches(r'.*?{}.*'.format(query)))
        if len(matches):
            # print('Comic ID  Title')
            # print('========= =====================')
            for match in matches:
                print('{comic_id:<10}{title}'.format(**match))

    def upsert_subscribed(self, new_comic_metadata):
        comic_id = new_comic_metadata['comic_id']
        old_meta = self.__s_table.get(
            where('comic_id') == comic_id)
        if old_meta:
            self.__s_table.update(new_comic_metadata, eids=[old_meta.eid])
            old_len = len(old_meta['volume_codes'])
            new_len = len(new_comic_metadata['volume_codes'])
            if old_len < new_len:
                self.__s_table.update({'status': "update"},
                                      eids=[old_meta.eid])
        else:
            self.__s_table.insert(dict(status="new", **new_comic_metadata))
        return self.__s_table.get(where('comic_id') == comic_id)

    def subscribe(self, comic_id):
        comic_metadata = eight_comic.get_comic_metadata(comic_id)
        row = self.upsert_subscribed(comic_metadata)
        self.print_subscribed_comic_info(row)

    def unsubscribe(self, comic_id):
        row = self.__s_table.get(where('comic_id') == comic_id)
        self.print_subscribed_comic_info(row)
        self.__s_table.remove(where('comic_id') == comic_id)

    def download_subscribed(self, output_dir):
        for row in [r for r in self.get_all_subscribed_rows()
                    # if r.get('status')
                    ]:
            comic_download_list = eight_comic.get_comic_download_list(
                row, output_dir)
            with CF.ThreadPoolExecutor(max_workers=10) as e:
                for download_info in comic_download_list:
                    e.submit(download_image, **download_info)
            self.__s_table.update(
                {"status": ""}, where('comic_id') == row['comic_id'])


def download_image(url, save_path):
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        # print('Already Exist: {}'.format(save_path))
        pass
    else:
        dirname = os.path.dirname(save_path)
        os.makedirs(dirname, exist_ok=True)
        while True:
            try:
                response = UR.urlopen(url, timeout=60)
                break
            except UE.HTTPError as err:
                print('Skip {url} ->\n  {save_path}\n  {err}'.format(
                    url=url,
                    save_path=save_path,
                    err=err))
                break
            except UE.URLError as err:
                print('Retry {url} ->\n  {save_path}\n  {err}'.format(
                    url=url,
                    save_path=save_path,
                    err=err))
                continue
        with open(save_path, 'wb') as f:
            f.write(response.read())
        print('OK: {}'.format(save_path))


def get_args():
    def parse_args():
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Download comic books from 8comic!')

        parser.add_argument(
            'query', metavar='QUERY', type=str, nargs='?',
            help='Search index to find the comic_id')

        parser.add_argument(
            '-s', '--subscribe', metavar='Comic_ID',
            dest='subscribe_comic_ids', type=int, nargs='+',
            help='Subscribe some comic book.')

        parser.add_argument(
            '-u', '--unsubscribe', metavar='Comic_ID',
            dest='unsubscribe_comic_ids', type=int, nargs='+',
            help='Unsubscribe some comic book.')

        parser.add_argument(
            '-l', '--list-subscribed', dest='list_subscribed',
            action='store_const', const=True, default=False,
            help='List all subscribed books.')

        parser.add_argument(
            '-r', '--refresh', dest='refresh',
            action='store_const', const=True, default=False,
            help='Refresh index of content and subscribed comic\'s'
                 '\nmetadata.')

        parser.add_argument(
            '-d', '--download', dest='download',
            action='store_const', const=True, default=False,
            help='Download subscribed comic books.')

        parser.add_argument(
            '-o', '--output-dir', metavar='DIR', dest='output_dir', type=str,
            default=os.getcwd(),
            help='Change download folder. default is cwd.'
                 '\n(default: %(default)s)')

        # parser.add_argument(
        #     '--init', dest='init',
        #     action='store_const', const=True, default=False,
        #     help='Clear whole comic book database!')

        parser.add_argument(
            '-v', '--version', action='version', version=VERSION)

        args = parser.parse_args()
        return args

    args = parse_args()
    return args


def main():

    args = get_args()
    cdb = ComicDB()

    if args.query:
        cdb.search(args.query)
    else:
        if args.refresh:
            cdb.refresh()
        # if args.output_dir:
        #     if db.table('settings').contain(
        #             tinydb.where('name') == 'output_dir'):
        #         elem = db.table('settings').get(
        #                 tinydb.where('name') == 'output_dir')
        #         elem['value']
        if args.unsubscribe_comic_ids:
            print('Unsubscribe:')
            for comic_id in args.unsubscribe_comic_ids:
                cdb.unsubscribe(comic_id)
        if args.subscribe_comic_ids:
            for comic_id in args.subscribe_comic_ids:
                cdb.subscribe(comic_id)
        if args.list_subscribed:
            cdb.list_subscribed_comics()
        if args.download:
            cdb.download_subscribed(args.output_dir)
        # if args.init:
        #     cdb.purge_tables()


if __name__ == "__main__":
    main()
