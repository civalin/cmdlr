"""Info extractor."""

import re

from bs4 import BeautifulSoup

from cmdlr.autil import run_in_nodejs

from .sharedjs import get_shared_js


async def _get_volumes_data_tag(soup, loop):
    """Get single tag contain volumes data from entry soup."""
    vs_tag = soup.find('input', id='__VIEWSTATE')

    if vs_tag:  # 18X only
        lzstring = vs_tag['value']
        question_js = ('LZString.decompressFromBase64("{lzstring}")'
                       .format(lzstring=lzstring))
        full_js = get_shared_js() + question_js

        volumes_html = await loop.run_in_executor(
            None,
            lambda: run_in_nodejs(full_js),
        )

        volumes_data_tag = BeautifulSoup(volumes_html, 'html.parser')

    else:
        volumes_data_tag = soup.find('div', class_=['chapter', 'cf'])

    return volumes_data_tag


def _get_volumes_from_volumes_data_tag(volumes_data_tag, absurl):
    """Get all volumes from volumes data tag."""
    result = {}

    for sect_title_tag in volumes_data_tag.find_all('h4'):
        sect_title = sect_title_tag.get_text()

        chapter_data_tag = (
            sect_title_tag
            .find_next_sibling(class_='chapter-list')
        )
        chapter_a_tags = (
            chapter_data_tag
            .find_all('a', href=re.compile(r'^/comic/.*\.html$'))
        )

        name_url_mapper = {
            '{}_{}'.format(sect_title, a['title']): absurl(a['href'])
            for a in chapter_a_tags
        }

        result.update(name_url_mapper)

    return result


async def extract_volumes(fetch_result, loop):
    """Get all volumes."""
    soup, absurl = fetch_result
    volumes_data_tag = await _get_volumes_data_tag(soup, loop)

    return _get_volumes_from_volumes_data_tag(volumes_data_tag, absurl)


def extract_name(fetch_result):
    """Get name."""
    return fetch_result.soup.find('div', class_='book-title').h1.string


def extract_finished(fetch_result):
    """Get finished state."""
    text = (fetch_result.soup
            .find('strong', string=re.compile('^(?:漫畫狀態：|漫画状态：)$'))
            .find_next_sibling('span')
            .string)

    if '已完結' in text or '已完结' in text:
        return True

    return False


def extract_description(fetch_result):
    """Get description."""
    return fetch_result.soup.find('div', id='intro-all').get_text()


def extract_authors(fetch_result):
    """Get authors."""
    return [a.string for a in fetch_result.soup
            .find('strong', string=re.compile('^(?:漫畫作者：|漫画作者：)$'))
            .parent('a')]
