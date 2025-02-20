from blok.cli.install.builder import build_install_cli
from blok.cli.up.builder import build_up_cli
from .builder import build_cli
from blok.registry import BlokRegistry
from blok.cli.magic_registry import MagicRegistry
import rich_click as click
from blok.renderers.click import RichRenderer
from blok.renderer import Renderer
from rich import get_console
import typing as t


def make_cli(registry: BlokRegistry, renderer: Renderer):
    build = build_cli(registry, renderer)
    install = build_install_cli(registry, renderer)
    up = build_up_cli(registry, renderer)

    @click.command()
    def inspect():
        """Inspect the bloks available in the python environment"""

        click.echo("Available bloks:")
        for blok in registry.bloks.values():
            click.echo(blok.get_blok_name() + "\t\t\t" + blok.get_identifier())

    @click.group()
    @click.pass_context
    def cli(ctx):
        """Welcome to blok! A tool for building and managing docker-compose projects.

        Blok utilized your locally installed projects to build and manage docker-compose projects.
        Projects can register bloks into the blok registry using the __blok__ magic method.
        For more information, visit [link=https://arkitekt.live/bloks]https://arkitekt.live/bloks[/link]
        """

        pass

    cli.add_command(build, "build")
    cli.add_command(inspect, "inspect")
    cli.add_command(install, "install")
    cli.add_command(up, "up")
    return cli


def create_cli(*bloks, magic: bool = False, renderer: t.Optional[Renderer] = None):
    if not magic:
        reg = BlokRegistry(strict=True)
    else:
        reg = MagicRegistry("__blok__")

    for blok in bloks:
        reg.add_blok(blok)

    renderer = renderer or RichRenderer(get_console())

    return make_cli(reg, renderer)
