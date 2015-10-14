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


######################################################################
#
# Term description:
#
#   codename:
#     A analyzer short name.
#     e.g., 8c
#
#   comic_id: (str)
#     A comic identifier scope in the whole program.
#     Most internal interface using the comic_id to identify one comic.
#     e.g., 8c/123a97
#
#   local_comic_id: (str)
#     A comic identifier scope in the analyzer (comic site)
#     It is a string and a part of comic's url.
#     e.g., 123a97
#
#   (you should convert local_comic_id <-> comic_id by
#    `analyzer.convert_*` function)
#
#   volume_id: (str)
#     A volume identifier scope in a comic.
#     e.g., "13"
#
#   volume_name: (str)
#     A short volume description.
#     e.g., "vol1"
#
#   comic_entry_url: (str)
#     A url which reference a comic (in this site)
#     This url must contain the local_comic_id.
#
#   extra_data: (dict)
#     A comic level cache data.
#     Analyzer designer can define it structure by her(his) self.
#     e.g., {}
#
######################################################################

import abc


class ComicAnalyzerException(Exception):
    pass


class ComicAnalyzer(metaclass=abc.ABCMeta):
    '''Base class of all comic analyzer'''

    @property
    @abc.abstractmethod
    def codename(self):
        '''
        Return analyzer code name.
        Keep it SHORT and CLEAR. and not conflict with other analyzer.
        Recommend use 2 chars.

        e.g., co, sm, rd
        '''

    @property
    @abc.abstractmethod
    def desc(self):
        '''
        Return analyzer short description.
        Recommend include sitename or siteurl for user friendly.

        e.g., "8comic: vipcomic.com"
        '''

    def convert_to_local_comic_id(self, comic_id):
        if comic_id.startswith(self.codename + '/'):
            return comic_id[len(self.codename) + 1:]
        else:
            return None

    def convert_to_comic_id(self, local_comic_id):
        return self.codename + '/' + local_comic_id

    @abc.abstractmethod
    def url_to_comic_id(self, comic_entry_url):
        '''
            Convert comic_entry_url to comic_id.
            If convert success return a str format url, else return None.
        '''

    @abc.abstractmethod
    def comic_id_to_url(self, comic_id):
        '''
            Convert comic_id to comic_entry_url
            If convert success return a str format comic_id, else return None.
        '''

    @abc.abstractmethod
    def get_comic_info(self, comic_id):
        '''
            Get comic info from the internet
            The return data will be saved into user's comic_db

            return:
                {
                    comic_id: <comic_id>,
                    title: <comic_title>,
                    desc: <comic_desc>,
                    extra_data: {...},
                    volumes: [
                        {
                            'volume_id': <volume_id>,  # e.g., '16', '045'
                            'name': <volume_name>,
                        },
                        {...},
                        ...
                    ]
                }
        '''

    @abc.abstractmethod
    def get_volume_pages(self, comic_id, volume_id, extra_data):
        '''
            Get images url for future download.

            args:
                comic_id:
                    which comic you want to analysis
                volume_id:
                    which volume you want to analysis
                extra_data:
                    the comic extradata create by self.get_comic_info()

            yield:
                {
                    'url': <image_url>,
                    'local_filename': <local_filename>,  # e.g., 12.jpg
                }
        '''
