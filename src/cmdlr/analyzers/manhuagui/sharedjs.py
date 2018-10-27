"""Share js library."""

import os

from functools import lru_cache


@lru_cache(None)
def get_shared_js():
    """Generate shared javascript library."""
    dirpath = os.path.dirname(os.path.abspath(__file__))
    lzs_path = os.path.join(dirpath, 'lz-string.min.js')

    with open(lzs_path, encoding='utf8') as f:
        lzs_code = f.read()

    extend_code = """
    String.prototype.splic = function(f) {
        return LZString.decompressFromBase64(this).split(f)
    };
    """

    return lzs_code + extend_code
