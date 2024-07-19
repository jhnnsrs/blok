from .builder import build_cli
from blok.registry import BlokRegistry
from blok.cli.magic_registry import MagicRegistry
import rich_click as click
from blok.renderers.click import RichRenderer
from blok.renderer import Renderer
from rich import get_console
import typing as t


def create_cli(*bloks, magic: bool = False, renderer: t.Optional[Renderer] = None):
    if not magic:
        reg = BlokRegistry(strict=True)
    else:
        reg = MagicRegistry("__blok__")

    for blok in bloks:
        reg.add_blok(blok)

    renderer = renderer or RichRenderer(get_console())

    build = build_cli(reg, renderer)

    @click.command()
    def inspect():
        """Inspect the bloks available in the python environment"""

        click.echo("Available bloks:")
        for blok in magic.bloks.values():
            click.echo(blok.get_blok_name())

    @click.group()
    @click.pass_context
    def cli(ctx):
        """Welcome to blok! A tool for building and managing docker-compose projects.

        Blok utilized your locally installed projects to build and manage docker-compose projects.
        Projects can register bloks into the blok registry using the __blok__ magic method.
        For more information, visit [link=https://arkitekt.live/bloks]https://arkitekt_next.live/bloks[/link]
        """

        pass

    cli.add_command(build, "build")
    cli.add_command(inspect, "inspect")

    return cli
