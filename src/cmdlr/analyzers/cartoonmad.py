"""The www.cartoonmad.com analyzer.

[Entry examples]

    - http://www.cartoonmad.com/comic/5640.html
    - https://www.cartoonmad.com/comic/5640.html
"""

import re
from urllib.parse import urljoin

from cmdlr.analyzer import BaseAnalyzer
from cmdlr.autil import fetch


class Analyzer(BaseAnalyzer):
    """The www.cartoonmad.com analyzer.

    [Entry examples]

    - http://www.cartoonmad.com/comic/5640.html
    - https://www.cartoonmad.com/comic/5640.html
    """

    entry_patterns = [
        re.compile(
            r'^https?://(?:www.)?cartoonmad.com/comic/(\d+)(?:\.html)?$'
        ),
    ]

    def entry_normalizer(self, url):
        """Normalize all possible entry url to single one form."""
        match = self.entry_patterns[0].search(url)
        id = match.group(1)

        return 'https://www.cartoonmad.com/comic/{}.html'.format(id)

    @staticmethod
    def __extract_name(fetch_result):
        return fetch_result.soup.title.string.split(' - ')[0]

    @staticmethod
    def __extract_volumes(fetch_result):
        a_tags = (fetch_result.soup
                  .find('legend', string=re.compile('漫畫線上觀看'))
                  .parent
                  .find_all(href=re.compile(r'^/comic/')))

        return {a.string: fetch_result.absurl(a.get('href'))
                for a in a_tags}

    @staticmethod
    def __extract_finished(fetch_result):
        return (True
                if fetch_result.soup.find('img', src='/image/chap9.gif')
                else False)

    @staticmethod
    def __extract_description(fetch_result):
        return (fetch_result.soup
                .find('fieldset', id='info').td.get_text().strip())

    @staticmethod
    def __extract_authors(fetch_result):
        return [fetch_result.soup
                .find(string=re.compile('作者：'))
                .string.split('：')[1].strip()]

    async def get_comic_info(self, url, request, **unused):
        """Get comic info."""
        fetch_result = await fetch(url, request, encoding='big5')

        return {
            'name': self.__extract_name(fetch_result),
            'volumes': self.__extract_volumes(fetch_result),
            'description': self.__extract_description(fetch_result),
            'authors': self.__extract_authors(fetch_result),
            'finished': self.__extract_finished(fetch_result),
        }

    @staticmethod
    def __get_base_url(soup, absurl):
        ref = soup.find('img', src=re.compile(r'/cartoonimg/'))
        if ref:
            base_url = absurl(ref['src'])
        else:
            base_url = soup.find('img', src=re.compile(r'http://web'))['src']

        return base_url


    async def save_volume_images(self, url, request, save_image, **unused):
        """Get all images in one volume."""
        soup, absurl = await fetch(url, request, encoding='big5')
        base_url = self.__get_base_url(soup, absurl)

        def get_img_url(page_number):
            return urljoin(base_url, '{:0>3}.jpg'.format(page_number))

        page_count = len(soup.find_all('option', value=True))

        for page_num in range(1, page_count + 1):
            save_image(page_num, url=get_img_url(page_num))
