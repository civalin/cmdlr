"""The *.manhuagui.com analyzer.

# Entry examples #

- http://tw.manhuagui.com/comic/23292/
- http://www.manhuagui.com/comic/23292/



# Configurations #

## `meta_source` ##

(Not required, string or null, allow: 'tw', 'cn')

Choice one of following as metadata source:

- <tw.manhuagui.com> (tw) or
- <www.manhuagui.com> (cn)

If null or not exists, respect the original entry url.



## `disabled_image_servers` ##

(Not required, list of strings)

Select which images servers should *NOT* be used. Any non-exists server
code will be ignored.

Current available servers: ['dx', 'eu', 'i', 'lt', 'us']

> Hint: The real servers url are look like: `http://{code}.hamreus.com:8080`
"""

import re
import os
import functools
import random
import urllib.parse as UP

from bs4 import BeautifulSoup
import execjs

from ... import config
from ... import exceptions


_available_image_servers = ['dx', 'eu', 'i', 'lt', 'us']

_meta_source = config.get_customization('manhuagui').get('meta_source')


@functools.lru_cache()
def _get_shared_jsctx():
    dirpath = os.path.dirname(os.path.abspath(__file__))
    lzs_path = os.path.join(dirpath, 'lz-string.min.js')
    with open(lzs_path, encoding='utf8') as f:
        lzs_code = f.read()

    extend_code = """
    String.prototype.splic = String.prototype.splic = function(f) {
        return LZString.decompressFromBase64(this).split(f)
    };
    """

    final_code = lzs_code + extend_code
    return execjs.compile(final_code)


def _get_name(soup):
    return soup.find('div', class_='book-title').h1.string


def _get_description(soup):
    return soup.find('div', id='intro-all').get_text()


def _get_authors(soup):
    return [a.string for a in soup
            .find('strong', string=re.compile('^(?:漫畫作者：|漫画作者：)$'))
            .parent('a')]


def _get_finished(soup):
    text = (soup
            .find('strong', string=re.compile('^(?:漫畫狀態：|漫画状态：)$'))
            .find_next_sibling('span')
            .string)

    if '已完結' in text or '已完结' in text:
        return True

    return False


def _get_volumes(soup, baseurl):
    vs_node = soup.find('input', id='__VIEWSTATE')

    if vs_node:  # 18X only
        lzstring = vs_node['value']
        shared_jsctx = _get_shared_jsctx()
        volumes_html = shared_jsctx.eval(
                'LZString.decompressFromBase64("{lzstring}")'
                .format(lzstring=lzstring))
        volumes_node = BeautifulSoup(volumes_html, 'lxml')
    else:
        volumes_node = soup.find('div', class_=['chapter', 'cf'])

    sect_title_nodes = volumes_node.find_all('h4')

    result = {}

    for sect_title_node in sect_title_nodes:
        sect_title = sect_title_node.get_text()
        result.update({
            '{}_{}'.format(sect_title, a['title']):
            UP.urljoin(baseurl, a['href'])
            for a
            in (sect_title_node
                .find_next_sibling(class_='chapter-list')
                .find_all('a', href=re.compile(r'^/comic/.*\.html$')))
                })

    return result


def _get_real_image_servers():
    disabled_image_servers = (config
                              .get_customization('manhuagui')
                              .get('disabled_image_servers', []))
    return [s for s in _available_image_servers
            if s not in disabled_image_servers]


_real_image_servers = _get_real_image_servers()


def _get_img_url(c_info_path, c_info_filename, cid, md5):
    if c_info_filename.endswith('.webp'):
        filename = c_info_filename[:-5]
    else:
        filename = c_info_filename

    server = random.choice(_real_image_servers)

    return (
        'http://{server}.hamreus.com{c_info_path}{filename}?{qs}'
        .format(server=server,
                c_info_path=c_info_path,
                filename=filename,
                qs=UP.urlencode({'cid': cid, 'md5': md5}))
    )


session_init_kwargs = {
    'headers': {
        'referer': 'http://www.manhuagui.com/comic/',
        'user-agent': ('Mozilla/5.0 AppleWebKit/537.3 (KHTML, like Gecko)'
                       ' Windows 10 Chrome/64.0.3938.120 Safari/537.36')
    },
}


entry_patterns = [
    re.compile(r'^http://(www|tw).(?:manhuagui|ikanman).com/comic/(\d+)/$'),
]


def entry_normalizer(url):
    """Normalize all possible entry url to single one form."""
    match = entry_patterns[0].search(url)
    id = match.group(2)

    if _meta_source is None:
        subdomain = match.group(1)
    elif _meta_source == 'cn':
        subdomain = 'www'
    elif _meta_source == 'tw':
        subdomain = 'tw'
    else:
        raise exceptions.AnalyzerRuntimeError(
                'manhuagui.data_source should be one of ["tw", "cn", null]')

    return 'http://{}.manhuagui.com/comic/{}/'.format(subdomain, id)


async def get_comic_info(resp, loop, **kwargs):
    """Find comic info from entry."""
    html = await resp.text()
    soup = BeautifulSoup(html, 'lxml')
    return {'name': _get_name(soup),
            'description': _get_description(soup),
            'authors': _get_authors(soup),
            'finished': _get_finished(soup),
            'volumes': _get_volumes(soup, str(resp.url))}


async def save_volume_images(resp, save_image, **kwargs):
    """Get all images in one volume."""
    html = await resp.text()
    soup = BeautifulSoup(html, 'lxml')

    js_string = soup.find('script', string=re.compile(r'window\["')).string
    encrypted_js_string = re.sub(r'^window\[.+?\]', '', js_string)

    shared_jsctx = _get_shared_jsctx()
    SMH_js_string = shared_jsctx.eval(encrypted_js_string)
    c_info_js_string = 'cInfo = {};'.format(
        re.search(r'{.*}', SMH_js_string).group(0))
    c_info = execjs.compile(c_info_js_string).eval('cInfo')

    for idx, c_info_filename in enumerate(c_info['files']):
        img_url = _get_img_url(c_info['path'],
                               c_info_filename,
                               c_info['cid'],
                               c_info['sl']['md5'])
        save_image(page_num=idx + 1, url=img_url)
