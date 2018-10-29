"""The steps of book mission."""


def _get_download_step():
    """Build a download step."""
    async def download_step(comic, skip_errors, request_pool, *args):
        await comic.download(
            request_pool,
            skip_errors,
        )

    return download_step


def _get_new_comic_step():
    """Build a new comic step.

    Return to:
        --> download_step
    """
    async def new_comic_step(url, skip_errors, request_pool, cmgr, *args):
        comic = await cmgr.new_comic(request_pool, url)

        return comic, skip_errors, request_pool

    return new_comic_step


def _get_update_meta_step():
    """Build a update meta step.

    Return to:
        --> download_step
    """
    async def update_meta_step(comic, skip_errors, request_pool, *args):
        await comic.update_meta(request_pool)

        return comic, skip_errors, request_pool

    return update_meta_step


def get_url_steps(ctrl):
    """Get a url steps series."""
    download = ctrl.get('download')

    steps = []
    steps.append(_get_new_comic_step())

    if download:
        steps.append(_get_download_step())

    return steps


def get_comic_steps(ctrl):
    """Get a comic steps series."""
    update_meta = ctrl.get('update_meta')
    download = ctrl.get('download')

    steps = []

    if update_meta:
        steps.append(_get_update_meta_step())

    if download:
        steps.append(_get_download_step())

    return steps
