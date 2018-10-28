"""Offer dict merging tool."""

from collections import Mapping


def merge_dict(base_dict, incoming_dict):
    """Merge 2 dict, and return new dict."""
    bd_copy = base_dict.copy()

    for k, _ in incoming_dict.items():
        if (k in bd_copy
                and isinstance(bd_copy[k], dict)
                and isinstance(incoming_dict[k], Mapping)):
            bd_copy[k] = merge_dict(bd_copy[k], incoming_dict[k])

        else:
            bd_copy[k] = incoming_dict[k]

    return bd_copy
