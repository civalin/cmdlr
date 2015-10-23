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
import itertools

from . import comicanalyzer
from . analyzers import *


class AnalyzersManager():
    custom_datas_key = 'analyzers_custom_data'

    def __init__(self, cdb):
        def initial_analyzers(custom_datas, black_list):
            '''
                args:
                    custom_datas:
                        {'<str codename>': <dict custom_data>}
            '''
            analyzers, disabled_analyzers = {}, {}
            for a_cls in comicanalyzer.ComicAnalyzer.__subclasses__():
                custom_data = custom_datas.get(a_cls.codename())
                try:
                    azr = a_cls(custom_data)
                    if a_cls.codename() in black_list:
                        disabled_analyzers[azr.codename()] = azr
                    else:
                        analyzers[azr.codename()] = azr
                except comicanalyzer.ComicAnalyzerDisableException:
                    continue
                except:
                    print(('** Error: Analyzer "{} ({})" cannot be'
                           ' initialized.\n'
                           '    -> Current custom data: {}').format(
                        a_cls.name(), a_cls.codename(), custom_data))
            return analyzers, disabled_analyzers

        self.__cdb = cdb
        custom_datas = cdb.get_option(type(self).custom_datas_key, {})
        black_list = cdb.get_option('analyzers_black_list', set())
        self.analyzers, self.disabled_analyzers = initial_analyzers(
            custom_datas, black_list)

    @property
    def all_analyzers(self):
        return {key: value
                for key, value in itertools.chain(
                    self.analyzers.items(),
                    self.disabled_analyzers.items())}

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

    def on(self, codename):
        black_list = self.__cdb.get_option('analyzers_black_list', set())
        try:
            black_list.remove(codename)
        except:
            pass
        self.__cdb.set_option('analyzers_black_list', black_list)
        self.__init__(self.__cdb)

    def off(self, codename):
        black_list = self.__cdb.get_option('analyzers_black_list', set())
        black_list.add(codename)
        self.__cdb.set_option('analyzers_black_list', black_list)
        self.__init__(self.__cdb)

    def print_analyzer_info(self, codename):
        azr = self.all_analyzers.get(codename)
        if azr:
            azr_info = textwrap.dedent(azr.info()).strip(' \n')
            print(azr_info)
            custom_datas = self.__cdb.get_option(
                type(self).custom_datas_key, {})
            custom_data = custom_datas.get(codename, {})
            print('  Current Custom Data: {}'.format(custom_data))

    def print_analyzers_list(self):
        texts = []
        all_analyzers = sorted(itertools.chain(
                self.analyzers.values(),
                self.disabled_analyzers.values()),
            key=lambda azr: azr.codename())
        texts.append('## Analyzers table ## ---------------------------\n')

        for azr in all_analyzers:
            if azr.codename() in self.disabled_analyzers:
                disabled = 'x'
            else:
                disabled = ''
            text = '  {disabled:<1} {codename:<4} - {name} {site}'.format(
                codename=azr.codename(),
                name=azr.name(),
                site=azr.site(),
                disabled=disabled)
            texts.append(text)
        all_text = '\n'.join(texts)
        print(all_text)
        print('\n'
              'Use "-i CODENAME" to find current custom data and more info.')
