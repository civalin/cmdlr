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

import sqlite3
import os
import datetime as DT
import pickle


_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def extend_sqlite3_datatype():
    sqlite3.register_adapter(DT.datetime, pickle.dumps)
    sqlite3.register_converter('DATETIME', pickle.loads)
    sqlite3.register_adapter(dict, pickle.dumps)
    sqlite3.register_converter('DICT', pickle.loads)


extend_sqlite3_datatype()


class ComicDB():
    def __init__(self, dbpath):
        def migrate():
            def get_db_version():
                return self.conn.execute(
                    'PRAGMA user_version;').fetchone()['user_version']

            def set_db_version(version):
                self.conn.execute('PRAGMA user_version = {};'.format(
                    int(version)))

            def from0to1():
                self.conn.execute(
                    'CREATE TABLE comics ('           # 已訂閱的漫畫
                    'comic_id TEXT PRIMARY KEY NOT NULL,'  # e.g., xx123
                    'title TEXT NOT NULL,'            # e.g., 海賊王
                    'desc TEXT NOT NULL,'             # e.g., 關於海賊的漫畫
                    'created_time DATETIME NOT NULL,'
                    'extra_data DICT'    # extra data package
                    ');'
                )
                self.conn.execute(
                    'CREATE TABLE volumes ('
                    'comic_id TEXT REFERENCES comics(comic_id)'
                    '  ON DELETE CASCADE,'
                    'volume_id TEXT NOT NULL,'      # vol NO. e.g., 15
                    'name TEXT NOT NULL,'           # vol name. e.g., 第15回
                    'is_downloaded BOOLEAN NOT NULL DEFAULT 0'
                    ');'
                )
                self.conn.execute(
                    'CREATE TABLE options ('
                    'option TEXT PRIMARY KEY NOT NULL,'
                    'value TEXT'
                    ');'
                )
                self.__set_option(
                    'output_dir', os.path.expanduser('~/comics'))
                self.__set_option('last_refresh_time', None)
                self.__set_option('threads', str(2))
                set_db_version(1)

            db_version = get_db_version()

            if db_version == 0:
                from0to1()

            self.conn.commit()

        self.conn = sqlite3.connect(dbpath,
                                    detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON;')
        migrate()

    def __get_option(self, option):
        '''
            return the option value
        '''
        return self.conn.execute(
            'SELECT "value" FROM "options" where option = :option',
            {'option': option}).fetchone()['value']

    def __set_option(self, option, value):
        '''
            set the option value, the value must be str or None.
        '''
        data = {'value': value, 'option': option}
        cursor = self.conn.execute(
            'UPDATE "options" SET "value" = :value'
            ' WHERE "option" = :option',
            data)
        if cursor.rowcount == 0:
            self.conn.execute(
                'INSERT INTO "options"'
                ' (option, value)'
                ' VALUES (:option, :value)',
                data)
        self.conn.commit()

    @property
    def output_dir(self):
        return self.__get_option('output_dir')

    @output_dir.setter
    def output_dir(self, output_dir):
        self.__set_option('output_dir', output_dir)

    @property
    def last_refresh_time(self):
        '''
            Record last refresh time.
            return:
                None or datetime format
        '''
        lrt_strformat = self.__get_option('last_refresh_time')
        if lrt_strformat is None:
            return None
        else:
            last_refresh_time = DT.datetime.strptime(
                lrt_strformat, _DATETIME_FORMAT)
            return last_refresh_time

    @last_refresh_time.setter
    def last_refresh_time(self, last_refresh_time):
        '''
            args:
                last_refresh_time:
                    must be datetime format
        '''
        if last_refresh_time is None:
            self.__set_option(None)
        else:
            lrt_strformat = DT.datetime.strftime(
                last_refresh_time, '%Y-%m-%dT%H:%M:%S')
            self.__set_option('last_refresh_time', lrt_strformat)

    @property
    def threads(self):
        return int(self.__get_option('threads'))

    @threads.setter
    def threads(self, threads):
        self.__set_option(str(threads))

    def upsert_comic(self, comic_info):
        '''
            Update or insert comic_info from ComicAnalyzer.
            Please refer the ComicAnalyzer to check the data format.

            This function will also maintain the volumes table.
        '''
        def upsert_volume(volume):
            cursor = self.conn.execute(
                'UPDATE volumes SET'
                ' name = name'
                ' WHERE comic_id = :comic_id AND'
                '       volume_id = :volume_id',
                {
                    'comic_id': comic_info['comic_id'],
                    'volume_id': volume['volume_id'],
                    'name': volume['name'],
                }
            )
            if cursor.rowcount == 0:
                self.conn.execute(
                    'INSERT INTO volumes'
                    ' (comic_id, volume_id, name)'
                    ' VALUES ('
                    ' :comic_id,'
                    ' :volume_id,'
                    ' :name'
                    ' )',
                    {
                        'comic_id': comic_info['comic_id'],
                        'volume_id': volume['volume_id'],
                        'name': volume['name'],
                    }
                )

        now = DT.datetime.now()
        cursor = self.conn.execute(
            'UPDATE comics SET'
            ' desc = :desc,'
            ' title = :title,'
            ' created_time = :created_time,'
            ' extra_data = :extra_data'
            ' WHERE comic_id = :comic_id',
            {
                'comic_id': comic_info['comic_id'],
                'title': comic_info['title'],
                'desc': comic_info['desc'],
                'created_time': now,
                'extra_data': comic_info['extra_data'],
            })
        if cursor.rowcount == 0:
            self.conn.execute(
                'INSERT INTO comics'
                ' (comic_id, title, desc, created_time, extra_data)'
                ' VALUES ('
                ' :comic_id,'
                ' :title,'
                ' :desc,'
                ' :created_time,'
                ' :extra_data'
                ' )',
                {
                    'comic_id': comic_info['comic_id'],
                    'title': comic_info['title'],
                    'desc': comic_info['desc'],
                    'created_time': now,
                    'extra_data': comic_info['extra_data'],
                })

        for volume in comic_info['volumes']:
            upsert_volume(volume)

        self.conn.commit()

    def delete_comic(self, comic_id):
        self.conn.execute(
            'DELETE FROM comics where comic_id = :comic_id',
            {'comic_id': comic_id})
        self.conn.commit()

    def set_volume_is_downloaded(
            self, comic_id, volume_id, is_downloaded=True):
        '''
            change volume downloaded status
        '''
        self.conn.execute(
            'UPDATE volumes'
            ' SET is_downloaded = :is_downloaded'
            ' WHERE comic_id = :comic_id AND volume_id = :volume_id',
            {
                'comic_id': comic_id,
                'volume_id': volume_id,
                'is_downloaded': is_downloaded,
            })
        self.conn.commit()

    def set_all_volumes_is_not_downloaded(self):
        '''
            Set is_downloaded of all volumes to False.
        '''
        self.conn.execute('UPDATE volumes SET is_downloaded = 0')
        self.conn.commit()

    def get_not_downloaded_volumes(self):
        return self.conn.execute(
            'SELECT * FROM comics INNER JOIN volumes'
            ' ON comics.comic_id = volumes.comic_id'
            ' WHERE volumes.is_downloaded = 0'
            ' ORDER BY comic_id').fetchall()

    def get_all_comics(self):
        return self.conn.execute(
            'SELECT comics.* FROM comics JOIN volumes'
            ' ON comics.comic_id = volumes.comic_id'
            ' GROUP BY comics.comic_id'
            ' ORDER BY volumes.is_downloaded DESC,'
            '          comics.title ASC,'
            '          comics.comic_id ASC').fetchall()

    def get_volumes_count(self):
        return self.conn.execute(
            'SELECT COUNT(*) FROM volumes'
                ).fetchone()[0]

    def get_comic(self, comic_id):
        return self.conn.execute(
            'SELECT * FROM comics'
            ' WHERE comic_id = :comic_id',
            {'comic_id': comic_id}).fetchone()

    def get_comic_volumes_status(self, comic_id):
        '''
            Use for UI display.
        '''
        volumes = self.conn.execute(
            'SELECT * FROM volumes'
            ' WHERE comic_id = :comic_id',
            {'comic_id': comic_id}).fetchall()
        data = {
            'total': len(volumes),
            'downloaded_count': 0,
            'no_downloaded_count': 0,
            'no_downloaded_names': [],
            }
        for volume in volumes:
            if(volume['is_downloaded']):
                data['downloaded_count'] = data['downloaded_count'] + 1
            else:
                data['no_downloaded_count'] = data['no_downloaded_count'] + 1
                data['no_downloaded_names'].append(volume['name'])

        return data
