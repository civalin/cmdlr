"""The www.comicbus.com analyzer.

# Entry examples

- http://www.comicbus.com/html/10951.html
"""

import re

from bs4 import BeautifulSoup

from . import imgurl


def _get_name(soup):
    return (soup
            .find('title').string
            .split('漫畫,動畫,在線漫畫')[0])


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


session_init_kwargs = {
        'headers': {
            'referer': 'http://www.comicbus.com',
            },
        }


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


async def save_volume_images(resp, save_image, loop, **kwargs):
    """Get images in one volume."""
    def is_copyright_url(url):
        return re.search(r'comic-\d+.html', str(url))

    def get_comic_id(url):
        return re.search(r'(\d+).html', str(url)).group(1)

    def get_vol_id(url):
        return re.search(r'ch=(\d+)', str(url), re.IGNORECASE).group(1)

    comic_id = get_comic_id(resp.url)
    vol_id = get_vol_id(resp.url)

    binary = await resp.read()
    html = binary.decode('big5', errors='ignore')

    # slow to get_img_urls due to external js op, asynchronized
    img_urls = await loop.run_in_executor(
            None,
            lambda: imgurl.Decoder.get_img_urls(html, comic_id, vol_id))

    for img_url, page_num in img_urls:
        save_image(page_num, url=img_url)
