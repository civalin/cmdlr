"""Info extractor."""

import re

from bs4 import BeautifulSoup

from cmdlr.autil import run_in_nodejs

from .sharedjs import get_shared_js


async def _get_volumes_data_node(soup, loop):
    """Get single node contain volumes data from entry soup."""
    vs_node = soup.find('input', id='__VIEWSTATE')

    if vs_node:  # 18X only
        lzstring = vs_node['value']
        question_js = ('LZString.decompressFromBase64("{lzstring}")'
                       .format(lzstring=lzstring))
        full_js = get_shared_js() + question_js

        volumes_html = (
            await loop.run_in_executor(None, lambda: run_in_nodejs(full_js))
        ).eval
        volumes_data_node = BeautifulSoup(volumes_html, 'lxml')

    else:
        volumes_data_node = soup.find('div', class_=['chapter', 'cf'])

    return volumes_data_node


def _get_volumes_from_volumes_data_node(volumes_data_node, absurl):
    """Get all volumes from volumes data node."""
    result = {}

    for sect_title_node in volumes_data_node.find_all('h4'):
        sect_title = sect_title_node.get_text()

        chapter_data_node = (
            sect_title_node
            .find_next_sibling(class_='chapter-list')
        )
        chapter_a_nodes = (
            chapter_data_node
            .find_all('a', href=re.compile(r'^/comic/.*\.html$'))
        )

        name_url_mapper = {
            '{}_{}'.format(sect_title, a['title']): absurl(a['href'])
            for a in chapter_a_nodes
        }

        result.update(name_url_mapper)

    return result


async def extract_volumes(fetch_result, loop):
    """Get all volumes."""
    soup, absurl = fetch_result

    volumes_data_node = await _get_volumes_data_node(soup, loop)
    return _get_volumes_from_volumes_data_node(volumes_data_node, absurl)


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
