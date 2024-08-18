from rich.panel import Panel
from rich.tree import Tree
from typing import Dict
from blok.blok import Blok


def create_welcome_pane(path, blok):
    return Panel(
        f"We will generate your new setup here: {path} using the {blok} blok",
        expand=False,
        title="Welcome to Blok!",
        style="bold magenta",
    )


def create_dependency_resolutions_pane(dep_map: Dict[str, Blok]):
    tree = Tree("Dependency Resolutions")

    for key, value in dep_map.items():
        tree.add(f"[bold]{key}[/bold] resolved to {value.get_blok_meta().name}")

    return Panel(
        tree,
        expand=False,
        title="Dependency Resolutions",
        style="magenta",
    )
