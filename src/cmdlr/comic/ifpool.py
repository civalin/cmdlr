"""Control the downloading of the images of a single volume."""

import os

import asyncio

from ..exception import NoImagesFound
from ..exception import InvalidValue
from ..log import logger


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

            logger.debug('Image Fetched: {}_{}_{:03}'.format(
                self.cname, self.vname, page_num))

    async def __save_image_error_process(self,
                                         page_num, url, **request_kwargs):
        try:
            await self.__save_image_op(page_num, url, **request_kwargs)

        except asyncio.CancelledError as e:
            pass

        except Exception as e:
            logger.error(
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
