"""Cmdlr base analyzer implement."""

from abc import ABCMeta
from abc import abstractmethod


class BaseAnalyzer(metaclass=ABCMeta):
    """Base class of cmdlr analyzer."""

    session_init_kwargs = {}
    comic_req_kwargs = {}
    volume_req_kwargs = {}

    # should override by a list of str or re.complie instances.
    entry_patterns = []

    def __init__(self, customization):
        """Init this analyzer."""
        self.customization = customization

    @abstractmethod
    async def get_comic_info(self, resp, *, request, loop, **kwargs):
        pass

    @abstractmethod
    async def save_volume_images(self, resp, save_image,
                                 *, request, loop, **kwargs):
        pass

    def entry_normalizer(self, url):
        """Normalize all possible entry url to single one form."""
        return url

    def get_image_extension(self, resp):
        """Get image extension."""
        ctype = resp.content_type

        if ctype in ['image/jpeg', 'image/jpg']:
            return '.jpg'
        elif ctype == 'image/png':
            return '.png'
        elif ctype == 'image/gif':
            return '.gif'
        elif ctype == 'image/bmp':
            return '.bmp'
