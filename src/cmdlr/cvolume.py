"""Cmdlr volume related operations module."""

import os
import zipfile
import datetime as DT
import asyncio
import tempfile

from . import log
from . import yamla
from . import sessions
from .exception import NoImagesFound
from .exception import InvalidValue


def _get_volume_cbzpath(comic_path, comic_name, volume_name):
    """Get colume cbzpath."""
    volume_cbzname = _get_volume_cbzname(comic_name, volume_name)

    return os.path.join(comic_path, volume_cbzname)


def _convert_to_cbz(source_dirpath, comic_path, comic_name, volume_name):
    """Convert dir to cbz format."""
    volume_cbzpath = _get_volume_cbzpath(
        comic_path, comic_name, volume_name)
    volume_cbztmppath = volume_cbzpath + '.tmp'

    with zipfile.ZipFile(volume_cbztmppath, 'w') as zfile:
        for filename in os.listdir(source_dirpath):
            real_path = os.path.join(source_dirpath, filename)
            in_zip_path = filename

            zfile.write(real_path, in_zip_path)

    os.rename(volume_cbztmppath, volume_cbzpath)
    log.logger.info('Archived: {}'.format(volume_cbzpath))


def _save_image_binary(binary, page_num, ext, volume_dirpath):
    filename = '{page_num:04}{ext}'.format(page_num=page_num, ext=ext)
    filepath = os.path.join(volume_dirpath, filename)

    with open(filepath, mode='wb') as f:
        f.write(binary)


def _get_img_download(amgr, curl, tmpdirpath, cname, vname, skip_errors):
    request = sessions.get_request(curl)
    get_image_extension = amgr.get_match_analyzer(curl).get_image_extension

    async def img_download(page_num, url, **request_kwargs):
        try:
            async with request(url=url, **request_kwargs) as resp:
                ext = get_image_extension(resp)

                if not ext:
                    raise InvalidValue(
                        'Cannot determine file extension'
                        ' of "{}" content type.'.format(resp.content_type)
                    )

                binary = await resp.read()
                _save_image_binary(binary, page_num, ext, tmpdirpath)

                log.logger.info('Image Fetched: {}_{}_{:03}'.format(
                    cname, vname, page_num))

        except asyncio.CancelledError as e:
            pass

        except Exception as e:
            log.logger.error(
                'Image Fetch Failed : {}_{}_{:03} ({} => {}: {})'
                .format(cname, vname, page_num, url, type(e).__name__, e))

            if not skip_errors:
                raise e from None

    return img_download


def _get_save_image(loop, img_download):
    imgdl_tasks = []

    def save_image(page_num, *, url, **request_kwargs):
        task = loop.create_task(
            img_download(int(page_num), url, **request_kwargs))

        imgdl_tasks.append(task)

    return save_image, imgdl_tasks


def _cleanup_img_download_tasks(done, pending):
    """Cancel pending tasks & raise exception in img_download if exists."""
    for task in pending:
        task.cancel()

    for e in [task.exception() for task in done]:
        if e:
            raise e from None


def _save_volume_meta(dirpath, curl, vurl, comic_name, volume_name):
    filepath = os.path.join(dirpath, '.volume-meta.yaml')

    yamla.to_file(filepath, {
        'comic_url': curl,
        'volume_url': vurl,
        'comic_name': comic_name,
        'volume_name': volume_name,
        'archived_time': DT.datetime.now(DT.timezone.utc),
    })


def _get_volume_cbzname(comic_name, volume_name):
    """Get volume cbzname."""
    return '{}_{}.cbz'.format(comic_name, volume_name)


def get_not_downloaded_volnames(path, comic_name, im_volnames):
    """Get Not downloaded volumn names.

    Args:
        path (str): comic's local dir name.
        comic_name (str): comic's name.
        im_volnames (list of str): in-meta volume's names

    Returns:
        (list) volumn_name

    """
    fname_vname_map = {_get_volume_cbzname(comic_name, vname): vname
                       for vname in im_volnames}
    should_exists_fnames = fname_vname_map.keys()
    already_exists_fnames = set(os.listdir(path))

    return [fname_vname_map[sefname]
            for sefname in should_exists_fnames
            if sefname not in already_exists_fnames]


async def download_one_volume(
        amgr, path, curl, comic_name, vurl, volume_name, skip_errors, loop):
    """Download single one volume.

    Args:
        amgr (AnalyzerManager): analyzer manager
        path (str): comic's local dir path
        curl (str): comic's entry url
        comic_name (str): comic's title
        vurl (str): volume's url
        volume_name (str): volume's title
        skip_errors (bool):
            should continue work when some images download fail?
        loop (asyncio.AbstractEventLoop): the aio event loop
    """
    with tempfile.TemporaryDirectory(prefix='cmdlr_') as tmpdirpath:
        img_download = _get_img_download(
            amgr, curl, tmpdirpath, comic_name, volume_name, skip_errors)
        save_image, imgdl_tasks = _get_save_image(loop, img_download)

        request = sessions.get_request(curl)

        volume_req_kwargs = amgr.get_match_analyzer(curl).volume_req_kwargs
        save_volume_images = amgr.get_match_analyzer(curl).save_volume_images

        async with request(url=vurl, **volume_req_kwargs) as resp:
            await save_volume_images(resp, save_image,
                                     request=request,
                                     loop=loop)

        if len(imgdl_tasks) == 0:
            raise NoImagesFound(
                'Not found any images in volume: [{}] => [{}] {}'
                .format(comic_name, volume_name, vurl))

        done, pending = await asyncio.wait(  # wait until first exception
            imgdl_tasks, loop=loop,
            return_when=asyncio.FIRST_EXCEPTION)
        _cleanup_img_download_tasks(done, pending)  # cleanup & raise

        if len(pending) == 0:
            _save_volume_meta(tmpdirpath, curl, vurl, comic_name, volume_name)
            _convert_to_cbz(tmpdirpath, path, comic_name, volume_name)
