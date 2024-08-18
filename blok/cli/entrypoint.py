from dataclasses import asdict
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
from blok.blok import Command, Dependency, ExecutionContext, InitContext
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
import inquirer


def filter_bloks(
    bloks: List[Blok],
    discard_bloks: Optional[List[str]] = None,
    prefer_bloks: Optional[List[str]] = None,
):
    if discard_bloks:
        bloks = [
            blok for blok in bloks if blok.get_blok_meta().name not in discard_bloks
        ]

    if prefer_bloks:
        prefered_blok = [
            blok for blok in bloks if blok.get_blok_meta().name in prefer_bloks
        ]
        if prefered_blok:
            bloks = prefered_blok
    return bloks


def traverse_command_tree(nested: NestedDict):
    for key, value in nested.items():
        if isinstance(value, NestedDict):
            yield from traverse_command_tree(value)
        else:
            assert isinstance(value, Command), f"Expected Command but got {value}"
            yield key, asdict(value)


def initialize_blok_with_dependencies(
    blok: Blok,
    registry: BlokRegistry,
    renderer: Renderer,
    discard_bloks: list,
    prefer_bloks: list,
    kwargs: dict,
    with_optionals: list | None = None,
    run=False,
    interactive: bool = True,

):
    """
    Given a blok name, initialize the necessary modules including its dependencies.

    :param blok_name: The name of the blok to initialize.
    """
    initialied_bloks = OrderedDict()
    chosen_optionals = set()

    def initialize_service_as_blok_recursive(dep: Dependency, causing_blok: Blok):
        service_name = dep.service
        is_optional = dep.optional
        if is_optional:
            # If we have provided a list of optionals and this is not in the list, we skip
            if run:
                if service_name not in with_optionals:
                    return
                else:
                    chosen_optionals.add(service_name)
                    pass      
            else:
                # If we have not provided a list of optionals, we ask the user
                if not renderer.confirm(f"{causing_blok.get_blok_meta().name} can optional use  {service_name} {dep.description if dep.description else ''}: Would you like to initialize it?"):
                    
                    return
                
                chosen_optionals.add(service_name)

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
            if interactive:
                questions = [
                    inquirer.List(
                        "blok",
                        message=f"Which blok would you like to resolve {service_name}",
                        choices=[x.get_blok_meta().name for x in filtered_bloks],
                    ),
                ]
                answers = inquirer.prompt(questions)
                if not answers:
                    raise click.ClickException("User cancelled")
                answer = answers["blok"]
                chosen_blok = [
                    blok
                    for blok in filtered_bloks
                    if blok.get_blok_meta().name == answer
                ][0]

            else:
                raise TooManyBlokFoundError(
                    f"Multiple bloks found for key {service_name}. This might happen if you have registered multiple bloks fullfilling the same interface. Just discard the ones you do not need. Or set your prefered bloks. Here are the bloks found: {filtered_bloks}"
                )

        else:
            chosen_blok = filtered_bloks[0]

        initialied_bloks[service_name] = chosen_blok

        for dependency in get_cleartext_deps(chosen_blok):
            initialize_service_as_blok_recursive(dependency, chosen_blok)

        blok_dependencies = {
            dep.service: initialied_bloks[dep.service] for dep in get_cleartext_deps(chosen_blok)
        }

        try:
            chosen_blok.preflight(
                InitContext(
                    dependencies=blok_dependencies,
                    kwargs=get_prepended_values(
                        kwargs, chosen_blok.get_blok_meta().name
                    ),
                )
            )
        except Exception as e:
            raise BlokInitializationError(
                f"Failed to initialize blok {chosen_blok.get_blok_meta().name}"
            ) from e

    for dep in get_cleartext_deps(blok):
        initialize_service_as_blok_recursive(dep, blok)

    blok_dependencies = {dep.service: initialied_bloks[key.service] for key in get_cleartext_deps(blok)}
    try:
        blok.preflight(
            InitContext(
                dependencies=blok_dependencies,
                kwargs=get_prepended_values(kwargs, blok.get_blok_meta().name),
            )
        )
    except Exception as e:
        raise BlokInitializationError(
            f"Failed to initialize starting blok {blok.get_blok_meta().name}"
        ) from e

    return initialied_bloks, chosen_optionals


def entrypoint(
    registry: BlokRegistry, renderer: Renderer, blok_file_name: str, **kwargs
):
    try:
        console = get_console()
        path = kwargs.pop("path")
        blok_name = kwargs.pop("blok")
        yes = kwargs.pop("yes", False)

        dry = kwargs.pop("dry", False)

        discard_bloks = kwargs.pop("discard_bloks", None)
        prefer_bloks = kwargs.pop("use_bloks", None)
        print(prefer_bloks)
        run = kwargs.pop("run", False)
        print(run)
        with_optionals = kwargs.pop("with_optionals", None)
        print(with_optionals)

        blok = registry.get_blok(blok_name)
        blok.entry(renderer)
        initialized, chosen_optionals = initialize_blok_with_dependencies(
            blok, registry, renderer, discard_bloks, prefer_bloks, kwargs, with_optionals, run
        )

        pane = create_dependency_resolutions_pane(initialized)
        console.print(pane)

        # In the future we can use the same context to build the bloks
        kwargs["use_bloks"] = [
            blok.get_blok_meta().name for blok in initialized.values()
        ]
        print(chosen_optionals)
        kwargs["with_optionals"] = list(chosen_optionals)
        kwargs["run"] = True

        files = {}

        context = ExecutionContext(
            docker_compose=NestedDict({"services": {}, "networks": {}}),
            file_tree=NestedDict(files),
            install_commands=NestedDict(),
            up_commands=NestedDict(),
        )

        for key, service in initialized.items():
            try:
                service.build(context)
            except Exception as e:
                raise BlokInitializationError(
                    f"Failed to initialize blok {blok.get_blok_name()} for service {key}"
                ) from e

            # TODO: Validate context?

        # Finally build the blok
        try:
            blok.build(context)
        except Exception as e:
            raise BlokInitializationError(
                f"Failed to initialize blok {blok.get_blok_name()} for service {key}"
            ) from e

        # This would generate this are you okay?

        compose_dict = remove_empty_dicts(context.docker_compose)

        print_all = False

        if print_all:
            tree = construct_file_tree("DockerCompose", compose_dict)
            renderer.print(tree)

            tree = construct_file_tree("Files", context.file_tree)
            renderer.print(tree)

        old_files = create_structure_from_files_and_folders(path)

        new_yaml_body = {
            "config": kwargs,
            "resolved_blocks": {
                key: value.get_blok_meta().name for key, value in initialized.items()
            },
            "initialized_order": list(
                i.get_blok_meta().name for i in initialized.values()
            ),
            "with_optionals": list(chosen_optionals),
            "install_commands": dict(traverse_command_tree(context.install_commands)),
            "up_commands": dict(traverse_command_tree(context.up_commands)),
        }

        diffs = compare_structures(
            old_files,
            {
                **context.file_tree,
                "docker-compose.yml": YamlFile(**compose_dict),
                "__blok__.yml": YamlFile(**new_yaml_body),
            },
        )

        if not diffs:
            renderer.print("No differences found")

        else:
            tree = construct_diff_tree(diffs)
            renderer.print(tree)

        # Generate docker compose file

        kwargs["run"] = True
        if yes or renderer.confirm("Do you want to generate the files?"):
            os.makedirs(path, exist_ok=True)

            docker_compose_file_path = Path(path) / "docker-compose.yml"

            with open(docker_compose_file_path, "w") as f:
                yaml.dump(compose_dict, f, yaml.SafeDumper, indent=3)

            renderer.print(f"Generated docker-compose file at {docker_compose_file_path}")

            # Generate file tree

            # Generate files and folders
            create_files_and_folders(Path(path), context.file_tree)

        with open(Path(path) / blok_file_name, "w") as f:
            yaml.dump(
                new_yaml_body,
                f,
                yaml.SafeDumper,
            )

    except Exception as e:
        print(traceback.format_exc())
        raise click.ClickException(str(e)) from e
