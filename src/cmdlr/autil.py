"""Analyzer utils."""

import shutil
import json
import tempfile
import subprocess
from collections import namedtuple

from .exceptions import ExternalDependencyNotFound


JSResult = namedtuple('JSResult', ['eval', 'env'])


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

    return JSResult(**json.loads(ret_value.decode()))
