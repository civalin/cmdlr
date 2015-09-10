import sqlite3
import os
import datetime as DT
import pickle


def extend_sqlite3_datatype():
    sqlite3.register_adapter(DT.datetime, pickle.dumps)
    sqlite3.register_converter('DATETIME', pickle.loads)


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
                    ');'
                )
                self.conn.execute(
                    'CREATE TABLE volumes ('
                    'comic_id TEXT REFERENCES comics(comic_id)'
                    '  ON DELETE CASCADE,'
                    'volume_id INTEGER NOT NULL,'      # vol NO. e.g., 15
                    'name TEXT NOT NULL,'              # vol name. e.g., 第15回
                    'is_downloaded BOOLEAN NOT NULL DEFAULT 0,'
                    ');'
                )
                self.conn.execute(
                    'CREATE TABLE metadata ('
                    'output_dir TEXT NOT NULL,'
                    'last_refresh_time DATETIME,'
                    ');'
                )
                set_db_version(1)

            db_version = get_db_version()

            if db_version == 0:
                from0to1()

            self.conn.commit()

        def metadata_init():
            def is_metadata_row_exists():
                exist = self.conn.execute(
                    'SELECT COUNT(*) FROM "metadata"').fetchone()[0]
                return bool(exist)

            def insert_default_metadata():
                default_output_dir = os.path.expanduser('~/comics')
                self.conn.execute(
                    'INSERT INTO "metadata" ("output_dir")'
                    'VALUES (:output_dir)',
                    {'output_dir': default_output_dir}
                )

            if not is_metadata_row_exists():
                insert_default_metadata()

        self.conn = sqlite3.connect(dbpath,
                                    detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON;')
        self.migrate()
        self.__metadata_init()

    @property
    def output_dir(self):
        return self.conn.execute(
            'SELECT "output_dir" FROM "metadata"').fetchone()['output_dir']

    @output_dir.setter
    def output_dir(self, output_dir):
        self.conn.execute(
            'UPDATE "metadata" SET "output_dir" = :output_dir',
            {'output_dir': output_dir})

    @property
    def last_refresh_time(self):
        return self.conn.execute('SELECT "last_refresh_time" FROM "metadata"'
                                 ).fetchone()['last_refresh_time']

    @last_refresh_time.setter
    def last_refresh_time(self, last_refresh_time):
        self.conn.execute(
            'UPDATE "metadata" SET "last_refresh_time" = :last_refresh_time',
            {'last_refresh_time': last_refresh_time})

    def upsert_comic(self, comic_info):
        '''
            Update or insert comic_info from ComicAnalyzer.
            Please refer the ComicAnalyzer to check the data format.

            This function will also maintain the volumes table.
        '''
        def upsert_volume(volume):
            self.conn.execute(
                'INSERT OR REPLACE INTO volumes'
                ' (comic_id, number, name)'
                ' VOLUES ('
                ' :comic_id,'
                ' :volume_id,'
                ' :name,'
                ' )',
                {
                    'comic_id': comic_info['comic_id'],
                    'volume_id': volume['volume_id'],
                    'name': volume['name'],
                }
            )

        now = DT.datetime.now()
        self.conn.execute(
            'INSERT OR REPLACE INTO comics'
            ' (comic_id, title, desc, created_time)'
            ' VALUES ('
            ' :comic_id,'
            ' :title,'
            ' :desc,'
            ' COALESCE('
            '  (SELECT created_time FROM comics WHERE comic_id = :comic_id),'
            '  :created_time'
            ' ),'
            ' )',
            {
                'comic_id': comic_info['comic_id'],
                'title': comic_info['title'],
                'desc': comic_info['desc'],
                'created_time': now,
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
            self, comic_id, volume_number, is_downloaded=True):
        '''
            change volume downloaded status
        '''
        self.conn.execute(
            'UPDATE volumes'
            ' SET is_downloaded = :is_downloaded'
            ' WHERE comic_id = :comic_id AND number = :number',
            {
                'comic_id': comic_id,
                'number': volume_number,
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
            ' WHERE is_downloaded = 0'
            ' ORDER BY comic_id').fetchall()

    def get_all_comics():
        pass
