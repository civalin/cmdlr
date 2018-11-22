"""Cmdlr comic meta schema."""

import datetime as DT
import html

from voluptuous import Schema
from voluptuous import FqdnUrl
from voluptuous import Required
from voluptuous import Length
from voluptuous import Range
from voluptuous import Unique
from voluptuous import All
from voluptuous import Any
from voluptuous import Invalid
from voluptuous import ALLOW_EXTRA


_trans_comp_table = str.maketrans('\?*<":>+[]/', '＼？＊＜”：＞＋〔〕／')
_trans_path_table = str.maketrans('?*<">+[]', '？＊＜”＞＋〔〕')


def _safe_path_comp(string):
    """Make string is a safe path component."""
    return string.translate(_trans_comp_table)


def _safe_path(string):
    """Make string is a safe path."""
    return string.translate(_trans_path_table)


def _st_str(v):
    return html.unescape(str(v)).strip()


def _safepathcomp_str(v):
    return _safe_path_comp(_st_str(v))


def _safepath_str(v):
    return _safe_path(_st_str(v))


def _dict_value_unique(v):
    if not len(v.values()) == len(set(v.values())):
        raise Invalid('contain duplicate items')
    return v


parsed_meta_schema = Schema({
    Required('name'): All(Length(min=1), _safepathcomp_str),
    Required('volumes'): Schema(All(
        dict,
        Length(min=1),
        _dict_value_unique,
        {All(Length(min=1), _safepathcomp_str): FqdnUrl()}
    )),
    'finished': bool,
    'description': All(str, _st_str),
    'authors': All([_st_str], Unique()),
})


meta_schema = parsed_meta_schema.extend({
    Required('url'): FqdnUrl(),
    Required('volumes_checked_time'): DT.datetime,
    Required('volumes_modified_time'): DT.datetime,
})

config_schema = Schema({
    'data_dirs': All(
        [
            All(_safepath_str, Length(min=1)),
        ],
        Length(min=1),
    ),

    'logging_dir': Any(
        None,
        All(_safepath_str, Length(min=1))
    ),

    'logging_level': Any('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),

    'analyzer_dir': Any(
        None,
        All(_safepath_str, Length(min=1)),
    ),

    'network': {
        'delay': All(
            Any(int, float),
            Range(min=0),
        ),
        'timeout': All(
            Any(int, float),
            Range(min=1),
        ),
        'max_try': All(int, Range(min=1)),
        'total_connections': All(int, Range(min=1)),
        'per_host_connections': All(int, Range(min=1)),
        'socks_proxy': Any(
            None,
            All(_safepath_str, Length(min=1)),
        ),
    },

    'book_concurrent': All(int, Range(min=1)),

    'analyzer_pref': {
        str: Schema({
            'system': Schema({
                'enabled': bool,
                'delay': All(
                    Any(int, float),
                    Range(min=0),
                ),
                'timeout': All(
                    Any(int, float),
                    Range(min=1),
                ),
                'max_try': All(int, Range(min=1)),
                'per_host_connection': All(int, Range(min=1)),
            }, extra=0),
        }, extra=ALLOW_EXTRA),
    },
})
