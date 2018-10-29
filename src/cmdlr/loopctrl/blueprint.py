"""Build blueprint for choreographer."""

from itertools import groupby

from .steprunner import book_runner
from .step import get_url_steps
from .step import get_comic_steps


def _get_aname_runners_exist(exist_comics, ctrl, request_pool):
    skip_errors = ctrl.get('skip_errors')
    comic_steps = get_comic_steps(ctrl)

    return [
        (
            comic.analyzer.name,
            book_runner(
                comic_steps,
                [comic, skip_errors, request_pool],
                comic.url,
            )
        )
        for comic in exist_comics
    ]


def _get_aname_runners_non_exist(non_exist_urls,
                                 amgr, cmgr, ctrl, request_pool):
    skip_errors = ctrl.get('skip_errors')
    url_steps = get_url_steps(ctrl)

    return [
        (
            amgr.get(url).name,
            book_runner(
                url_steps,
                [url, skip_errors, request_pool, cmgr],
                url,
            )
        )
        for url in non_exist_urls
    ]


def _group_second_by_first(tuple_list):
    def first(item):
        return item[0]

    return {
        key: [value for key, value in key_values]
        for key, key_values
        in groupby(sorted(tuple_list, key=first), key=first)
    }


def _get_exist_and_non_exist(cmgr, urls):
    if urls:
        exist_comics, non_exist_urls = cmgr.get_selected(urls)

    else:
        exist_comics = cmgr.get_all()
        non_exist_urls = []

    return exist_comics, non_exist_urls


def get_aname_to_runners(cmgr, amgr, request_pool, urls, ctrl):
    """Build the resource choreographer need for."""
    exist_comics, non_exist_urls = _get_exist_and_non_exist(cmgr, urls)

    aname_runners_exist = _get_aname_runners_exist(
        exist_comics,
        ctrl,
        request_pool,
    )
    aname_runners_non_exist = _get_aname_runners_non_exist(
        non_exist_urls,
        amgr,
        cmgr,
        ctrl,
        request_pool,
    )

    aname_runners = aname_runners_non_exist + aname_runners_exist

    return _group_second_by_first(aname_runners)
