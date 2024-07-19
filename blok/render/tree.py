from blok.diff import Diff, ChangedDiff, AddedKeyDiff, RemoveKeyDiff, ListChangedDiff
from typing import List
from blok.tree.models import YamlFile, Repo


def construct_diff_tree(diffs: List[Diff]):
    from rich.tree import Tree

    tree = Tree("Differences")

    for diff in diffs:
        if isinstance(diff, ChangedDiff):
            tree.add(
                f"[yellow]Will Modify:[/yellow] {diff.path}\n  [red]Old:[/red] {diff.old}\n  [green]New:[/green] {diff.new}"
            )
        elif isinstance(diff, AddedKeyDiff):
            tree.add(f"[green]Will Add:[/green] {diff.path}/{diff.new}")
        elif isinstance(diff, RemoveKeyDiff):
            tree.add(f"[red]Will Discard (not delete):[/red] {diff.path}/{diff.old}")
        elif isinstance(diff, ListChangedDiff):
            tree.add(
                f"[yellow]List Modified:[/yellow] {diff.path}\n  [red]Item:[/red] {diff.old}"
            )

    return tree


def add_nodes(tree, structure):
    if not isinstance(structure, dict):
        return
    for key, value in structure.items():
        if isinstance(value, YamlFile):
            subtree = tree.add(f"[blue]{key} - YAML[/blue]")
            add_nodes(subtree, value.values)

        elif isinstance(value, Repo):
            # Create directory and clone repo
            subtree = tree.add(f"[red]{key}: {value} - REPO[/red]")
            # TODO: Clone repo

        elif isinstance(value, dict):
            # Add folder node and recurse into it
            subtree = tree.add(key)
            add_nodes(subtree, value)
        elif isinstance(value, list):
            # Add folder node and recurse into it
            subtree = tree.add(key)
            for item in value:
                if isinstance(item, dict):
                    add_nodes(subtree, item)
                else:
                    subtree.add(item)
        else:
            tree.add(f"{key}: [green]{value}[/green]")


def construct_file_tree(tree_name: str, structure: dict):
    from rich.tree import Tree

    tree = Tree(tree_name)
    add_nodes(tree, structure)
    return tree
