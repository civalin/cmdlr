"""Analyzer utils."""

import json
import subprocess
from tempfile import NamedTemporaryFile
from shutil import which
from collections import namedtuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .exception import ExternalDependencyNotFound


_JSResult = namedtuple('JSResult', ['eval', 'env'])


def run_in_nodejs(js):
    """Dispatch to external nodejs and get the eval result.

    Args:
        js(str): javascript code without escaped.

    Returns:
        JSResult type result, already converted from build-in json module.

    """
    cmd = which('node')
    if not cmd:
        raise ExternalDependencyNotFound('Can not found node js in system.')

    full_code = '''const vm = require('vm');

    const sandbox = {{}};
    vm.createContext(sandbox);

    const code = {};
    let evalValue = vm.runInContext(code, sandbox);

    if (evalValue === undefined) {{
        evalValue = null;
    }}

    console.log(JSON.stringify({{eval: evalValue, env: sandbox}}))
    '''.format(json.dumps(js))

    with NamedTemporaryFile(mode='wt') as f:
        f.write(full_code)
        f.flush()

        ret_value = subprocess.check_output([
            cmd,
            f.name,
        ])

    return _JSResult(**json.loads(ret_value.decode()))


_FetchResult = namedtuple('FetchResult', ['soup', 'absurl'])


async def fetch(url, request,
                encoding='utf8', parser='html.parser', **req_kwargs):
    """Get remote html resource and parse it.

    Args:
        url: a remote html resource url
        request: the `request` function in analyzer
        encoding: the html encoding, e.g., utf8, big5
        parser: the BeautifulSoup parser code.
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
    soup = BeautifulSoup(text, parser)

    base_tag = soup.select_one('html > head > base[href]')

    if base_tag:
        base_href = base_tag.get('href')
        base_url = urljoin(base_url, base_href)

    def absurl(url):
        return urljoin(base_url, url)

    return _FetchResult(soup=soup, absurl=absurl)
