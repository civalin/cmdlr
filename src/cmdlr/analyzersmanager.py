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

import textwrap

from . import comicanalyzer
from . analyzers import *


class AnalyzersManager():
    custom_datas_key = 'analyzers_custom_data'

    def __init__(self, cdb):
        def initial_analyzers(custom_datas):
            '''
                args:
                    custom_datas:
                        {'<str codename>': <dict custom_data>}
            '''
            analyzers = {}
            for cls in comicanalyzer.ComicAnalyzer.__subclasses__():
                custom_data = custom_datas.get(cls.codename())
                try:
                    azr = cls(custom_data)
                    analyzers[azr.codename()] = azr
                except comicanalyzer.ComicAnalyzerDisableException:
                    continue
                except:
                    print(('** Error: Analyzer "{} ({})" cannot be'
                           ' initialized.\n'
                           '    -> Current custom data: {}').format(
                        cls.name(), cls.codename(), custom_data))
            return analyzers

        self.__cdb = cdb
        custom_datas = cdb.get_option(type(self).custom_datas_key, {})
        self.analyzers = initial_analyzers(custom_datas)

    def set_custom_data(self, custom_data_str):
        def parsed(custom_data_str):
            try:
                (codename, data_str) = custom_data_str.split('/', 1)
                if data_str == '':
                    custom_data = {}
                else:
                    pairs = [item.split('=', 1)
                             for item in data_str.split(',')]
                    custom_data = {key: value for key, value in pairs}
            except ValueError:
                print('"{}" cannot be parsed. Cancel.'.format(
                    custom_data_str))
                return (None, None)
            return (codename, custom_data)

        codename, custom_data = parsed(custom_data_str)
        if codename is None:
            print('Analyzer codename: "{}" not found. Cancel.'.format(
                codename))
        else:
            azr = self.analyzers.get(codename)
            try:
                type(azr)(custom_data)
                key = type(self).custom_datas_key
                custom_datas = self.__cdb.get_option(key)
                custom_datas[codename] = custom_data
                self.__cdb.set_option(key, custom_datas)
                print('{} <= {}'.format(azr.name(), custom_data))
                print('Updated done!')
            except:
                print('Custom data test failed. Cancel.')

    def get_analyzer_by_comic_id(self, comic_id):
        codename = comic_id.split('/')[0]
        return self.analyzers.get(codename)

    def get_analyzer_and_comic_id(self, comic_entry):
        def get_analyzer_by_url(url):
            for azr in self.analyzers.values():
                comic_id = azr.url_to_comic_id(url)
                if comic_id:
                    return azr
            return None

        azr = get_analyzer_by_url(comic_entry)
        if azr is None:
            azr = self.get_analyzer_by_comic_id(comic_entry)
            if azr is None:
                return (None, None)
            else:
                comic_id = comic_entry
        else:
            comic_id = azr.url_to_comic_id(comic_entry)
        return (azr, comic_id)

    def print_analyzer_info(self, codename):
        azr = self.analyzers.get(codename)
        if azr:
            azr_info = textwrap.dedent(azr.info()).strip(' \n')
            print(azr_info)
            custom_datas = self.__cdb.get_option(
                type(self).custom_datas_key, {})
            custom_data = custom_datas.get(codename, {})
            print('  Current Custom Data: {}'.format(custom_data))
