"""Cmdlr multiple comics manager."""

import os
import functools

from . import comic
from . import exceptions
from . import log


def _get_exist_url_comics_in_dir(amgr, urlcomics, dir):
    for basename in os.listdir(dir):
        comic_path = os.path.join(dir, basename)

        try:
            c = comic.Comic(amgr, path=comic_path)
            url = c.meta['url']

            if url in urlcomics:
                raise exceptions.DuplicateComic(
                    'Comic "{url}" in both "{path1}" and "{path2}",'
                    ' please remove at least one.'
                    .format(url=url,
                            path1=c.path,
                            path2=urlcomics[url].path)
                )

            urlcomics[c.meta['url']] = c

        except exceptions.NotAComicDir as e:
            pass

        except exceptions.NoMatchAnalyzer as e:
            log.logger.debug('{} ({})'.format(e, comic_path))


@functools.lru_cache(maxsize=None, typed=True)
def get_exist_url_comics(amgr, *dirs):
    """Get all comic in dirpaths."""
    urlcomics = {}

    for dir in dirs:
        if not os.path.exists(dir):
            continue

        _get_exist_url_comics_in_dir(amgr, urlcomics, dir)

    return urlcomics


def get_normalized_urls(amgr, urls):
    """Convert a lot of urls to normalized urls.

    This function will also strip out:
        1. duplicated urls after normalization. and
        2. the urls no match any analyzers.

    return None if urls is None
    """
    if urls is None:
        return None

    result = set()

    for url in set(urls):
        try:
            result.add(amgr.get_normalized_entry(url))

        except exceptions.NoMatchAnalyzer:
            log.logger.error('No Matched Analyzer: {}'.format(url))

    return result


def get_filtered_url_comics(urlcomics, normalized_urls):
    """Only extract subset of urlcomics if comic url in urls."""
    return {url: urlcomics[url]
            for url in normalized_urls if url in urlcomics}


def get_selected_url_comics(amgr, dirs, urls=None):
    """Get selected url comics by urls and data in comic dir."""
    urlcomics = get_exist_url_comics(amgr, *dirs)

    if urls:
        normalized_urls = get_normalized_urls(amgr, urls)

        already_exists_urlcomics = get_filtered_url_comics(
            urlcomics, normalized_urls)
        not_exists_urlcomics = {
            url: comic.Comic(
                amgr=amgr,
                url=url,
                incoming_dir=dirs[0],
            )
            for url in normalized_urls if url not in urlcomics
        }

        final_urlcomics = {}
        final_urlcomics.update(already_exists_urlcomics)
        final_urlcomics.update(not_exists_urlcomics)

        return final_urlcomics

    else:
        return urlcomics
