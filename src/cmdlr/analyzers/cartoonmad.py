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
import json
import base64
import html

from .. import comicanalyzer
from .. import downloader


class CartoonmadException(comicanalyzer.ComicAnalyzerException):
    pass


class CartoonmadAnalyzer(comicanalyzer.ComicAnalyzer):

    @classmethod
    def codename(cls):
        return 'ctm'

    @classmethod
    def name(cls):
        return '動漫狂'

    @classmethod
    def site(cls):
        return 'www.cartoonmad.com'

    def info(self):
        return """
            ## 動漫狂 Analyzer ## ---------------------------------
            #
            #   This analyzer are focus on cartoonmad.com.
            #   Typical comic url:
            #       http://www.cartoonmad.com/comic/<number>.html
            #
            #   Custom data: Not required
            #
            #   LICENSE:    MIT
            #   Author:     Civa Lin<larinawf@gmail.com>
            #   Bug report: https://bitbucket.org/civalin/cmdlr
            #   Version:    2015.03.06
            #
            #----------------------------------------------------------
        """

    def url_to_comic_id(self, comic_entry_url):
        match = re.search('cartoonmad.com/comic/(\d{1,8}).html',
                          comic_entry_url)
        if match is None:
            return None
        else:
            local_comic_id = match.groups()[0]
            return self.convert_to_comic_id(local_comic_id)

    def comic_id_to_url(self, comic_id):
        local_comic_id = self.convert_to_local_comic_id(comic_id)
        if local_comic_id:
            return 'http://www.cartoonmad.com/comic/{}.html'.format(
                local_comic_id)
        else:
            return None

    def get_comic_info(self, comic_id):
        def get_title(comic_html):
            match_title = re.search(r'<a href=/comic/\d+.html>(.*?)</a>',
                                    comic_html)
            title = match_title.group(1).strip()
            return title

        def get_desc(comic_html):
            match_desc = re.search(
                r'<td style="font-size:11pt;">(.*?)</td>',
                comic_html,
                re.M | re.DOTALL)
            desc = match_desc.group(1).strip()
            desc = re.sub('<.+?>', '', desc)
            desc = html.unescape(desc)
            return desc

        def get_volumes(comic_html):
            match_volumes = re.findall(
                '<a href=/comic/(\d{9,}).html target=_blank>'
                '(.*?)</a>',
                comic_html,
                re.M | re.DOTALL)
            volumes = [
                {
                    'volume_id': v[0],
                    'name': '{}'.format(
                        ' '.join(v[1].split()))}
                for index, v in enumerate(match_volumes)]
            return volumes

        comic_url = self.comic_id_to_url(comic_id)
        comic_html = downloader.get(
            comic_url).decode('big5', errors='ignore')
        answer = {
            'comic_id': comic_id,
            'title': get_title(comic_html),
            'desc': get_desc(comic_html),
            'extra_data': {},
            'volumes': get_volumes(comic_html)
            }
        return answer

    def get_volume_pages(self, comic_id, volume_id, extra_data):
        def get_volume_url(volume_id):
            return 'http://www.cartoomad.com/comic/{}.html'.format(
                volume_id)

        def get_pages(volume_html):
            def get_img_url_generator(volume_html):
                match_img_url = re.search(
                    '<img src="(http://web.+?)"',
                    volume_html)
                img_url = match_img_url.group(1)
                components = img_url.split('/')

                def get_img_url(page_number):
                    components[6] = '{:0>3}.jpg'.format(page_number)
                    return '/'.join(components)

                return get_img_url

            def get_page_count(volume_html):
                match_options = re.findall(r'<option value=', volume_html)
                return len(match_options)

            get_img_url = get_img_url_generator(volume_html)
            page_count = get_page_count(volume_html)
            pages_phase1 = [get_img_url(page_number)
                            for page_number in range(1, page_count + 1)]
            pages = [
                {
                    'url': url,
                    'local_filename': '{}'.format(url.rsplit('/', 1)[1])
                }
                for url in pages_phase1]
            return pages

        volume_html = downloader.get(
            get_volume_url(volume_id)).decode('utf8', errors='ignore')
        return get_pages(volume_html)
