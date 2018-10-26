"""Comic volume file related function."""

import os
import zipfile
import datetime as DT
import asyncio
from tempfile import TemporaryDirectory

from . import log
from . import yamla
from .exception import NoImagesFound
from .exception import InvalidValue


class ImageFetchPool:
    """Control one volume image fetching."""

    @staticmethod
    def __get_image_filepath(page_num, ext, dirpath):
        filename = '{page_num:04}{ext}'.format(page_num=page_num, ext=ext)

        return os.path.join(dirpath, filename)

    @staticmethod
    def __save_binary(filepath, binary):
        with open(filepath, mode='wb') as f:
            f.write(binary)

    def __init__(self, request_pool, comic, vname, dirpath, skip_errors):
        """Init all data."""
        self.analyzer = comic.analyzer

        self.request = request_pool.get_request(self.analyzer)
        self.loop = request_pool.loop

        self.cname = comic.meta['name']

        self.vname = vname
        self.vurl = comic.meta['volumes'][vname]
        self.dirpath = dirpath
        self.skip_errors = skip_errors

        self.save_image_tasks = []

    async def __save_image_op(self, page_num, url, **request_kwargs):
        async with self.request(url=url, **request_kwargs) as resp:
            ext = self.analyzer.get_image_extension(resp)

            if not ext:
                raise InvalidValue(
                    'Cannot determine file extension of "{}" content type.'
                    .format(resp.content_type)
                )

            binary = await resp.read()

            filepath = self.__get_image_filepath(page_num, ext, self.dirpath)
            self.__save_binary(filepath, binary)

            log.logger.info('Image Fetched: {}_{}_{:03}'.format(
                self.cname, self.vname, page_num))

    async def __save_image_error_process(self,
                                         page_num, url, **request_kwargs):
        try:
            await self.__save_image_op(page_num, url, **request_kwargs)

        except asyncio.CancelledError as e:
            pass

        except Exception as e:
            log.logger.error(
                'Image Fetch Failed : {}_{}_{:03} ({} => {}: {})'
                .format(self.cname, self.vname, page_num,
                        url, type(e).__name__, e),
            )

            if not self.skip_errors:
                raise e from None

    def get_save_image(self):
        """Get save_image function."""
        def save_image(page_num, *, url, **request_kwargs):
            task = self.loop.create_task(
                self.__save_image_error_process(
                    int(page_num),
                    url,
                    **request_kwargs,
                ),
            )

            self.save_image_tasks.append(task)

        return save_image

    @staticmethod
    def __cleanup_save_image_tasks(done, pending):
        """Cancel the pending tasks & raise exception in save_image_tasks."""
        for task in pending:
            task.cancel()

        for e in [task.exception() for task in done]:
            if e:
                raise e from None

    async def download(self):
        """Wait all pending download tasks (build by `save_image`) have finish.

        Returns:
            True if looking successful

        """
        if len(self.save_image_tasks) == 0:
            raise NoImagesFound(
                'Not found any images in volume: [{}] => [{}] {}'
                .format(self.cname, self.vname, self.vurl))

        done, pending = await asyncio.wait(
            self.save_image_tasks,
            loop=self.loop,
            return_when=asyncio.FIRST_EXCEPTION,
        )

        self.__cleanup_save_image_tasks(done, pending)  # cleanup & raise

        at_least_one = len(os.listdir(self.dirpath)) >= 1
        if len(pending) == 0 and at_least_one:
            return True


class ComicVolume:
    """Volume generate."""

    def __init__(self, comic):
        """Init volume related data."""
        self.comic = comic

    def __get_filename(self, name):
        comic_name = self.comic.meta['name']

        return '{}_{}.cbz'.format(comic_name, name)

    def __get_filepath(self, name):
        filename = self.__get_filename(name)

        return os.path.join(self.comic.dir, filename)

    def get_wanted_names(self):
        """Get volumn names which not downloaded."""
        filename_name_mapper = {
            self.__get_filename(name): name
            for name in self.comic.meta['volumes'].keys()
        }

        all_filenames = filename_name_mapper.keys()
        exist_filenames = set(os.listdir(self.comic.dir))

        return [filename_name_mapper[filename]
                for filename in all_filenames
                if filename not in exist_filenames]

    def __save_meta(self, dirpath, name):
        filepath = os.path.join(dirpath, '.volume-meta.yaml')

        yamla.to_file(
            filepath,
            {'comic_url': self.comic.url,
             'volume_url': self.comic.meta['volumes'][name],
             'comic_name': self.comic.meta['name'],
             'volume_name': name,
             'archived_time': DT.datetime.now(DT.timezone.utc)},
        )

    def __convert_to_cbz(self, from_dir, name):
        """Convert dir to cbz format."""
        filepath = self.__get_filepath(name)
        tmp_filepath = filepath + '.tmp'

        with zipfile.ZipFile(tmp_filepath, 'w') as zfile:
            for filename in os.listdir(from_dir):
                real_path = os.path.join(from_dir, filename)
                in_zip_path = filename

                zfile.write(real_path, in_zip_path)

        os.rename(tmp_filepath, filepath)
        log.logger.info('Archived: {}'.format(filepath))

    async def download(self, request_pool, name, skip_errors):
        """Download a volume by volname."""
        with TemporaryDirectory(prefix='cmdlr_') as tmpdir:
            vurl = self.comic.meta['volumes'][name]
            analyzer = self.comic.analyzer

            image_pool = ImageFetchPool(
                request_pool, self.comic, name, tmpdir, skip_errors)
            save_image = image_pool.get_save_image()

            request = request_pool.get_request(analyzer)
            loop = request_pool.loop

            async with request(url=vurl, **analyzer.volume_req_kwargs) as resp:
                await analyzer.save_volume_images(
                    resp, save_image, request=request, loop=loop)

            images_download_success = await image_pool.download()

            if images_download_success:
                self.__save_meta(tmpdir, name)
                self.__convert_to_cbz(tmpdir, name)
