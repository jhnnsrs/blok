from pathlib import Path
import traceback
from rich import get_console
import yaml
from blok.diff import compare_structures
from blok.io.read import create_structure_from_files_and_folders
from blok.io.write import create_files_and_folders
from blok.registry import BlokRegistry
from blok.errors import (
    DependencyNotFoundError,
    TooManyBlokFoundError,
    BlokBuildError,
    BlokInitializationError,
)
from blok.tree.models import YamlFile
from blok.utils import get_cleartext_deps, get_prepended_values, remove_empty_dicts
from blok.models import NestedDict
from blok.blok import ExecutionContext, InitContext
import rich_click as click
from rich.tree import Tree
from blok.render.tree import construct_file_tree, construct_diff_tree
from blok.render.panel import create_welcome_pane, create_dependency_resolutions_pane
import os
from blok.blok import Blok
from typing import List, Optional
from collections import OrderedDict
from blok.renderer import Renderer
import subprocess
from blok.renderer import Renderer, Panel


def secure_path_combine(x: Path, y: Path) -> Path:
    # Resolve the combined path

    mother_path = x.resolve()

    combined_path = (mother_path / y).resolve()

    # Check if the combined path is within the mother path
    if mother_path in combined_path.parents or mother_path == combined_path:
        return combined_path
    else:
        raise ValueError(
            "The user-defined path traverses out of the mother path. {} but requested {}".format(
                list(combined_path.parents), mother_path
            )
        )


@click.pass_context
def entrypoint(
    ctx: click.Context,
    registry: BlokRegistry,
    renderer: Renderer,
    blok_file_name: str,
    **kwargs,
):
    renderer.render(
        Panel(
            "Welcome to Blok!", title="Lets install this project", style="bold magenta"
        )
    )

    path = Path(kwargs.pop("path"))
    yes = kwargs.pop("yes", False)

    select = kwargs.pop("select", [])

    install_commands = ctx.obj.get("install_commands", {})

    selected_commands = []

    if select:
        for key in select:
            if key in install_commands:
                selected_commands.append(install_commands[key])
            else:
                raise click.ClickException(f"Command with key {key} not found")

    else:
        selected_commands = list(install_commands.values())

    if not selected_commands:
        raise click.ClickException("No install commands found in blok configuration")

    for command in selected_commands:
        if yes or renderer.confirm(
            "Run install command?: " + " ".join(command["command"])
        ):
            rel_path = secure_path_combine(path, Path(command["cwd"]))
            subprocess.run(" ".join(command["command"]), shell=True, cwd=rel_path)
