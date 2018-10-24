"""Cmdlr multiple comics manager."""

import os

from . import exceptions
from . import log
from .comic import Comic
from .comic import get_parsed_meta
from .metatool import MetaToolkit


class ComicManager:
    """Manage all comics in whole system."""

    def __init__(self, config, amgr):
        """Init comic manager."""
        self.config = config
        self.amgr = amgr
        self.meta_toolkit = MetaToolkit(config)
        self.url_to_comics = {}

        self.__load_comic_in_dirs()

    def __load_comic_in_dir(self, dir):
        for basename in os.listdir(dir):
            comicdir = os.path.join(dir, basename)

            if Comic.is_comic_dir(comicdir):
                try:
                    comic = Comic(self.amgr, self.meta_toolkit, comicdir)

                    if comic.url in self.url_to_comics:
                        another_comic_dir = self.url_to_comics[comic.url].dir

                        raise exceptions.DuplicateComic(
                            'Comic "{url}" in both "{dir1}" and "{dir2}",'
                            ' please remove at least one.'
                            .format(url=comic.url,
                                    dir1=comic.dir,
                                    dir2=another_comic_dir)
                        )

                    else:
                        self.url_to_comics[comic.url] = comic

                except exceptions.NoMatchAnalyzer as e:
                    log.logger.debug('{} ({})'.format(e, dir))

    def __load_comic_in_dirs(self):
        for dir in self.config.dirs:
            if os.path.isdir(dir):
                self.__load_comic_in_dir(dir)

    def __get_normalized_urls(self, urls):
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
                result.add(self.amgr.get_normalized_entry(url))

            except exceptions.NoMatchAnalyzer:
                log.logger.error('No Matched Analyzer: {}'.format(url))

        return result

    def get_url_to_comics(self, urls):
        """Pick some comics be selected by input url."""
        if not urls:
            return self.url_to_comics

        normalized_urls = self.__get_normalized_urls(urls)

        return {
            url: self.url_to_comics[url]
            for url in normalized_urls if url in self.url_to_comics
        }

    def get_non_exist_urls(self, urls):
        """Pick non-local existed urls."""
        normalized_urls = self.__get_normalized_urls(urls)

        return [url for url in normalized_urls
                if url not in self.url_to_comics]

    async def build_comic(self, loop, curl, ctrl):
        """Build comic from url."""
        parsed_meta = await get_parsed_meta(
            loop, self.amgr, self.meta_toolkit, curl)

        if curl in self.url_to_comics:
            raise exceptions.DuplicateComic('Duplicate comic found. Cancel.')

        comic = Comic.build_from_parsed_meta(
            self.config, self.amgr, self.meta_toolkit, parsed_meta, curl)

        self.url_to_comics[curl] = comic

        log.logger.info('Meta Created: {name} ({curl})'
                        .format(**parsed_meta, curl=curl))

        if ctrl.get('download'):
            await comic.download(loop, ctrl.get('skip_download_errors'))
