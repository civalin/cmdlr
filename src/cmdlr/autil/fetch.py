"""fetch data and parseing."""
from collections import namedtuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup


_FetchResult = namedtuple('FetchResult', ['soup', 'absurl'])


async def fetch(url, request, encoding='utf8', **req_kwargs):
    """Get remote html resource and parse it.

    Args:
        url: a remote html resource url
        request: the `request` function in analyzer
        encoding: the html encoding, e.g., utf8, big5
        req_kwargs: all keyword arguments should pass to request()

    Returns:
        a FetchResult object `fetch_result`

        fetch_result.soup: A BeautifulSoup object.
        fetch_result.absurl: A function can re

    """
    async with request(url, **req_kwargs) as resp:
        binary = await resp.read()
        base_url = str(resp.url)

    text = binary.decode(encoding, errors='ignore')
    soup = BeautifulSoup(text, 'html.parser')

    base_tag = soup.select_one('html > head > base[href]')

    if base_tag:
        base_href = base_tag.get('href')
        base_url = urljoin(base_url, base_href)

    def absurl(url):
        return urljoin(base_url, url)

    return _FetchResult(soup=soup, absurl=absurl)
