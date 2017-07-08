"""Cmdlr comic module."""

import os
import sys

from . import log
from . import amgr
from . import schema
from . import exceptions
from . import sessions
from . import cmeta
from . import cvolume


def _get_path_mode(path, new_meta_url):
    """Get path is which mode.

    Args:
        path (str): local dir path
        new_meta_url (str): new incoming meta's url

    Returns:
        (path_mode, fs_comic)
    """
    try:
        fs_comic = Comic(path=path)
        if fs_comic.meta.get('url') == new_meta_url:
            return 'SAME_COMIC', fs_comic
        else:
            return 'DIFFERENT_COMIC', fs_comic
    except exceptions.NotAComicDir:
        if os.path.exists(path):
            return 'EXTERNAL_RESOURCE', None
        else:
            return 'NOT_USED', None


def _get_comic_init_exception(path, url, incoming_dir):
    return exceptions.InvalidValue(
            'Must give only one argments: path, (url, incoming_dir).'
            ' path: "{}", url: "{}", incoming_dir: "{}"'.format(
                path, url, incoming_dir))


class Comic():
    """Comic data container."""

    def __init__(self, *, path=None, url=None, incoming_dir=None):
        """Init."""
        self.path = None
        self.meta = {}
        self.incoming_dir = None
        self.ready = False

        if path and (url or incoming_dir):
            raise _get_comic_init_exception(path, url, incoming_dir)
        elif path:
            self.__load_by_path(path)
        elif url and incoming_dir:
            self.__load_by_url(url, incoming_dir)
        else:
            raise _get_comic_init_exception(path, url, incoming_dir)

    def __load_by_url(self, url, incoming_dir):
        self.meta['url'] = amgr.get_normalized_entry(url)
        self.incoming_dir = incoming_dir

    def __load_by_path(self, path):
        """load comic info from file system metadata.

        Args:
            path (str): comic dir path
        """
        self.meta = cmeta.load_meta(path)
        self.meta['url'] = amgr.get_normalized_entry(self.meta['url'])
        self.path = path
        self.ready = True

    def __update_meta(self, parsing_meta):
        """Update comic meta to both meta file and self."""
        url = self.meta['url']

        if self.ready:
            self.meta = cmeta.get_updated_meta(
                    self.meta,
                    parsing_meta['volumes'],
                    parsing_meta['finished'],
                    )

        else:  # the `url` not SYNC with local dir currently (`self.path`)
            path = os.path.join(self.incoming_dir,
                                parsing_meta['name'])

            path_mode, fs_comic = _get_path_mode(path, url)

            if path_mode == 'SAME_COMIC':
                self.meta = cmeta.get_updated_meta(
                        fs_comic.meta,
                        parsing_meta['volumes'],
                        parsing_meta['finished'],
                        )
                self.path = path

            elif path_mode == 'NOT_USED':
                self.meta = cmeta.get_new_meta(parsing_meta, url)
                self.path = path

            elif path_mode == 'DIFFERENT_COMIC':
                raise exceptions.ComicDirOccupied(
                        'Url Not The Same: "{}"'.format(path))

            elif path_mode == 'EXTERNAL_RESOURCE':
                raise exceptions.ComicDirOccupied(
                        'External Occupied: "{}"'.format(path))

            else:
                raise RuntimeError('Unknown Program Error')

        cmeta.save_meta(self.path, self.meta)
        self.ready = True

    async def get_info(self, loop):
        """Load comic info from url.

        It will cause a lot of network and parsing operation.
        """
        url = self.meta['url']

        request = sessions.get_request(url)
        comic_req_kwargs = amgr.get_prop(url, 'comic_req_kwargs', {})
        get_comic_info = amgr.get_prop(url, 'get_comic_info')

        async with request(url=url, **comic_req_kwargs) as resp:
            ori_meta = await get_comic_info(resp, request=request, loop=loop)
            try:
                parsing_meta = schema.parsing_meta(ori_meta)
            except Exception as e:
                e.ori_meta = ori_meta
                raise

        self.__update_meta(parsing_meta)

        log.logger.info('Meta Updated: {name} ({url})'.format(
            **parsing_meta, url=url))

    async def download(self, loop,
                       volume_names=None, force=False, skip_errors=False):
        """Download comic volume in database.

        Args:
            volume_names (iterable): volumes should be fetch
                                     if None, fetch everythings.
            force (bool): override exists files if exists
            skip_errors (bool): allow part of images not be fetched correctly
        """
        sd_volnames = cvolume.get_should_download_volnames(
                self.path, self.meta['name'], self.meta['volumes'],
                volume_names, force)

        for volname in sorted(sd_volnames):
            vurl = self.meta['volumes'][volname]
            try:
                await cvolume.download_one_volume(
                        path=self.path,
                        curl=self.meta['url'],
                        comic_name=self.meta['name'],
                        vurl=vurl,
                        volume_name=volname,
                        skip_errors=skip_errors,
                        loop=loop)
            except Exception:
                log.logger.error(
                        'Volume Download Failed: {cname}_{vname}'
                        ' ({vurl})'.format(
                            cname=self.meta['name'],
                            vname=volname,
                            vurl=vurl),
                        exc_info=sys.exc_info())
