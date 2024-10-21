import typing as t
from blok.errors import ProtocolNotCompliantError
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


def check_service_compliance(cls: t.Type, service: t.Type) -> bool:
    protocol_methods = {
        name
        for name in dir(service)
        if getattr(service, name, None)
        and not name.startswith("_")
        and not name == "get_blok_service_meta"
    }

    instance_methods = {
        name
        for name in dir(cls)
        if getattr(cls, name, None) and not name.startswith("_")
    }
    missing_methods = protocol_methods - instance_methods
    if missing_methods:
        raise ProtocolNotCompliantError(
            f"Class {cls.__name__} does not implement "
            + f"the following methods required by {service.__name__}"
            + ":\n\t-"
            + "\n\t -".join(missing_methods)
        )

    return True


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


def get_cleartext_deps(blok):
    dependencies = blok.get_blok_meta().dependencies
    cleartext_deps = []

    return dependencies
