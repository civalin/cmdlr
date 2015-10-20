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

import pathlib

from . import stringprocess


class ComicPath():
    '''Comic Path Calculator'''

    def __init__(self, output_dir, backup_dir, hanzi_mode=None):
        self.__output_dir = output_dir
        self.__backup_dir = backup_dir
        self.__sp = stringprocess.StringProcess(hanzi_mode=hanzi_mode)

    @property
    def output_dir(self):
        return pathlib.Path(
            self.__sp.replace_unsafe_characters_for_path(
                self.__output_dir))

    @property
    def backup_dir(self):
        return pathlib.Path(
            self.__sp.replace_unsafe_characters_for_path(
                self.__backup_dir))

    def get_comic_dir(self, comic_info):
        return self.output_dir / self.__sp.component_modified(
            comic_info['title'])

    def get_volume_dir(self, comic_info, volume_info):
        return self.get_comic_dir(
            comic_info) / self.__sp.component_modified(volume_info['name'])

    def get_volume_cbz(self, comic_info, volume_info):
        return self.get_volume_dir(comic_info, volume_info).with_suffix(
            '.cbz')

    def get_page_path(self, comic_info, volume_info, page):
        volume_dir = self.get_volume_dir(comic_info, volume_info)
        return volume_dir / self.__sp.component_modified(
            page['local_filename'])

    def get_backup_comic_dir(self, comic_info):
        return self.backup_dir / self.__sp.component_modified(
            '{title}({comic_id})'.format(**comic_info))


def get_cpath(cdb):
    data = {
        'output_dir': cdb.get_option('output_dir'),
        'backup_dir': cdb.get_option('backup_dir'),
        'hanzi_mode': cdb.get_option('hanzi_mode'),
        }
    return ComicPath(**data)
