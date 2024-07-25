from blok.registry import BlokRegistry
import rich_click as click
import typing as t
from pathlib import Path
import yaml
from functools import partial
import os
from blok.cli.up.entrypoint import entrypoint
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
        raise click.ClickException("No blok configuration file found")

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

    func = click.argument(
        "path",
        type=click.Path(readable=True, writable=True),
        default=lambda: Path(os.getcwd()),
        callback=partial(configure, config_file_name),
    )(func)
    func = click.option(
        "--yes",
        "-y",
        is_flag=True,
        default=False,
    )(func)
    func = click.option(
        "--select",
        "-s",
        type=str,
        default=lambda: list(),
        multiple=True,
    )(func)
    func = click.option(
        "--no-docker",
        "-nd",
        type=bool,
        default=False,
        is_flag=True,
    )(func)

    func = click.command()(func)

    return func


def build_up_cli(
    blok_registry: BlokRegistry,
    renderer: Renderer,
    config_file_name: str = "__blok__.yml",
):
    return wrap_builder(entrypoint, blok_registry, renderer, config_file_name)
