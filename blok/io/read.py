import os
from pathlib import Path
from blok.tree.models import YamlFile, Repo
import yaml


def create_structure_from_files_and_folders(base_path, omit: list[str] | None = None):
    if omit is None:
        omit = []
    structure = {}

    for root, dirs, files in os.walk(base_path):
        rel_path = Path(root).relative_to(base_path)
        current_dict = structure

        if "__repo__.txt" in files:
            with (Path(root) / "__repo__.txt").open("r") as repo_file:
                repo_url = repo_file.read().strip()

            for part in rel_path.parts[:-1]:
                current_dict = current_dict.setdefault(part, {})
            current_dict[rel_path.parts[-1]] = Repo(repo_url)

        else:
            for part in rel_path.parts:
                current_dict = current_dict.setdefault(part, {})

        for dir_name in dirs:
            current_dict[dir_name] = {}

        for file_name in files:
            if omit and file_name in omit:
                continue

            if file_name == "__repo__.txt":
                continue

            file_path = Path(root) / file_name

            try:
                with file_path.open("rb") as file:
                    content = file.read()

                if file_name.endswith(".yaml") or file_name.endswith(".yml"):
                    content_decoded = content.decode()
                    yaml_content = yaml.safe_load(content_decoded)
                    current_dict[file_name] = YamlFile(**yaml_content)
                else:
                    try:
                        content_decoded = content.decode()
                        current_dict[file_name] = content_decoded
                    except UnicodeDecodeError:
                        current_dict[file_name] = content
            except Exception as e:
                print(f"Failed to read {file_path}")

    return structure
