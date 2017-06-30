"""The www.comicbus.com analyzer.

# Entry examples

- http://www.comicbus.com/html/10951.html
"""

import re

from bs4 import BeautifulSoup


def _get_name(soup):
    return (soup
            .find('meta', attrs={'name': 'keywords'})['content']
            .split(',')[0])


def _get_description(soup):
    return soup.find('table', colspan='3').td.get_text().strip()


def _get_authors(soup):
    return [soup.find(string='作者：').parent.find_next_sibling('td').string]


def _get_finished(soup):
    msg = soup.find('a', href='#Comic').font.next_sibling
    return True if '完' in msg else False


def _get_volumes(soup):
    def onclick_to_url(onclick_str):
        m = re.search(r'cview\(\s*\'([^\']+)\',(\d+),(\d)', onclick_str)

        url_postfix = (m.group(1)
                       .replace('.html', '').replace('-', '.html?ch='))
        copyright = m.group(3)

        if copyright == '1':
            url_prefix = 'http://v.comicbus.com/online/comic-'
        else:
            url_prefix = 'http://v.nowcomic.com/online/manga_'

        return '{}{}'.format(url_prefix, url_postfix)

    a_nodes = soup.find_all('a', onclick=re.compile(r'cview\('))

    name_onclicks = [(a.font.contents[0] if a.font else a.string, a['onclick'])
                     for a in a_nodes]
    return {name.strip(): onclick_to_url(onclick_str)
            for name, onclick_str in name_onclicks}


entry_patterns = [re.compile(r'^http://www.comicbus.com/html/\d+\.html$')]


async def get_comic_info(resp, **kwargs):
    """Get comic info from entry."""
    binary = await resp.read()
    html = binary.decode('big5', errors='ignore')
    soup = BeautifulSoup(html, 'lxml')

    return {'name': _get_name(soup),
            'description': _get_description(soup),
            'authors': _get_authors(soup),
            'finished': _get_finished(soup),
            'volumes': _get_volumes(soup)}


async def save_volume_images(resp, save_image, **kwargs):
    """Get images in one volume."""
    def get_comic_id(url):
        return re.search(r'(\d+).html', str(url)).group(1)

    def get_volume_id(url):
        return re.search(r'Ch=(\d+)', str(url), re.IGNORECASE).group(1)

    def get_cs(html):
        return re.search(r"var cs='(\w*)'", html).group(1)

    def get_volume_cs_list(cs):
        chunk_size = 50
        return [cs[i:i+chunk_size]
                for i in range(0, len(cs), chunk_size)]

    def decode_volume_cs(volume_cs):
        def get_only_digit(string):
            return re.sub("\D", "", string)

        volume_info = {
            "volume_id": str(int(get_only_digit(volume_cs[0:4]))),
            "sid": get_only_digit(volume_cs[4:6]),
            "did": get_only_digit(volume_cs[6:7]),
            "page_count": int(get_only_digit(volume_cs[7:10])),
            "volume_cs": volume_cs,
            }
        return volume_info

    def get_image_url(page_num, comic_id, did, sid, volume_id, volume_cs):
        def get_hash(page_num):
            magic_number = (((page_num - 1) / 10) % 10)\
                            + (((page_num - 1) % 10) * 3)\
                            + 10
            magic_number = int(magic_number)
            return volume_cs[magic_number:magic_number+3]

        hash = get_hash(page_num)
        return ("http://img{sid}.6comic.com:99/{did}/"
                "{comic_id}/{volume_id}/{page_num:03}_{hash}.jpg").format(
                        page_num=page_num,
                        comic_id=comic_id,
                        did=did,
                        sid=sid,
                        volume_id=volume_id,
                        hash=hash,
                        )

    def get_image_urls(comic_id, volume_id, volume_info):
        pages = []
        for page_num in range(1, volume_info['page_count'] + 1):
            url = get_image_url(page_num=page_num,
                                comic_id=comic_id,
                                did=volume_info['did'],
                                sid=volume_info['sid'],
                                volume_id=volume_id,
                                volume_cs=volume_info['volume_cs'])
            pages.append((url, page_num))

        return pages

    comic_id = get_comic_id(resp.url)
    volume_id = get_volume_id(resp.url)

    binary = await resp.read()
    html = binary.decode('big5', errors='ignore')

    cs = get_cs(html)
    volume_cs_list = get_volume_cs_list(cs)
    volume_info_list = [decode_volume_cs(volume_cs)
                        for volume_cs in volume_cs_list]
    volume_info_dict = {v['volume_id']: v for v in volume_info_list}
    this_volume_info = volume_info_dict[volume_id]

    for img_url, page_num in get_image_urls(
            comic_id, volume_id, this_volume_info):
        save_image(page_num, url=img_url)
