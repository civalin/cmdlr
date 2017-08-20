"""Image decoder."""
import re
import os
from bs4 import BeautifulSoup

import execjs


class CDecoder():
    """Image path decoder for copyright = 1 page."""

    @staticmethod
    def get_img_urls(html, comic_id, vol_id):
        """Get all image urls."""
        def get_jsctx():
            """get execjs context."""
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


class NCDecoder():
    """Image path decoder for copyright = 0 page."""

    @classmethod
    def __get_this_vol_info(cls, cs, vol_id):
        def get_volume_cs_list(cs):
            chunk_size = 50
            return [cs[i:i+chunk_size]
                    for i in range(0, len(cs), chunk_size)]

        def decode_volume_cs(volume_cs):
            def get_only_digit(string):
                return re.sub("\D", "", string)

            volume_info = {
                "vol_id": str(int(get_only_digit(volume_cs[0:4]))),
                "sid": get_only_digit(volume_cs[4:6]),
                "did": get_only_digit(volume_cs[6:7]),
                "page_count": int(get_only_digit(volume_cs[7:10])),
                "volume_cs": volume_cs,
                }
            return volume_info

        volume_cs_list = get_volume_cs_list(cs)
        volume_info_list = [decode_volume_cs(volume_cs)
                            for volume_cs in volume_cs_list]
        volume_info_dict = {v['vol_id']: v for v in volume_info_list}
        return volume_info_dict[vol_id]

    @classmethod
    def __get_img_url(cls, page_num, comic_id, did, sid, vol_id, volume_cs):
        def get_hash(page_num):
            magic_number = (((page_num - 1) / 10) % 10)\
                            + (((page_num - 1) % 10) * 3)\
                            + 10
            magic_number = int(magic_number)
            return volume_cs[magic_number:magic_number+3]

        hash = get_hash(page_num)
        return ("http://img{sid}.6comic.com:99/{did}/"
                "{comic_id}/{vol_id}/{page_num:03}_{hash}.jpg").format(
                        page_num=page_num,
                        comic_id=comic_id,
                        did=did,
                        sid=sid,
                        vol_id=vol_id,
                        hash=hash,
                        )

    @classmethod
    def get_img_urls(cls, html, comic_id, vol_id):
        """Get all img urls."""
        def get_cs(html):
            return re.search(r"var cs='(\w*)'", html).group(1)

        cs = get_cs(html)
        vol_info = cls.__get_this_vol_info(cs, vol_id)

        pages = []
        for page_num in range(1, vol_info['page_count'] + 1):
            url = cls.__get_img_url(page_num=page_num,
                                    comic_id=comic_id,
                                    did=vol_info['did'],
                                    sid=vol_info['sid'],
                                    vol_id=vol_id,
                                    volume_cs=vol_info['volume_cs'])
            pages.append((url, page_num))

        return pages
