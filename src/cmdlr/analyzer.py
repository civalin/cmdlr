"""Cmdlr base analyzer implement."""

import importlib
from abc import ABCMeta
from abc import abstractmethod

from .merge import merge_dict

from .exception import AnalyzerRuntimeError


ANALYZERS_PKGPATH = 'cmdlr.analyzers'


class _BaseAnalyzer(metaclass=ABCMeta):
    """Internal operation for BaseAnalyzer."""

    def __init__(self, pref, *args, **kwargs):
        """Init this analyzer."""
        if 'system' in self.default_pref:
            raise AnalyzerRuntimeError(
                'key "system" not allow in default_pref" ({})'
                .format(self.name)
            )

        self.current_pref = merge_dict(self.default_pref, pref)
        self.config = self.to_config(self.current_pref)

    @property
    def name(self):
        """Get analyzer's name."""
        # the analyzer module name must under this path:
        #    'cmdlr.analyzers.<analyzer name>.<maybe exist...>'
        return self.__class__.__module__.split('.')[2]

    @property
    def desc(self):
        """Get analyzer's desc."""
        module_name = '.'.join([ANALYZERS_PKGPATH, self.name])
        module = importlib.import_module(module_name)

        return module.__doc__


class BaseAnalyzer(_BaseAnalyzer):
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

    default_pref = {}
    default_request_kwargs = {
        'method': 'GET',
    }

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
        """Pre-processing user's 'pref' to 'self.config' for ease to use."""
        return pref
