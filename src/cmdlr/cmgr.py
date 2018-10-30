"""Cmdlr multiple comics manager."""

import os
from collections import namedtuple

from .log import logger
from .exception import DuplicateComic
from .exception import NoMatchAnalyzer
from .comic import Comic
from .comic import MetaToolkit


_SelectedResult = namedtuple('SelectedResult',
                             ['exist_comics', 'not_exist_urls'])


class ComicManager:
    """Manage all comics in whole system."""

    def __init__(self, config, amgr):
        """Init comic manager."""
        self.config = config
        self.amgr = amgr
        self.meta_toolkit = MetaToolkit()
        self.url_to_comics = {}

        self.__load_comic_in_dirs()

    def __load_comic_in_dir(self, dir):
        for basename in os.listdir(dir):
            comicdir = os.path.join(dir, basename)

            if Comic.is_comic_dir(comicdir):
                try:
                    comic = Comic(self.amgr, self.meta_toolkit, comicdir)

                except NoMatchAnalyzer as e:
                    logger.debug('{} ({})'.format(e, comicdir))

                else:
                    if comic.url in self.url_to_comics:
                        another_comic_dir = self.url_to_comics[comic.url].dir

                        raise DuplicateComic(
                            'Comic "{url}" in both "{dir1}" and "{dir2}",'
                            ' please remove at least one.'
                            .format(url=comic.url,
                                    dir1=comic.dir,
                                    dir2=another_comic_dir)
                        )

                    else:
                        self.url_to_comics[comic.url] = comic

    def __load_comic_in_dirs(self):
        for dir in self.config.data_dirs:
            if os.path.isdir(dir):
                self.__load_comic_in_dir(dir)

    def get_non_exist_urls(self, urls):
        """Pick non-local existed urls."""
        normalized_urls = self.amgr.get_normalized_entrys(urls)

        return [url for url in normalized_urls
                if url not in self.url_to_comics]

    def get(self, url):
        """Get a comic by a entry url.

        Returns:
            None if:
                1. url without a match analyzer or
                2. the comic was not exists

        """
        try:
            normalized_url = self.amgr.get_normalized_entry(url)
            return self.url_to_comics.get(normalized_url)

        except NoMatchAnalyzer as e:
            pass

    def get_all(self):
        """Get all comics."""
        return list(self.url_to_comics.values())

    def get_selected(self, urls):
        """Get all comics selected."""
        normalized_urls = self.amgr.get_normalized_entrys(urls)

        url_comics = [(url, self.get(url)) for url in normalized_urls]

        exist_comics = []
        non_exist_urls = []

        for url, comic in url_comics:
            if comic is None:
                non_exist_urls.append(url)

            else:
                exist_comics.append(comic)

        return _SelectedResult(exist_comics, non_exist_urls)

    async def new_comic(self, request_pool, url):
        """Build and register a new comic from url."""
        parsed_meta = await Comic.get_parsed_meta(
            request_pool,
            self.amgr,
            self.meta_toolkit,
            url,
        )

        if url in self.url_to_comics:
            raise DuplicateComic('Duplicate comic found. Cancel.')

        comic = Comic.build_from_parsed_meta(
            self.config, self.amgr, self.meta_toolkit, parsed_meta, url)

        self.url_to_comics[url] = comic

        logger.info('Meta Created: {name} ({url})'
                    .format(**parsed_meta, url=url))

        return comic
