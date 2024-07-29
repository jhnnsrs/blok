from blok.diff import compare_structures, ChangedDiff
from typing import List
from pathlib import Path
import os


class YamlFile:
    """Represents a yaml file"""

    def __init__(self, **values):
        self.values = values

    def __str__(self):
        return str(self.values)

    def diff(self, other: "YamlFile", path: str) -> List[str]:
        return compare_structures(self.values, other.values, path)

    @classmethod
    def is_representable_as(cls, path: Path):
        if path.suffix in [".yaml", ".yml"]:
            return True
        return False


class JSONFile:
    """Represents a yaml file"""

    def __init__(self, **values):
        self.values = values

    def __str__(self):
        return str(self.values)

    def diff(self, other: "YamlFile", path: str) -> List[str]:
        return compare_structures(self.values, other.values, path)

    @classmethod
    def is_representable_as(cls, path: Path):
        if path.suffix in [".json", ".json"]:
            return True
        return False


class Repo:
    """Represents a repository

    Repository will be cloned if it does not exist


    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def diff(self, other: "Repo", path: str) -> List[str]:
        if self.value != other.value:
            return [ChangedDiff(path, self.value, self.value)]
        return []

    def __eq__(self, other):
        if not isinstance(other, Repo):
            return False
        return self.value == other.value

    @classmethod
    def is_representable_as(cls, path: Path):
        if path.is_dir():
            if "__repo__.txt" in os.listdir(path):
                return True

        return False
