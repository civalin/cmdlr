"""Processing the javascript."""

import os
import json
import subprocess
from tempfile import NamedTemporaryFile
from shutil import which
from tempfile import gettempdir
from functools import lru_cache

from ..exception import ExternalDependencyNotFound
from ..log import logger


@lru_cache()
def _prepare_node_env():
    node_cmd = which('node')
    npm_cmd = which('npm')

    if not node_cmd:
        raise ExternalDependencyNotFound('Can not found `node` in system.')

    if not npm_cmd:
        raise ExternalDependencyNotFound('Can not found `npm` in system.')

    temp_dir = gettempdir()
    node_cache_dir = os.path.join(temp_dir, 'cmdlr-node-cache')
    node_path = os.path.join(node_cache_dir, 'node_modules')

    if not os.path.exists(node_path):
        logger.debug('[npm] Retrieving external node.js modules...')

        external_modules = ['vm2@~3.6.4']

        subprocess.run(
            [
                npm_cmd,
                'install',
                *external_modules,
                '--prefix',
                node_cache_dir,
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )

        logger.debug('[npm] Retrieving external node.js modules... Success.')

    return node_cmd, node_path


_js_code_template = r'''
const { VM } = require('vm2');

const vm = new VM({
    timeout: 1000,
    sandbox: {},
    console: 'off',
});

const code = %%CODE%%;
let evalValue = vm.run(code);

if (evalValue === undefined) {
    evalValue = null;
}

console.log(JSON.stringify(evalValue))
'''


def run_in_nodejs(js):
    """Dispatch to external nodejs and get the eval result.

    Args:
        js(str): javascript code without escaped.

    Returns:
        js return value, already converted from build-in json module.

    """
    node_cmd, node_path = _prepare_node_env()

    full_code = _js_code_template.replace('%%CODE%%', json.dumps(js))

    with NamedTemporaryFile(mode='wt') as f:
        f.write(full_code)
        f.flush()

        ret_value = subprocess.run(
            [
                node_cmd,
                f.name,
                '--require',
                'vm2'
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={'NODE_PATH': node_path},
        ).stdout

    return json.loads(ret_value.decode())
