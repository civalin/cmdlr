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

from . import comicanalyzer
from . analyzers import *


_ANALYZERS = []


def _get_custom_data_key(azr):
    return 'analyzer_custom_data_' + azr.codename()


def set_custom_data(cdb, custom_data):
    try:
        (codename, data) = custom_data.split('/', 1)
        if data == '':
            data = {}
        else:
            pairs = [pair.split('=', 1) for pair in data.split(',')]
            data = {key: value for key, value in pairs}
    except ValueError:
        print('"{}" cannot be parsed. Cancel.'.format(
            custom_data))
        return
    for cls in comicanalyzer.ComicAnalyzer.__subclasses__():
        if cls.codename() == codename:
            try:
                cls(data)
                key = _get_custom_data_key(cls)
                print('{} <= {}'.format(cls.name(), data))
                cdb.set_option(key, data)
                print('Updated done!')
            except:
                print('Custom data test failed. Cancel.')
            return
    print('Analyzer codename: "{}" not found. Cancel.'.format(codename))


def get_custom_data_in_cdb(cdb, cls):
    key = _get_custom_data_key(cls)
    data = cdb.get_option(key)
    if not (data and type(data) == dict):
        data = {}
    return data


def initial_analyzers(cdb):
    for cls in comicanalyzer.ComicAnalyzer.__subclasses__():
        data = get_custom_data_in_cdb(cdb, cls)
        try:
            azr = cls(data)
            _ANALYZERS.append(azr)
        except comicanalyzer.ComicAnalyzerDisableException:
            continue
        except:
            print(('** Error: Analyzer "{} ({})" cannot be initialized.\n'
                   '    -> Current custom data: {}').format(
                cls.name(), cls.codename(), data))


def get_analyzer_by_comic_id(comic_id):
    for azr in _ANALYZERS:
        if comic_id.split('/')[0] == azr.codename():
            return azr
    return None


def get_analyzer_and_comic_id(comic_entry):
    def get_analyzer_by_url(url):
        for analyzer in _ANALYZERS:
            comic_id = analyzer.url_to_comic_id(url)
            if comic_id:
                return analyzer
        return None

    azr = get_analyzer_by_url(comic_entry)
    if azr is None:
        azr = get_analyzer_by_comic_id(comic_entry)
        if azr is None:
            print('"{}" not fits any analyzers.'.format(comic_entry))
            return (None, None)
        else:
            comic_id = comic_entry
    else:
        comic_id = azr.url_to_comic_id(comic_entry)
    return (azr, comic_id)


def get_all_analyzers():
    return _ANALYZERS
