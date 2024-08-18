from blok.registry import BlokRegistry
import rich_click as click
import typing as t
from pathlib import Path
import yaml
from functools import partial
import os
from blok.cli.entrypoint import entrypoint
from blok.renderer import Renderer


def configure(config_file_name: str, ctx, param, filename):
    """Configures the context with the default map"""
    config_path = Path(filename) / config_file_name

    try:
        with open(config_path, "r") as f:
            cfg = yaml.load(f, yaml.SafeLoader)
        if not cfg:
            cfg = {}
        ctx.default_map = cfg.get("config")
        ctx.obj = cfg
    except FileNotFoundError:
        pass

    return filename


def reconfigure(ctx, param, flag):
    """Configures the context with the default map"""
    if flag:
        print("Forcing reconfiguration")
        ctx.default_map = {}
    return flag


def wrap_builder(
    builder_func: t.Callable,
    blok_registry: BlokRegistry,
    renderer: Renderer,
    config_file_name: str,
):
    def wrapped_builder(*args, **kwargs):
        "Builds a docker-compose project utilizing the bloks available in the python environment and locally" ""
        return builder_func(blok_registry, renderer, config_file_name, *args, **kwargs)

    func = wrapped_builder
    func = click.option(
        "--dry",
        "-dry",
        is_flag=True,
        default=False,
    )(func)
    func = click.option(
        "--run",
        "-r",
        default=False,
        required=False,
    )(func)
    func = click.option(
        "--use-bloks",
        "-b",
        type=click.Choice(blok_registry.bloks.keys()),
        multiple=True,
        default=list(blok_registry.bloks.keys()),
        help="Bloks to use",
    )(func)
    func = click.option(
        "--discard_bloks",
        "-d",
        type=click.Choice(blok_registry.bloks.keys()),
        multiple=True,
        default=[],
        help="Bloks to discard in the build",
    )(func)
    func = click.option(
        "--with-optionals",
        "-o",
        type=click.Choice(blok_registry.dependency_resolver.keys()),
        multiple=True,
        default=None,
        required=False,
        help="Optional services to include",
    )(func)
    func = click.option(
        "--force",
        "-f",
        is_flag=True,
        default=False,
        callback=reconfigure,
    )(func)

    for option in blok_registry.get_click_options():
        func = option(func)

    func = click.argument(
        "path",
        type=click.Path(readable=True, writable=True),
        default=lambda: Path(os.getcwd()),
        callback=partial(configure, config_file_name),
    )(func)
    func = click.argument("blok", type=click.Choice(blok_registry.bloks.keys()))(func)
    func = click.option(
        "--force",
        "-f",
        is_flag=True,
        default=False,
        callback=reconfigure,
    )(func)
    func = click.option(
        "--yes",
        "-y",
        is_flag=True,
        default=False,
    )(func)

    func = click.command()(func)

    return func


def build_cli(
    blok_registry: BlokRegistry,
    renderer: Renderer,
    config_file_name: str = "__blok__.yml",
):
    return wrap_builder(entrypoint, blok_registry, renderer, config_file_name)
