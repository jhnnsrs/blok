class BlokError(Exception):
    """Base class for blok errors."""


class DependencyNotFoundError(BlokError):
    """Raised when a dependency is not found."""


class TooManyBlokFoundError(BlokError):
    """Raised when too many bloks are found."""


class BlokInitializationError(BlokError):
    """Raised when a blok fails to initialize."""


class BlokBuildError(BlokError):
    """Raised when a blok fails to build."""


class ProtocolError(BlokError):
    """Base class for protocol errors."""


class ProtocolNotCompliantError(BlokError):
    """Raised when an instance does not comply with a protocol."""
