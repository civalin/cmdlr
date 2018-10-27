"""Cmdlr base analyzer implement."""

from abc import ABCMeta
from abc import abstractmethod


class BaseAnalyzer(metaclass=ABCMeta):
    """Base class of cmdlr analyzer."""

    # [Must override]

    entry_patterns = []  # a list of str or re.complie instances.

    @abstractmethod
    async def get_comic_info(self, *, url, request, loop):
        """Get comic info."""

    @abstractmethod
    async def save_volume_images(self, *, url, save_image, request, loop):
        """Call save_image to all image url with page number."""

    # [Optional]

    session_init_kwargs = {}
    default_pref = {}

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

    @staticmethod
    def to_config(pref):
        """Pre-processing user's config to internal format."""
        return pref

    # [Internal]: Don't touch it if it can be possible.

    def __init__(self, pref, *args, **kwargs):
        """Init this analyzer."""
        real_pref = {**self.default_pref, **pref}
        self.config = self.to_config(real_pref)
