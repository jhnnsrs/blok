import json
import os
from pathlib import Path
from blok.tree.models import JSONFile, YamlFile, Repo
import yaml
import subprocess


def create_structure_from_files_and_folders(base_path, omit: list[str] | None = None):
    if omit is None:
        omit = []
    structure = {}

    def get_repo_url(repo_path):
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Failed to get repo URL for {repo_path}: {e}")
            return None

    def process_directory(current_path, current_dict):
        for root, dirs, files in os.walk(current_path):
            rel_path = Path(root).relative_to(base_path)
            if ".git" in dirs:
                # Handle git repository
                repo_url = get_repo_url(root)
                if repo_url:
                    temp_dict = current_dict
                    for part in rel_path.parts:
                        temp_dict = temp_dict.setdefault(part, {})
                    temp_dict[".git"] = Repo(value=repo_url)
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

                file_path = Path(root) / file_name

                try:
                    with file_path.open("rb") as file:
                        content = file.read()

                    if file_name.endswith(".yaml") or file_name.endswith(".yml"):
                        content_decoded = content.decode()
                        yaml_content = yaml.safe_load(content_decoded)
                        temp_dict[file_name] = YamlFile(**yaml_content)
                    elif file_name.endswith(".json"):
                        content_decoded = content.decode()
                        json_content = json.loads(content_decoded)
                        temp_dict[file_name] = JSONFile(**json_content)
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
