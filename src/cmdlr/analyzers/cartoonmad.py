"""The www.cartoonmad.com analyzer.

# Entry examples #

- http://www.cartoonmad.com/comic/5640.html
"""

import re
import urllib.parse as UP

from bs4 import BeautifulSoup


def _get_soup(binary):
    html = binary.decode('big5', errors='ignore')

    return BeautifulSoup(html, 'lxml')


def _get_name(soup):
    return soup.title.string.split(' - ')[0]


def _get_description(soup):
    return soup.find('fieldset', id='info').td.get_text().strip()


def _get_authors(soup):
    return [soup.find(string=re.compile('作者：')).string
            .split('：')[1].strip()]


def _get_finished(soup):
    return True if soup.find('img', src='/image/chap9.gif') else False


def _get_volumes(soup, baseurl):
    a_nodes = (soup
               .find('legend', string=re.compile('漫畫線上觀看'))
               .parent
               .find_all(href=re.compile(r'^/comic/')))

    return {
        a.string: UP.urljoin(
            str(baseurl),
            a.get('href'),
        )
        for a in a_nodes
    }


entry_patterns = [
    re.compile(r'^https?://(?:www.)?cartoonmad.com/comic/(\d+)(?:\.html)?$'),
]


def entry_normalizer(url):
    """Normalize all possible entry url to single one form."""
    match = entry_patterns[0].search(url)
    id = match.group(1)

    return 'https://www.cartoonmad.com/comic/{}.html'.format(id)


async def get_comic_info(resp, **kwargs):
    """Find comic info from entry."""
    soup = _get_soup(await resp.read())

    return {'name': _get_name(soup),
            'description': _get_description(soup),
            'authors': _get_authors(soup),
            'finished': _get_finished(soup),
            'volumes': _get_volumes(soup, str(resp.url))}


async def save_volume_images(resp, save_image, **kwargs):
    """Get all images in one volume."""
    def get_page_count(soup):
        return len(soup.find_all('option', value=True))

    def get_img_url_generator(soup):
        baseimgurl = soup.find('img', src=re.compile(r'http://web'))['src']

        def get_img_url(page_number):
            return UP.urljoin(baseimgurl, '{:0>3}.jpg'.format(page_number))

        return get_img_url

    soup = _get_soup(await resp.read())
    get_img_url = get_img_url_generator(soup)
    page_count = get_page_count(soup)

    for page_num in range(1, page_count + 1):
        save_image(page_num, url=get_img_url(page_num))
