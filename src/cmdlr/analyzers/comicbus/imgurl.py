"""Image decoder."""
import re


class CDecoder():
    """Image path decoder for copyright = 1 page."""

    y = 46

    @classmethod
    def __lc(cls, l):
        if len(l) != 2:
            return l
        az = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        a = l[0:1]
        b = l[1:2]
        if a == "Z":
            return str(8000 + az.index(b))
        else:
            return str(az.index(a) * 52 + az.index(b))

    @classmethod
    def __su(cls, a, b, c):
        return a[b:b+c]

    @classmethod
    def __get_page_count(cls, cs, vol_id):  # == susdv == ps
        """Get page count from cs and vol_num."""
        return int(cls.__lc(cls.__su(cs,
                                     (int(vol_id) - 1) * cls.y + 0,
                                     2)))

    @classmethod
    def __get_img_url(cls, cs, comic_id, vol_id, page_num):
        """Get img url."""
        def get_vol_code(cs, vol_id):  # == ekiyy
            return cls.__lc(cls.__su(cs,
                                     (int(vol_id) - 1) * cls.y + 2,
                                     40))

        def get_magic_code(cs, vol_id):  # == rehqx
            return cls.__lc(cls.__su(cs,
                                     (int(vol_id) - 1) * cls.y + 44,
                                     2))

        def nn(n):
            return '{:>03}'.format(n)

        def mm(p):
            return (int((p - 1) / 10) % 10) + (((p - 1) % 10) * 3)

        mc = get_magic_code(cs, vol_id)
        vc = get_vol_code(cs, vol_id)
        return ('http://img'
                + cls.__su(mc, 0, 1)
                + '.8comic.com/'
                + cls.__su(mc, 1, 1)
                + '/'
                + comic_id
                + '/'
                + vol_id
                + '/'
                + nn(page_num)
                + '_'
                + cls.__su(vc, mm(page_num), 3)
                + '.jpg')

    @classmethod
    def get_img_urls(cls, cs, comic_id, vol_id):
        """Get all img urls."""
        page_count = cls.__get_page_count(cs, vol_id)
        return [(cls.__get_img_url(cs, comic_id, vol_id, page_num), page_num)
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
    def get_img_urls(cls, cs, comic_id, vol_id):
        """Get all img urls."""
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
