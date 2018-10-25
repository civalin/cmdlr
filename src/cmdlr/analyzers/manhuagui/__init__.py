"""The *.manhuagui.com analyzer."""

import re
import os
import functools
import random
import urllib.parse as UP

from bs4 import BeautifulSoup

from cmdlr import exceptions
from cmdlr.analyzer import BaseAnalyzer
from cmdlr.autil import run_in_nodejs


@functools.lru_cache()
def _get_shared_js():
    dirpath = os.path.dirname(os.path.abspath(__file__))
    lzs_path = os.path.join(dirpath, 'lz-string.min.js')

    with open(lzs_path, encoding='utf8') as f:
        lzs_code = f.read()

    extend_code = """
    String.prototype.splic = String.prototype.splic = function(f) {
        return LZString.decompressFromBase64(this).split(f)
    };
    """

    return lzs_code + extend_code


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
        shared_js = _get_shared_js()

        volumes_html = run_in_nodejs(
            shared_js
            + ('LZString.decompressFromBase64("{lzstring}")'
               .format(lzstring=lzstring))
        ).eval

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
            for a in (sect_title_node
                      .find_next_sibling(class_='chapter-list')
                      .find_all('a', href=re.compile(r'^/comic/.*\.html$')))
        })

    return result


class Analyzer(BaseAnalyzer):
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

    > Hint: The real servers url are look like:
            `http://{code}.hamreus.com:8080`
    """

    entry_patterns = [
        re.compile(
            r'^https?://(www|tw).(?:manhuagui|ikanman).com/comic/(\d+)/?$',
        ),
    ]

    session_init_kwargs = {
        'headers': {
            'referer': 'http://www.manhuagui.com/comic/',
            'user-agent': ('Mozilla/5.0 AppleWebKit/537.3'
                           ' (KHTML, like Gecko)'
                           ' Windows 10 Chrome/64.0.3938.120 Safari/537.36')
        },
    }

    available_image_servers = ['dx', 'eu', 'i', 'lt', 'us']

    def __get_real_image_servers(self):
        disabled_image_servers = (self.customization
                                  .get('disabled_image_servers', []))

        return [s for s in self.available_image_servers
                if s not in disabled_image_servers]

    def __get_img_url(self,
                      img_servers, c_info_path, c_info_filename, cid, md5):
        if c_info_filename.endswith('.webp'):
            filename = c_info_filename[:-5]

        else:
            filename = c_info_filename

        server = random.choice(img_servers)

        return (
            'http://{server}.hamreus.com{c_info_path}{filename}?{qs}'
            .format(server=server,
                    c_info_path=c_info_path,
                    filename=filename,
                    qs=UP.urlencode({'cid': cid, 'md5': md5}))
        )

    def entry_normalizer(self, url):
        """Normalize all possible entry url to single one form."""
        match = self.entry_patterns[0].search(url)
        id = match.group(2)

        meta_source = self.customization.get('meta_source')

        if meta_source is None:
            subdomain = match.group(1)

        elif meta_source == 'cn':
            subdomain = 'www'

        elif meta_source == 'tw':
            subdomain = 'tw'

        else:
            raise exceptions.AnalyzerRuntimeError(
                'manhuagui.data_source should be one of ["tw", "cn", null]')

        return 'https://{}.manhuagui.com/comic/{}/'.format(subdomain, id)

    async def get_comic_info(self, resp, loop, **kwargs):
        """Find comic info from entry."""
        html = await resp.text()
        soup = BeautifulSoup(html, 'lxml')

        return {'name': _get_name(soup),
                'description': _get_description(soup),
                'authors': _get_authors(soup),
                'finished': _get_finished(soup),
                'volumes': _get_volumes(soup, str(resp.url))}

    async def save_volume_images(self, resp, save_image, **kwargs):
        """Get all images in one volume."""
        html = await resp.text()
        soup = BeautifulSoup(html, 'lxml')

        js_string = soup.find('script', string=re.compile(r'window\["')).string
        encrypted_js_string = re.sub(r'^window\[.+?\]', '', js_string)

        shared_js = _get_shared_js()
        SMH_js_string = run_in_nodejs(shared_js + encrypted_js_string).eval

        c_info_js_string = 'cInfo = {};'.format(
            re.search(r'{.*}', SMH_js_string).group(0))
        c_info = run_in_nodejs(c_info_js_string).env.get('cInfo')

        img_servers = self.__get_real_image_servers()

        for idx, c_info_filename in enumerate(c_info['files']):
            img_url = self.__get_img_url(
                img_servers,
                c_info['path'],
                c_info_filename,
                c_info['cid'],
                c_info['sl']['md5'],
            )

            save_image(page_num=idx + 1, url=img_url)
