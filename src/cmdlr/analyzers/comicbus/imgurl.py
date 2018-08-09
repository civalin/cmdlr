"""Image decoder."""

import re
import os
from bs4 import BeautifulSoup

import execjs


class Decoder():
    """Image path decoder."""

    @staticmethod
    def get_img_urls(html, comic_id, vol_id):
        """Get all image urls."""
        def get_jsctx():
            """Get execjs context."""
            dirpath = os.path.dirname(os.path.abspath(__file__))
            jslib_path = os.path.join(dirpath, 'cdecoder-lib.js')

            with open(jslib_path, encoding='utf8') as f:
                jslib_code = f.read()

            return execjs.compile(jslib_code)

        def get_jscode(html):
            soup = BeautifulSoup(html, 'lxml')

            return (soup
                    .find('script', string=re.compile(r'var chs='))
                    .get_text()
                    .split('\n')[-1]
                    .strip())

        jsctx = get_jsctx()
        js = get_jscode(html)
        page_count = jsctx.call('getPageCount', js, int(vol_id))

        return [(jsctx.call('getUrl', js, int(vol_id), page_num), page_num)
                for page_num in range(1, page_count + 1)]
