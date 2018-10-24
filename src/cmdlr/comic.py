"""Cmdlr comic module."""

import os
import sys

from . import log
from . import schema
from . import sessions
from . import cvolume
from . import exceptions


async def get_parsed_meta(loop, amgr, meta_toolkit, curl):
    """Get infomation about specific curl."""
    analyzer = amgr.get_match_analyzer(curl)
    request = sessions.get_request(curl)

    comic_req_kwargs = analyzer.comic_req_kwargs
    get_comic_info = analyzer.get_comic_info

    async with request(url=curl, **comic_req_kwargs) as resp:
        ori_meta = await get_comic_info(resp, request=request, loop=loop)

        try:
            parsed_meta = schema.parsed_meta(ori_meta)

        except Exception as e:
            e.ori_meta = ori_meta
            raise

    return parsed_meta


class Comic():
    """Comic data container."""

    comic_meta_filename = '.comic-meta.yaml'

    @classmethod
    def build_from_parsed_meta(
            cls, config, amgr, meta_toolkit, parsed_meta, curl):
        """Create Local comic dir and return coresponse Comic object."""
        meta = meta_toolkit.create(parsed_meta, curl)

        name = meta['name']
        dir = os.path.join(config.incoming_dir, name)

        if os.path.exists(dir):
            raise exceptions.ComicDirOccupied(
                '"{}" already be occupied, comic "{}" cannot be created.'
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

        if os.path.isfile(meta_filepath):
            return True

        return False

    def __load_meta(self):
        return self.meta_toolkit.load(self.meta_filepath)

    def __init__(self, amgr, meta_toolkit, dir):
        """Init."""
        self.amgr = amgr
        self.dir = dir
        self.meta_toolkit = meta_toolkit

        self.meta_filepath = self.__get_meta_filepath(dir)
        self.meta = self.__load_meta()

        self.analyzer = amgr.get_match_analyzer(self.meta['url'])

        # normalize url
        self.meta['url'] = self.analyzer.entry_normalizer(self.meta['url'])

    def __merge_and_save_meta(self, parsed_meta):
        """Merge comic meta to both meta file and self."""
        self.meta = self.meta_toolkit.update(
            self.meta,
            parsed_meta['volumes'],
            parsed_meta['finished'],
        )

        self.meta_toolkit.save(self.meta_filepath, self.meta)

    @property
    def url(self):
        """Get comic url."""
        return self.meta['url']

    async def update_meta(self, loop):
        """Load comic info from url.

        It will cause a lot of network and parsing operation.
        """
        parsed_meta = await get_parsed_meta(
            loop,
            self.amgr,
            self.meta_toolkit,
            self.url,
        )

        self.__merge_and_save_meta(parsed_meta)

        log.logger.info('Meta Updated: {name} ({curl})'
                        .format(**parsed_meta, curl=self.url))

    async def download(self, loop, skip_errors=False):
        """Download comic volume in database.

        Args:
            skip_errors (bool): allow part of images not be fetched correctly
        """
        sd_volnames = cvolume.get_not_downloaded_volnames(
            self.dir,
            self.meta['name'],
            list(self.meta['volumes'].keys())
        )

        for volname in sorted(sd_volnames):
            vurl = self.meta['volumes'][volname]

            try:
                await cvolume.download_one_volume(
                    amgr=self.amgr,
                    path=self.dir,
                    curl=self.meta['url'],
                    comic_name=self.meta['name'],
                    vurl=vurl,
                    volume_name=volname,
                    skip_errors=skip_errors,
                    loop=loop,
                )

            except Exception:
                log.logger.error(
                    ('Volume Download Failed: {cname}_{vname} ({vurl})'
                     .format(cname=self.meta['name'],
                             vname=volname,
                             vurl=vurl)),
                    exc_info=sys.exc_info(),
                )
