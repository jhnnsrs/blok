from blok.cli.builder import build_cli
from blok.cli.magic_registry import MagicRegistry
from blok.renderers.click import RichRenderer
from rich import get_console
import rich_click as click

magic = MagicRegistry("__blok__")

magic.load_magic()

renderer = RichRenderer(get_console())

WELCOME_MESSAGE = """"
Welcome to blok! A tool for building and managing docker-compose projects.

Blok utilized your locally installed projects to build and manage docker-compose projects.
Projects can register bloks into the blok registry using the __blok__ magic method.
For more information, visit [link=https://arkitekt.live/bloks]https://arkitekt_next.live/bloks[/link]

"""

LOGO = r"""
 ____   _       ___   __  _ 
|    \ | |     /   \ |  |/ ]
|  o  )| |    |     ||  ' / 
|     || |___ |  O  ||    \ 
|  O  ||     ||     ||     \
|     ||     ||     ||  .  |
|_____||_____| \___/ |__|\_|                             
"""

ERROR_EPILOGUE = "To find out more, visit [link=https://arkitekt.live/bloks]https://arkitekt.live/bloks[/link]"


click.rich_click.HEADER_TEXT = LOGO + "\n"
click.rich_click.ERRORS_EPILOGUE = ERROR_EPILOGUE
click.rich_click.USE_RICH_MARKUP = True


build = build_cli(magic, renderer)


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
