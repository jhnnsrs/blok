"""This module contains functionality for comparing
two docker-compose setups


"""

from collections.abc import Iterable
from typing import Protocol, List
from dataclasses import dataclass


class Diffable(Protocol):
    def diff(self, other: "Diffable", path: str) -> List[str]: ...


@dataclass
class ChangedDiff:
    path: str
    old: object
    new: object


@dataclass
class AddedKeyDiff:
    path: str
    new: str


@dataclass
class RemoveKeyDiff:
    path: str
    old: str


@dataclass
class ListChangedDiff:
    path: str
    old: str


Diff = ChangedDiff | AddedKeyDiff | RemoveKeyDiff | ListChangedDiff


def compare_structures(old_structure, new_structure, path=""):
    diffs = []

    old_keys = set(old_structure.keys())
    new_keys = set(new_structure.keys())

    for key in old_keys - new_keys:
        diffs.append(RemoveKeyDiff(path, key))

    for key in new_keys - old_keys:
        diffs.append(AddedKeyDiff(path, key))

    for key in old_keys & new_keys:
        old_value = old_structure[key]
        new_value = new_structure[key]

        if hasattr(old_value, "diff") and hasattr(new_value, "diff"):
            diffs.extend(old_value.diff(new_value, path + "/" + key))

        elif isinstance(old_value, dict) and isinstance(new_value, dict):
            diffs.extend(compare_structures(old_value, new_value, path + "/" + key))

        elif isinstance(old_value, (list, tuple)) and isinstance(
            new_value, (list, tuple)
        ):
            if len(old_value) != len(new_value):
                diffs.append(
                    ListChangedDiff(
                        path + "/" + key,
                        f"Length mismatch: {len(old_value)} != {len(new_value)}",
                    )
                )

            for i, (a, b) in enumerate(zip(old_value, new_value)):
                diffs.extend(
                    compare_structures(
                        {"a": a},
                        {"a": b},
                        path + "/" + key + "/" + str(i),
                    )
                )

        elif old_value != new_value:
            diffs.append(ChangedDiff(path + "/" + key, old_value, new_value))

    return diffs
