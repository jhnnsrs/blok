from pathlib import Path
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
from blok.utils import get_prepended_values, remove_empty_dicts
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


def filter_bloks(
    bloks: List[Blok],
    discard_bloks: Optional[List[str]] = None,
    prefer_bloks: Optional[List[str]] = None,
):
    if discard_bloks:
        bloks = [blok for blok in list if blok.get_blok_name() not in discard_bloks]

    if prefer_bloks:
        prefered_blok = [blok for blok in list if blok.get_blok_name() in prefer_bloks]
        if prefered_blok:
            bloks = prefered_blok

    return bloks


def initialize_blok_with_dependencies(
    blok: Blok,
    registry: BlokRegistry,
    discard_bloks: list,
    prefer_bloks: list,
    kwargs: dict,
):
    """
    Given a blok name, initialize the necessary modules including its dependencies.

    :param blok_name: The name of the blok to initialize.
    """
    initialied_bloks = OrderedDict()

    def initialize_service_as_blok_recursive(service_name, causing_blok):
        if service_name in initialied_bloks:
            return

        try:
            potential_bloks = registry.get_bloks_for_dependency(service_name)
        except KeyError:
            raise DependencyNotFoundError(
                f"Could not find blok for key {service_name}. This might happen if you have not registered a blok fullfilling the interface Causing Blok: {causing_blok}"
            )

        filtered_bloks = filter_bloks(
            potential_bloks, discard_bloks=discard_bloks, prefer_bloks=prefer_bloks
        )

        if not filtered_bloks:
            raise DependencyNotFoundError(
                f"Could not find blok for key {service_name}. This might happen if you have not registered a blok fullfilling the interface"
            )

        if len(filtered_bloks) > 1:
            raise TooManyBlokFoundError(
                f"Multiple bloks found for key {service_name}. This might happen if you have registered multiple bloks fullfilling the same interface. Just discard the ones you do not need. Or set your prefered bloks. Here are the bloks found: {filtered_bloks}"
            )

        chosen_blok = filtered_bloks[0]

        initialied_bloks[service_name] = chosen_blok

        for dependency in chosen_blok.get_dependencies():
            initialize_service_as_blok_recursive(dependency, chosen_blok)

        blok_dependencies = {
            key: initialied_bloks[key] for key in chosen_blok.get_dependencies()
        }

        try:
            chosen_blok.init(
                InitContext(
                    dependencies=blok_dependencies,
                    kwargs=get_prepended_values(kwargs, chosen_blok.get_blok_name()),
                )
            )
        except Exception as e:
            raise BlokInitializationError(
                f"Failed to initialize blok {chosen_blok.get_blok_name()}"
            ) from e

    for blok_key in blok.get_dependencies():
        initialize_service_as_blok_recursive(blok_key, blok)

    blok_dependencies = {key: initialied_bloks[key] for key in blok.get_dependencies()}

    try:
        blok.init(
            InitContext(
                dependencies=blok_dependencies,
                kwargs=get_prepended_values(kwargs, blok.get_blok_name()),
            )
        )
    except Exception as e:
        raise BlokInitializationError(
            f"Failed to initialize starting blok {blok.get_blok_name()}"
        ) from e

    return initialied_bloks


def entrypoint(
    registry: BlokRegistry, renderer: Renderer, blok_file_name: str, **kwargs
):
    console = get_console()
    path = kwargs.pop("path")
    blok_name = kwargs.pop("blok")
    yes = kwargs.pop("yes", False)

    dry = kwargs.pop("dry", False)

    discard_bloks = kwargs.pop("discard_bloks", None)
    prefer_bloks = kwargs.pop("prefer_bloks", None)

    blok = registry.get_blok(blok_name)
    blok.entry(renderer)

    initialized = initialize_blok_with_dependencies(
        blok, registry, discard_bloks, prefer_bloks, kwargs
    )

    pane = create_dependency_resolutions_pane(initialized)
    console.print(pane)

    files = {}

    context = ExecutionContext(
        docker_compose=NestedDict({"services": {}, "networks": {}}),
        file_tree=NestedDict(files),
    )

    for key, service in initialized.items():
        try:
            service.build(context)
        except Exception as e:
            raise BlokInitializationError(
                f"Failed to initialize blok {blok.get_blok_name()} for service {key}"
            ) from e

        # TODO: Validate context?

    # This would generate this are you okay?

    compose_dict = remove_empty_dicts(context.docker_compose)

    print_all = False

    if print_all:
        tree = construct_file_tree("DockerCompose", compose_dict)
        get_console().print(tree)

        tree = construct_file_tree("Files", context.file_tree)
        get_console().print(tree)

    old_files = create_structure_from_files_and_folders(path)

    diffs = compare_structures(
        old_files,
        {
            **context.file_tree,
            "docker-compose.yml": YamlFile(**compose_dict),
        },
    )

    if not diffs:
        get_console().print("No differences found")
        get_console().print("Exiting")

    else:
        tree = construct_diff_tree(diffs)
        get_console().print(tree)

    # Generate docker compose file

    if yes or click.confirm("Do you want to generate the files?"):
        os.makedirs(path, exist_ok=True)

        docker_compose_file_path = Path(path) / "docker-compose.yml"

        with open(docker_compose_file_path, "w") as f:
            yaml.dump(compose_dict, f, yaml.SafeDumper, indent=3)

        print(f"Generated docker-compose file at {docker_compose_file_path}")

        # Generate file tree

        # Generate files and folders
        create_files_and_folders(Path(path), context.file_tree)

        with open(Path(path) / blok_file_name, "w") as f:
            yaml.dump(kwargs, f, yaml.SafeDumper)
