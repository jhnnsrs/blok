from typing import Dict, Any, Protocol
from blok import blok, InitContext, Option
from blok import service
from dataclasses import dataclass
import socket
from dataclasses import dataclass, field
from typing import Set
from blok.bloks.services.dns import DNSResult, DnsService
from blok.bloks.services.vscode import VsCodeService
from blok.blok import ExecutionContext
from blok.tree.models import JSONFile


@blok(
    VsCodeService,
    description="A blok for setting up a vscode workspace",
    options=[Option("with_docker", help="Have a docker up command", default=True)],
)
class VsCodeBlok:
    def __init__(self):
        self.result = None
        self.tasks = []

    def preflight(self, init: InitContext, with_docker=True):
        if with_docker:
            self.register_task(
                "Docker Compose Up",
                "shell",
                "docker",
                ["compose", "up"],
                {"cwd": "${workspaceFolder}"},
            )

    def register_task(
        self,
        label: str,
        type: str,
        command: str,
        args: list[str],
        options: Dict[str, Any],
    ):
        self.tasks.append(
            {
                "label": label,
                "type": type,
                "command": command,
                "args": args,
                "options": options,
            }
        )

    def build(self, context: ExecutionContext):
        context.file_tree.set_nested(
            ".vscode",
            "tasks.json",
            JSONFile(version="2.0.0", tasks=self.tasks),
        )
        pass
