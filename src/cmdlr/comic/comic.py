"""Cmdlr comic module."""

import os
import sys

from ..schema import parsed_meta_schema
from ..log import logger
from ..exception import ComicDirOccupied

from .volfile import ComicVolume


class Comic():
    """Comic data container."""

    comic_meta_filename = '.comic-meta.json'

    @staticmethod
    async def get_parsed_meta(request_pool, amgr, meta_toolkit, curl):
        """Get infomation about specific curl."""
        analyzer = amgr.get(curl)

        request = request_pool.get_request(analyzer)
        loop = request_pool.loop

        get_comic_info = analyzer.get_comic_info

        ori_meta = await get_comic_info(url=curl,
                                        request=request,
                                        loop=loop)

        try:
            parsed_meta = parsed_meta_schema(ori_meta)

        except Exception as e:
            e.ori_meta = ori_meta
            raise

        return parsed_meta

    @classmethod
    def build_from_parsed_meta(
            cls, config, amgr, meta_toolkit, parsed_meta, curl):
        """Create Local comic dir and return coresponse Comic object."""
        meta = meta_toolkit.create(parsed_meta, curl)

        name = meta['name']
        dir = os.path.join(config.incoming_data_dir, name)

        if os.path.exists(dir):
            raise ComicDirOccupied(
                '"{}" already be occupied.'
                .format(dir, curl),
            )

        meta_filepath = os.path.join(dir, cls.comic_meta_filename)
        meta_toolkit.save(meta_filepath, meta)

        return cls(amgr, meta_toolkit, dir)

    @classmethod
    def __get_meta_filepath(cls, dir):
        return os.path.join(dir, cls.comic_meta_filename)

    @classmethod
    def is_comic_dir(cls, dir):
        """check_localdir can be load as a Comic or not."""
        meta_filepath = cls.__get_meta_filepath(dir)

        # TODO: compatiability only, pending to remove
        old_meta_filepath = os.path.splitext(meta_filepath)[0] + '.yaml'

        if os.path.isfile(meta_filepath) or os.path.isfile(old_meta_filepath):
            return True

        return False

    @classmethod
    def __get_meta_info(cls, amgr, meta_toolkit, dir):
        meta_filepath = cls.__get_meta_filepath(dir)
        meta = meta_toolkit.load(meta_filepath)

        analyzer = amgr.get(meta['url'])

        # normalize url
        meta['url'] = analyzer.entry_normalizer(meta['url'])

        return analyzer, meta_filepath, meta

    def __init__(self, amgr, meta_toolkit, dir):
        """Init."""
        self.amgr = amgr
        self.meta_toolkit = meta_toolkit
        self.dir = dir

        (self.analyzer,
         self.meta_filepath,
         self.meta) = self.__get_meta_info(amgr, meta_toolkit, dir)

    def __merge_and_save_meta(self, parsed_meta):
        """Merge comic meta to both meta file and self."""
        self.meta = self.meta_toolkit.update(self.meta, parsed_meta)

        self.meta_toolkit.save(self.meta_filepath, self.meta)

    @property
    def url(self):
        """Get comic url."""
        return self.meta['url']

    async def update_meta(self, request_pool):
        """Load comic info from url.

        It will cause a lot of network and parsing operation.
        """
        parsed_meta = await self.get_parsed_meta(
            request_pool,
            self.amgr,
            self.meta_toolkit,
            self.url,
        )

        self.__merge_and_save_meta(parsed_meta)

        logger.info('Meta Updated: {name} ({curl})'
                    .format(**parsed_meta, curl=self.url))

    async def download(self, request_pool, skip_errors=False):
        """Download comic volume in database.

        Args:
            skip_errors (bool): allow part of images not be fetched correctly
        """
        comic_volume = ComicVolume(self)
        wanted_volnames = comic_volume.get_wanted_names()

        for volname in sorted(wanted_volnames):
            try:
                await comic_volume.download(
                    request_pool,
                    volname,
                    skip_errors,
                )

            except Exception:
                logger.error(
                    ('Volume Download Failed: {cname}_{vname} ({vurl})'
                     .format(cname=self.meta['name'],
                             vname=volname,
                             vurl=self.meta['volumes'][volname]),
                     ),
                    exc_info=sys.exc_info(),
                )
