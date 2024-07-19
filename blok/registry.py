from dataclasses import asdict
import typing as t
from blok.blok import Blok
from blok.utils import (
    check_allowed_module_string,
    check_protocol_compliance,
    lazy_load_blok,
)


class BlokRegistry:
    def __init__(self, strict: bool = False):
        self.services: t.Dict[str, Blok] = {}
        self.bloks: t.Dict[str, Blok] = {}
        self.dependency_resolver = {}
        self.strict = strict

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
        key, service = lazy_load_blok(module)
        self.add_blok(with_key or key, service)

    def add_blok(self, blok: Blok):
        check_protocol_compliance(blok, Blok)
        if blok.get_blok_name() in self.bloks:
            if self.strict:
                raise KeyError(
                    f"Blok {blok.get_blok_name()} already exists. Cannot register it twice. Choose a different name."
                )
        else:
            self.dependency_resolver.setdefault(blok.get_identifier(), []).append(
                blok.get_blok_name()
            )

        self.bloks[blok.get_blok_name()] = blok

    def get_module_name(self, identifier):
        return self.dependency_resolver[identifier]

    def get_click_options(self):
        import rich_click as click

        integrated_options = []

        for blok_key, blok in self.bloks.items():
            for option in blok.get_options():
                params = asdict(option)

                subcommand = params.pop("subcommand")
                show_default = params.pop("show_default", False)
                assert subcommand, "subcommand is required"
                assert check_allowed_module_string(
                    subcommand
                ), "subcommand must be a valid python variable name"

                integrated_option = click.option(
                    f"--{blok_key.replace('_', '-')}-{subcommand.replace('_', '-')}",
                    envvar=f"{blok_key.upper()}_{subcommand.upper()}",
                    show_default=True,
                    **params,
                )

                integrated_options.append(integrated_option)

        return integrated_options
