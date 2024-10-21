from blok.renderer import Renderer, Panel
from rich import panel
import rich_click as click


class RichRenderer(Renderer):
    def __init__(self, console):
        self.console = console

    def render(self, scene: Panel) -> None:
        if isinstance(scene, Panel):
            self.console.print(
                panel.Panel(
                    scene.content,
                    title=scene.title,
                    style=scene.style,
                    expand=scene.expand,
                )
            )
            return

        raise NotImplementedError("Scene type not supported")

    def confirm(self, question: str) -> bool:
        return click.confirm(question)

    def ask(self, question: str) -> str:
        return click.prompt(question)

    def print(self, *args, **kwargs) -> None:
        self.console.print(*args, **kwargs)
