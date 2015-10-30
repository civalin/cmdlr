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


class U17ComicException(comicanalyzer.ComicAnalyzerException):
    pass


class U17Analyzer(comicanalyzer.ComicAnalyzer):

    @classmethod
    def codename(cls):
        return 'u17'

    @classmethod
    def name(cls):
        return '有妖氣'

    @classmethod
    def site(cls):
        return 'www.u17.com'

    def info(self):
        return """
            ## 有妖氣 Analyzer ## -------------------------------------
            #
            #   This analyzer are focus on u17.com.
            #   Typical comic url:
            #       http://www.u17.com/comic/<number>.html
            #
            #   Custom data: Not required
            #
            #   LICENSE:    MIT
            #   Author:     Civa Lin<larinawf@gmail.com>
            #   Bug report: https://bitbucket.org/civalin/cmdlr
            #   Version:    2015.10.30
            #
            #----------------------------------------------------------
        """

    def url_to_comic_id(self, comic_entry_url):
        match = re.search('u17.com/comic/(\d+).html',
                          comic_entry_url)
        if match is None:
            return None
        else:
            local_comic_id = match.groups()[0]
            return self.convert_to_comic_id(local_comic_id)

    def comic_id_to_url(self, comic_id):
        local_comic_id = self.convert_to_local_comic_id(comic_id)
        if local_comic_id:
            return 'http://www.u17.com/comic/{}.html'.format(
                local_comic_id)
        else:
            return None

    def get_comic_info(self, comic_id):
        def get_title(comic_html):
            match_title = re.search(r'(.*?)</h1>',
                                    comic_html)
            title = match_title.group(1).strip()
            return title

        def get_desc(comic_html):
            match_desc = re.search(
                r'<p class="words" id="words">(.*?)</p>',
                comic_html,
                re.M | re.DOTALL)
            desc = match_desc.group(1).strip()
            desc = re.sub('<.+?>', '', desc)
            desc = html.unescape(desc)
            return desc

        def get_volumes(comic_html):
            match_volumes = re.findall(
                'id="cpt_(\d+)"\s*href="[^"]+?"'
                '\s*title="([^"]+?)"\s*target="_blank"\s*>',
                comic_html,
                re.M | re.DOTALL)
            volumes = [
                {
                    'volume_id': v[0].strip(),
                    'name': '{:>04}_{}'.format(
                        index + 1, v[1].split()[0].strip())}
                for index, v in enumerate(match_volumes)]
            return volumes

        comic_url = self.comic_id_to_url(comic_id)
        comic_html = downloader.get(
            comic_url).decode('utf8', errors='ignore')
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
            return 'http://www.u17.com/chapter/{}.html?t=old'.format(
                volume_id)

        def get_pages(volume_html):
            match_ori_pages_json = re.search(
                "image_list: \$.evalJSON\('(.*?)'\)",
                volume_html)
            ori_pages_json = match_ori_pages_json.group(1)
            ori_pages = json.loads(ori_pages_json)
            pages_phase1 = [
                (int(page), base64.b64decode(data['src']).decode('utf8'))
                for page, data in ori_pages.items()
                if data.get('url') is None]
            pages = [
                {
                    'url': url,
                    'local_filename': '{:03}.{}'.format(
                        page,
                        url.rsplit('.', 1)[1])
                }
                for page, url in sorted(pages_phase1)]
            return pages

        volume_html = downloader.get(
            get_volume_url(volume_id)).decode('utf8', errors='ignore')
        return get_pages(volume_html)
