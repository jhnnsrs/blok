from dataclasses import asdict
import typing as t
from blok.blok import Blok
from blok.utils import (
    check_allowed_module_string,
    check_protocol_compliance,
)
import importlib


def lazy_load_blok(path) -> t.Tuple[str, Blok]:
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


class BlokRegistry:
    def __init__(self, strict: bool = False):
        self.services: t.Dict[str, Blok] = {}
        self.bloks: t.Dict[str, Blok] = {}
        self.dependency_resolver = {}
        self.strict = strict
        self.meta = {}

    def load_modules(self, modules: t.List[str]):
        for module in modules:
            self.load_module(module)

    def get_blok(self, blok_key: str):
        try:
            return self.bloks[blok_key]
        except KeyError:
            raise KeyError(f"Could not find blok with key {blok_key}")

    def get_bloks_for_dependency(
        self,
        identifier: str,
    ):
        blok_keys = self.get_module_name(identifier)
        return [self.get_blok(blok_key) for blok_key in blok_keys]

    def load_module(self, module: str, with_key: t.Optional[str] = None):
        key, blok = lazy_load_blok(module)
        self.add_blok(with_key or key, blok)

    def add_blok(self, blok: Blok):
        check_protocol_compliance(blok, Blok)
        meta = blok.get_blok_meta()

        if meta.name in self.bloks:
            if self.strict:
                raise KeyError(
                    f"Blok {meta.name} already exists. Cannot register it twice. Choose a different name."
                )
        else:
            self.dependency_resolver.setdefault(meta.service_identifier, []).append(
                meta.name
            )

        self.meta[meta.name] = meta

        self.bloks[meta.name] = blok

    def get_module_name(self, identifier):
        return self.dependency_resolver[identifier]

    def get_click_options(self):
        import rich_click as click

        integrated_options = []

        for blok_key, blok in self.bloks.items():
            for option in blok.get_options():
                params = asdict(option)

                subcommand = params.pop("subcommand")
                assert subcommand, "subcommand is required"
                assert check_allowed_module_string(
                    subcommand
                ), "subcommand must be a valid python variable name"

                integrated_option = click.option(
                    f"--{blok_key.replace('_', '-')}-{subcommand.replace('_', '-')}",
                    envvar=f"{blok_key.upper()}_{subcommand.upper()}",
                    **params,
                )

                integrated_options.append(integrated_option)

        return integrated_options
