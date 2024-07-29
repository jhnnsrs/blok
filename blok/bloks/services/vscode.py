from typing import Dict, Any, Protocol
from blok import blok, InitContext, Option
from blok import service
from dataclasses import dataclass
import socket
from dataclasses import dataclass, field
from typing import Set


@service("io.blok.vscode")
class VsCodeService(Protocol):
    def register_task() -> None:
        pass
