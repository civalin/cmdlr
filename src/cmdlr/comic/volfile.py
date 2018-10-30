"""Comic volume file related function."""

import os
import zipfile
from datetime import datetime
from tempfile import TemporaryDirectory

from ..jsona import to_json_filepath
from ..log import logger
from .ifpool import ImageFetchPool


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
        filepath = os.path.join(dirpath, '.volume-meta.json')

        to_json_filepath(
            {'comic_url': self.comic.url,
             'volume_url': self.comic.meta['volumes'][name],
             'comic_name': self.comic.meta['name'],
             'volume_name': name,
             'archived_time': datetime.utcnow()},
            filepath,
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
        logger.info('Archived: {}'.format(filepath))

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

            await analyzer.save_volume_images(url=vurl,
                                              request=request,
                                              save_image=save_image,
                                              loop=loop)

            images_download_success = await image_pool.download()

            if images_download_success:
                self.__save_meta(tmpdir, name)
                self.__convert_to_cbz(tmpdir, name)
