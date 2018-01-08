"""Cmdlr comic meta schema."""

import datetime as DT
import html

from voluptuous import (
        Schema, FqdnUrl, Required, Length, Range, Unique, All, Any, Invalid)

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


parsing_meta = Schema({
    Required('name'): All(Length(min=1), _safepathcomp_str),
    Required('description'): All(str, _st_str),
    Required('authors'): All([_st_str], Unique()),
    Required('finished'): bool,
    Required('volumes'): Schema(All(dict, Length(min=1), _dict_value_unique, {
            All(Length(min=1), _safepathcomp_str): FqdnUrl(),
            })),
    })


meta = parsing_meta.extend({
    Required('url'): FqdnUrl(),
    Required('volumes_checked_time'): DT.datetime,
    Required('volumes_modified_time'): DT.datetime,
    })

config = Schema({
    'delay': All(float, Range(min=0)),
    'dirs': All(Length(min=1), [All(Length(min=1), _safepath_str)]),
    'extra_analyzer_dir': Any(None, All(Length(min=1), _safepath_str)),
    'disabled_analyzers': [_st_str],
    'per_host_concurrent': All(int, Range(min=1)),
    'max_concurrent': All(int, Range(min=1)),
    'max_retry': All(int, Range(min=0)),
    'proxy': Any(None, FqdnUrl()),
    'customization': {str: dict},
    })
