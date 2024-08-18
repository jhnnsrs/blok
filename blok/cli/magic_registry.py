from blok.registry import BlokRegistry, Blok
from blok.utils import check_protocol_compliance
import importlib
import os
import traceback
import pkgutil
import typing as t


def load_and_call_get_blocks(module_name, rekuest_path, magic_path):
    try:
        spec = importlib.util.spec_from_file_location(
            f"{module_name}.{magic_path}", rekuest_path
        )
        rekuest_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rekuest_module)
        if hasattr(rekuest_module, "get_bloks"):
            bloks = rekuest_module.get_bloks()
            assert isinstance(bloks, list), "get_bloks must return a list"
            return bloks
        else:
            print(f"No get_bloks function in {module_name}.{magic_path}")
    except Exception as e:
        print(f"Failed to call get_bloks for {module_name}: {e}")
        traceback.print_exc()

    return []


def check_and_import_magic(magic_path: str):
    registered_bloks = []

    # Check local modules in the current working directory
    current_directory = os.getcwd()
    for item in os.listdir(current_directory):
        item_path = os.path.join(current_directory, item)
        if os.path.isdir(item_path) and os.path.isfile(
            os.path.join(item_path, "__init__.py")
        ):
            rekuest_path = os.path.join(item_path, f"{magic_path}.py")
            if os.path.isfile(rekuest_path):
                registered_bloks.extend(
                    load_and_call_get_blocks(item, rekuest_path, magic_path)
                )

    # Check installed packages
    for _, module_name, _ in pkgutil.iter_modules():
        try:
            module_spec = importlib.util.find_spec(module_name)
            if module_spec and module_spec.origin:
                rekuest_path = os.path.join(
                    os.path.dirname(module_spec.origin), f"{magic_path}.py"
                )
                if os.path.isfile(rekuest_path):
                    registered_bloks.extend(
                        load_and_call_get_blocks(module_name, rekuest_path, magic_path)
                    )

        except Exception as e:
            print(f"Failed to call get_bloks for installed package {module_name}: {e}")
            traceback.print_exc()

    return registered_bloks


class MagicRegistry(BlokRegistry):
    def __init__(self, magic_path: str, **kwargs):
        super().__init__(**kwargs)
        self.magic_path = magic_path

    def load_magic(self):
        registered_blocks = check_and_import_magic(self.magic_path)
        for blok in registered_blocks:
            self.add_blok(blok)
