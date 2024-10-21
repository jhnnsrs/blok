from dataclasses import dataclass
import typing as t


@dataclass
class Panel:
    content: str
    title: str
    style: str = "bold magenta"
    expand: bool = False


Scene = Panel


@t.runtime_checkable
class Renderer(t.Protocol):
    def render(self, scene: Scene) -> None: ...

    def ask(self, question: str) -> str: ...

    def confirm(self, question: str) -> bool: ...

    def print(self, *args, **kwargs) -> None: ...
