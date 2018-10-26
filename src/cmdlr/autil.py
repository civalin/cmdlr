"""Analyzer utils."""

import shutil
import json
import tempfile
import subprocess
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
    cmd = shutil.which('node')
    if not cmd:
        raise ExternalDependencyNotFound('Can not found node js in system.')

    full_code = '''const vm = require('vm');

    const sandbox = {{}};
    vm.createContext(sandbox);

    code = {};
    evalValue = vm.runInContext(code, sandbox);

    console.log(JSON.stringify({{eval: evalValue, env: sandbox}}))
    '''.format(json.dumps(js))

    with tempfile.NamedTemporaryFile(mode='wt') as f:
        f.write(full_code)
        f.flush()

        ret_value = subprocess.check_output([
            cmd,
            f.name,
        ])

    return _JSResult(**json.loads(ret_value.decode()))


_FetchResult = namedtuple('FetchResult', ['soup', 'get_abspath'])


async def fetch(url, request, encoding='utf8', **req_kwargs):
    """Get BeautifulSoup from remote url."""
    async with request(url, **req_kwargs) as resp:
        binary = await resp.read()
        text = binary.decode(encoding, errors='ignore')
        soup = BeautifulSoup(text, 'lxml')

        base_url = str(resp.url)

    def get_abspath(url):
        return urljoin(base_url, url)

    return _FetchResult(soup=soup,
                        get_abspath=get_abspath)
