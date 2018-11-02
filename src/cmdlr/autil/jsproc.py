"""Processing the javascript."""

import json
import subprocess
from tempfile import NamedTemporaryFile
from shutil import which
from collections import namedtuple

from ..exception import ExternalDependencyNotFound


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
