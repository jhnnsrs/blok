import os
from pathlib import Path
from blok.tree.models import JSONFile, YamlFile, Repo
import yaml
import json
import subprocess


def create_files_and_folders(base_path, structure, git_command: str = "git"):
    for key, value in structure.items():
        current_path = base_path / key
        if isinstance(value, YamlFile):
            # Create file and write yaml
            with current_path.open("w") as file:
                yaml.dump(value.values, file, yaml.SafeDumper)

        elif isinstance(value, JSONFile):
            # Create file and write yaml
            with current_path.open("w") as file:
                json.dump(value.values, file, indent=2)

        elif isinstance(value, Repo):
            # Create directory and clone repo
            current_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(f"{git_command} clone {value} {current_path}", shell=True)
            # TODO: Clone repo

        elif isinstance(value, dict):
            # Create directory and recurse into it
            current_path.mkdir(parents=True, exist_ok=True)
            create_files_and_folders(current_path, value)
        else:
            # Create file and write bytes if any
            if value is not None:
                if isinstance(value, str):
                    value = value.encode()

                assert isinstance(
                    value, bytes
                ), f"Expected bytes for file content, got {type(value)}"

                with current_path.open("wb") as file:
                    if value is not None:
                        file.write(value)

            else:
                raise ValueError("Value cannot be None")
