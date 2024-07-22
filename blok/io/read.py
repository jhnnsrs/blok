import os
from pathlib import Path
from blok.tree.models import YamlFile, Repo
import yaml


def create_structure_from_files_and_folders(base_path, omit: list[str] | None = None):
    if omit is None:
        omit = []
    structure = {}

    def process_directory(current_path, current_dict):
        for root, dirs, files in os.walk(current_path):
            rel_path = Path(root).relative_to(base_path)
            if ".git" in files:
                # Skip this directory as it contains a git repository
                continue

            # Update current_dict to point to the correct level in the structure
            temp_dict = current_dict
            for part in rel_path.parts:
                temp_dict = temp_dict.setdefault(part, {})

            for dir_name in dirs:
                temp_dict[dir_name] = {}

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
                        temp_dict[file_name] = YamlFile(**yaml_content)
                    else:
                        try:
                            content_decoded = content.decode()
                            temp_dict[file_name] = content_decoded
                        except UnicodeDecodeError:
                            temp_dict[file_name] = content
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")

            # Recursively process subdirectories
            for dir_name in dirs:
                process_directory(Path(root) / dir_name, temp_dict[dir_name])
            break  # Prevent further recursion by os.walk since we manually process subdirectories

    process_directory(base_path, structure)
    return structure