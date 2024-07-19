from typing import List, runtime_checkable, Protocol
import typing as t
from blok.models import CLIOption, NestedDict
from blok.service import Service
from dataclasses import dataclass
from blok.renderer import Renderer


@dataclass
class InitContext:
    dependencies: t.Dict[str, "Blok"]
    kwargs: t.Dict[str, t.Any]


@dataclass
class ExecutionContext:
    docker_compose: NestedDict
    file_tree: NestedDict


@runtime_checkable
class Blok(Protocol):
    def get_blok_name(self) -> str: ...

    def get_identifier(self) -> str: ...

    def get_dependencies(self) -> List[str]: ...

    def entry(self, render: Renderer): ...

    def build(self, context: ExecutionContext): ...
    def init(self, init: InitContext): ...
    def get_options(self, name: str) -> List[CLIOption]: ...


def blok(
    service_identifier: t.Union[str, Service],
    options: t.Optional[List[CLIOption]] = None,
    dependencies: t.Optional[List[str]] = None,
):
    def decorator(cls):
        cls.__service_identifier__ = service_identifier if isinstance(service_identifier, str) else service_identifier.get_identifier()
        cls.__dependencies__ = dependencies or []
        cls.__options__ = options or []

        if not hasattr(cls, "get_blok_name"):
            cls.get_blok_name = lambda self: self.__class__.__name__.lower().replace("blok", "")

        if not hasattr(cls, "get_identifier"):
            cls.get_identifier = lambda self: self.__service_identifier__

        if not hasattr(cls, "get_dependencies"):
            cls.get_dependencies = lambda self: self.__dependencies__

        if not hasattr(cls, "get_options"):
            cls.get_options = lambda self: self.__options__

        if not hasattr(cls, "entry"):
            cls.entry = lambda self, renderer: None

        if not hasattr(cls, "build"):
            cls.init = lambda self, context: None

        if not hasattr(cls, "init"):
            cls.init = lambda self, context: None

        return cls

    return decorator
