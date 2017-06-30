"""Cmdlr custom exception."""


class BaseCmdlrException(Exception):
    """Base cmdlr exception."""


class NoMatchAnalyzer(BaseCmdlrException):
    """The entry url not match any analyzer."""


class InvalidValue(BaseCmdlrException):
    """Got a invalid input value."""


class NotAComicDir(BaseCmdlrException):
    """This path not a comic dir."""


class ComicDirOccupied(BaseCmdlrException):
    """This path has already occupied by different comic or non comic data."""


class DuplicateComic(BaseCmdlrException):
    """Two dir in manage area has the same url target."""


class NoImagesFound(BaseCmdlrException):
    """Not found any images in one volume."""


class ExtraAnalyzersDirNotExists(BaseCmdlrException):
    """Extra analyzer dir already be set but not exists."""


class AnalyzerRuntimeError(BaseCmdlrException):
    """Other analyzer error."""
