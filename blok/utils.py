import typing as t
from blok.errors import ProtocolNotCompliantError
from blok.blok import Blok
import importlib


def check_allowed_module_string(value: str) -> bool:
    for char in value:
        if char not in "abcdefghijklmnopqrstuvwxyz_":
            return False

    return True


def check_protocol_compliance(instance: t.Type, protocol: t.Type) -> bool:
    protocol_methods = {
        name
        for name in dir(protocol)
        if getattr(protocol, name, None) and not name.startswith("_")
    }

    instance_methods = {
        name
        for name in dir(instance)
        if getattr(instance, name, None) and not name.startswith("_")
    }

    missing_methods = protocol_methods - instance_methods

    if missing_methods:
        raise ProtocolNotCompliantError(
            f"Instance of {type(instance).__name__} does not implement "
            + f"the following methods required by {protocol.__name__}"
            + ":\n\t-"
            + "\n\t -".join(missing_methods)
        )

    return True


def lazy_load_blok(path) -> Blok:
    # lazily loading a command, first get the module name and attribute name
    import_path = path

    blok_name = "_".join(import_path.split("."))
    modname, cmd_object_name = import_path.rsplit(".", 1)
    # do the import
    mod = importlib.import_module(modname)
    # get the Command object from that module
    cmd_object = getattr(mod, cmd_object_name)
    # check the result to make debugging easier

    blok = cmd_object()
    check_protocol_compliance(blok, Blok)

    return blok_name, blok


def remove_empty_dicts(d):
    if not isinstance(d, dict):
        return d

    non_empty_items = {}
    for key, value in d.items():
        if isinstance(value, dict):
            cleaned_dict = remove_empty_dicts(value)
            if cleaned_dict:  # Only add non-empty dictionaries
                non_empty_items[key] = cleaned_dict
        else:
            non_empty_items[key] = value

    return non_empty_items


def get_prepended_values(kwargs: t.Dict[str, t.Any], blok_name: str):
    prepended = {
        key.split("_", 1)[1]: value
        for key, value in kwargs.items()
        if key.startswith(blok_name)
    }

    return prepended
