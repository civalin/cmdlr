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

import re

from .. import comicanalyzer
from .. import downloader


class EightComicException(comicanalyzer.ComicAnalyzerException):
    pass


class EightAnalyzer(comicanalyzer.ComicAnalyzer):

    @classmethod
    def codename(cls):
        return '8c'

    @classmethod
    def name(cls):
        return '8Comic 無限動漫'

    @classmethod
    def site(cls):
        return 'comicvip.com'

    def info(self):
        return """
            ## 8Comic 無限動漫 Analyzer ## ----------------------------
            #
            #   This analyzer are focus on comicvip.com.
            #   Typical comic url:
            #       http://www.comicvip.com/html/<number>.html
            #
            #   Custom data: Not required
            #
            #   LICENSE: MIT
            #   Author: Civa Lin<larinawf@gmail.com>
            #
            #----------------------------------------------------------
        """

    def __init__(self, custom_data):
        super().__init__(custom_data)
        # raise comicanalyzer.ComicAnalyzerDisableException  # disable plugin

    def url_to_comic_id(self, comic_entry_url):
        match = re.search('comicvip.com/html/(\d+).html',
                          comic_entry_url)
        if match is None:
            return None
        else:
            local_comic_id = match.groups()[0]
            return self.convert_to_comic_id(local_comic_id)

    def comic_id_to_url(self, comic_id):
        local_comic_id = self.convert_to_local_comic_id(comic_id)
        if local_comic_id:
            return 'http://www.comicvip.com/html/{}.html'.format(
                local_comic_id)
        else:
            return None

    def get_comic_info(self, comic_id):
        def get_title(one_page_html):
            match_title = re.search(r":\[(.*?)<font id=",
                                    one_page_html)
            title = match_title.group(1).strip()
            return title

        def get_desc(comic_html):
            match_desc = re.search(r'line-height:25px">(.*?)</td>',
                                   comic_html)
            desc = match_desc.group(1).strip()
            desc = re.sub('<.+?>', '', desc)
            return desc

        comic_url = self.comic_id_to_url(comic_id)
        comic_html = downloader.get(
            comic_url).decode('big5', errors='ignore')
        one_page_url = self.__get_one_page_url(comic_html, comic_url)
        one_page_html = downloader.get(
            one_page_url).decode('big5', errors='ignore')
        comic_code = self.__get_comic_code(one_page_html)

        answer = {
            'comic_id': comic_id,
            'title': get_title(one_page_html),
            'desc': get_desc(comic_html),
            'extra_data': {'comic_code': comic_code}
            }

        vol_code_list = self.__split_vol_code_list(comic_code)
        volume_info_list = [self.__decode_volume_code(vol_code)
                            for vol_code in vol_code_list]
        volumes = [{
            'volume_id': v['volume_id'],
            'name': '{:04}'.format(int(v['volume_id']))
            } for v in volume_info_list]

        answer['volumes'] = volumes
        return answer

    def get_volume_pages(self, comic_id, volume_id, extra_data):
        def get_image_url(page_number, local_comic_id,
                          did, sid, volume_number, volume_code, **kwargs):
            def get_hash(page_number):
                magic_number = (((page_number - 1) / 10) % 10) +\
                               (((page_number - 1) % 10) * 3)\
                               + 10
                magic_number = int(magic_number)
                return volume_code[magic_number:magic_number+3]

            hash = get_hash(page_number)
            image_url = "http://img{sid}.8comic.com/{did}/{local_comic_id}/"\
                        "{volume_number}/{page_number:03}_{hash}.jpg".format(
                            page_number=page_number,
                            local_comic_id=local_comic_id,
                            did=did,
                            sid=sid,
                            volume_number=volume_number,
                            hash=hash,
                            )
            return image_url

        comic_code = extra_data['comic_code']
        vol_code_list = self.__split_vol_code_list(comic_code)
        volume_info_list = [self.__decode_volume_code(vol_code)
                            for vol_code in vol_code_list]
        volume_info_dict = {v['volume_id']: v for v in volume_info_list}
        volume_info = volume_info_dict[volume_id]
        local_comic_id = self.convert_to_local_comic_id(comic_id)

        pages = []
        for page_number in range(1, volume_info['page_count'] + 1):
            url = get_image_url(page_number=page_number,
                                local_comic_id=local_comic_id,
                                did=volume_info['did'],
                                sid=volume_info['sid'],
                                volume_number=int(volume_id),
                                volume_code=volume_info['volume_code'])
            local_filename = '{:03}.jpg'.format(page_number)
            pages.append({'url': url, 'local_filename': local_filename})

        return pages

    def __get_one_page_url(self, comic_html, comic_url):
        def __get_page_url_fragment_and_catid(html):
            match = re.search(r"cview\('(.+?)',(\d+?)\)", html)
            if match is None:
                raise EightComicException(
                    "CView decode Error: {}".format(comic_url))
            else:
                answer = match.groups(1)
                return answer

        def __get_page_url(page_url_fragment, catid):
            catid = int(catid)
            if catid in (4, 6, 12, 22):
                baseurl = "http://www.comicvip.com/show/cool-"
            elif catid in (1, 17, 19, 21):
                baseurl = "http://www.comicvip.com/show/cool-"
            elif catid in (2, 5, 7, 9):
                baseurl = "http://www.comicvip.com/show/cool-"
            elif catid in (10, 11, 13, 14):
                baseurl = "http://www.comicvip.com/show/best-manga-"
            elif catid in (3, 8, 15, 16, 18, 20):
                baseurl = "http://www.comicvip.com/show/best-manga-"

            fragment = page_url_fragment.replace(
                ".html", "").replace("-", ".html?ch=")
            return baseurl + fragment

        page_url_fragment, catid = __get_page_url_fragment_and_catid(
            comic_html)
        page_url = __get_page_url(page_url_fragment, catid)
        return page_url

    def __get_comic_code(self, one_page_html):
        match_comic_code = re.search(r"var cs='(\w*)'",
                                     one_page_html)
        comic_code = match_comic_code.group(1)
        return comic_code

    def __split_vol_code_list(self, comic_code):
        '''split code for each volume'''
        chunk_size = 50
        return [comic_code[i:i+chunk_size]
                for i in range(0, len(comic_code), chunk_size)]

    def __decode_volume_code(self, volume_code):
        def get_only_digit(string):
            return re.sub("\D", "", string)

        volume_info = {
            "volume_id": str(int(get_only_digit(volume_code[0:4]))),
            "sid": get_only_digit(volume_code[4:6]),
            "did": get_only_digit(volume_code[6:7]),
            "page_count": int(get_only_digit(volume_code[7:10])),
            "volume_code": volume_code,
            }
        return volume_info
