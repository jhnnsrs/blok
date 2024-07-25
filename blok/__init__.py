"""Blok is a tool for building and managing docker-compose projec

Blok utilized the dependency injection pattern to build and manage docker-compose projects.
Services can be built and managed using the blok CLI tool. In general
blok aims to autodiscover services and build them using the __blok__ magic method.



"""

from .blok import blok, InitContext, ExecutionContext, Option, Command
from .service import service
from .renderer import Renderer, Panel
from .cli.create import create_cli


__all__ = [
    "blok",
    "service",
    "InitContext",
    "ExecutionContext",
    "Option",
    "Renderer",
    "Panel",
    "create_cli",
    "Command",
]
