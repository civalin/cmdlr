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

from . import stringprocess as SP


class ComicDBException(Exception):
    pass


class TitleConflictError(ComicDBException):
    pass


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
                    'title TEXT NOT NULL UNIQUE,'     # e.g., 海賊王
                    'desc TEXT NOT NULL,'             # e.g., 關於海賊的漫畫
                    'extra_data DICT'    # extra data package
                    ');'
                )
                self.conn.execute(
                    'CREATE TABLE volumes ('
                    'comic_id TEXT REFERENCES comics(comic_id)'
                    '  ON DELETE CASCADE,'
                    'volume_id TEXT NOT NULL,'      # vol NO. e.g., 15
                    'name TEXT NOT NULL,'           # vol name. e.g., 第15回
                    'created_time DATETIME NOT NULL,'
                    'is_downloaded BOOLEAN NOT NULL DEFAULT 0,'
                    'gone BOOLEAN NOT NULL DEFAULT 0'  # disappear in site
                    ');'
                )
                self.conn.execute(
                    'CREATE TABLE options ('
                    'option TEXT PRIMARY KEY NOT NULL,'
                    'value BLOB'
                    ');'
                )
                self.set_option(
                    'output_dir',
                    os.path.join(os.path.expanduser('~'), 'comics'))
                self.set_option(
                    'backup_dir',
                    os.path.join(os.path.expanduser('~'), 'comics_backup'))
                self.set_option('last_refresh_time', 'none')
                self.set_option('threads', 2)
                self.set_option('cbz', False)
                self.set_option('hanzi_mode', 'trad')
                self.set_option('analyzers_custom_data', {})
                self.set_option('analyzers_black_list', set())
                set_db_version(1)

            db_version = get_db_version()

            if db_version == 0:
                from0to1()

            self.conn.commit()

        def connection_setting():
            sp = SP.StringProcess(hanzi_mode='trad')

            def is_same_string(str1, str2):
                if (sp.component_modified(str1.lower()) ==
                        sp.component_modified(str2.lower())):
                    return True
                else:
                    return False

            def is_partof_string(sub_str, whole_str):
                if (sp.component_modified(sub_str.lower()) in
                        sp.component_modified(whole_str.lower())):
                    return True
                else:
                    return False

            self.conn.row_factory = sqlite3.Row
            self.conn.execute('PRAGMA foreign_keys = ON;')
            self.conn.create_function(
                'is_same_string', 2, is_same_string)
            self.conn.create_function(
                'is_partof_string', 2, is_partof_string)

        self.conn = sqlite3.connect(dbpath,
                                    detect_types=sqlite3.PARSE_DECLTYPES)
        connection_setting()
        migrate()

    def get_option(self, option, default=None):
        '''
            return the option value
        '''
        data = self.conn.execute(
                'SELECT "value" FROM "options" where option = :option',
                {'option': option}).fetchone()
        if data:
            return pickle.loads(data['value'])
        else:
            return default

    def set_option(self, option, value):
        '''
            set the option value, the value must be str or None.
        '''
        data = {'value': pickle.dumps(value), 'option': option}
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

    def upsert_comic(self, comic_info):
        '''
            Update or insert comic_info from ComicAnalyzer.
            Please refer the ComicAnalyzer to check the data format.

            This function will also maintain the volumes table.
        '''
        def upsert_volume(comic_id, volume):
            now = DT.datetime.now()
            data = {
                    'comic_id': comic_id,
                    'volume_id': volume['volume_id'],
                    'created_time': now,
                    'name': volume['name'],
                }
            volume_count = self.conn.execute(  # check already exists
                'SELECT COUNT(*) FROM volumes'
                ' WHERE comic_id = :comic_id AND'
                '       volume_id = :volume_id', data).fetchone()[0]
            if volume_count == 0:
                self.conn.execute(
                    'INSERT INTO volumes'
                    ' (comic_id, volume_id, name, created_time)'
                    ' VALUES ('
                    ' :comic_id,'
                    ' :volume_id,'
                    ' :name,'
                    ' :created_time'
                    ' )', data)
            else:
                self.conn.execute(
                    'UPDATE volumes SET'
                    ' gone = 0'
                    ' WHERE comic_id = :comic_id AND'
                    '       volume_id = :volume_id',
                    data)

        def upsert_comic(comic_info):
            cursor = self.conn.execute(
                'UPDATE comics SET'
                ' desc = :desc,'
                ' extra_data = :extra_data'
                ' WHERE comic_id = :comic_id', comic_info)
            if cursor.rowcount == 0:
                title_conflict_count = self.conn.execute(
                    'SELECT COUNT(title) FROM comics'
                    ' WHERE is_same_string(comics.title, :title)',
                    comic_info).fetchone()[0]
                if title_conflict_count == 0:
                    self.conn.execute(
                        'INSERT INTO comics'
                        ' (comic_id, title, desc, extra_data)'
                        ' VALUES ('
                        ' :comic_id,'
                        ' :title,'
                        ' :desc,'
                        ' :extra_data'
                        ' )', comic_info)
                else:
                    raise TitleConflictError

        def mark_disappear_volume(comic_info):
            volume_ids_text = ', '.join(
                ['"' + v['volume_id'] + '"'
                    for v in comic_info['volumes']])
            query = ('UPDATE volumes SET'
                     ' gone = 1'
                     ' WHERE comic_id = :comic_id AND'
                     '       volume_id not in ({})').format(volume_ids_text)
            self.conn.execute(query, comic_info)

        upsert_comic(comic_info)
        for volume in comic_info['volumes']:
            upsert_volume(comic_info['comic_id'], volume)
        mark_disappear_volume(comic_info)

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

    def set_all_volumes_no_downloaded(self, comic_id):
        self.conn.execute(('UPDATE volumes SET is_downloaded = 0'
                           ' WHERE comic_id = :comic_id'),
                          {'comic_id': comic_id})
        self.conn.commit()

    def get_no_downloaded_volumes(self):
        return self.conn.execute(
            'SELECT * FROM comics INNER JOIN volumes'
            ' ON comics.comic_id = volumes.comic_id'
            ' WHERE volumes.is_downloaded = 0 AND'
            '       volumes.gone = 0'
            ' ORDER BY comics.title ASC,'
            '          comics.comic_id ASC,'
            '          volumes.name ASC').fetchall()

    def get_all_comics(self):
        return [self.get_comic(row['comic_id'])
                for row in self.get_all_comic_ids()]

    def get_all_comic_ids(self):
        return self.conn.execute(
            'SELECT comics.comic_id FROM comics JOIN volumes'
            ' ON comics.comic_id = volumes.comic_id'
            ' GROUP BY comics.comic_id'
            ' ORDER BY min(volumes.is_downloaded) DESC,'
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

    def search_comic(self, keyword):
        results = self.conn.execute(
            'SELECT comic_id from comics'
            ' WHERE is_partof_string(:keyword, title)'
            ' ORDER BY comics.title ASC,'
            '          comics.comic_id ASC',
            {'keyword': keyword}).fetchall()
        comic_ids = [result['comic_id'] for result in results]
        return comic_ids

    def get_comic_volumes_status(self, comic_id):
        '''
            For UI display.
        '''
        volume_infos = self.conn.execute(
            'SELECT * FROM volumes'
            ' WHERE comic_id = :comic_id',
            {'comic_id': comic_id}).fetchall()
        if len(volume_infos):
            last_incoming_time = max(v['created_time'] for v in volume_infos)
        else:
            last_incoming_time = None
        data = {
            'last_incoming_time': last_incoming_time,
            'volume_infos': volume_infos,
            'downloaded_count': 0,
            'gone_count': 0,
            }
        for volume_info in volume_infos:
            if volume_info['is_downloaded']:
                data['downloaded_count'] = data['downloaded_count'] + 1
            if volume_info['gone']:
                data['gone_count'] = data['gone_count'] + 1

        return data
