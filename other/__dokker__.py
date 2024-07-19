import click
from blok.cli.models import service, instance, CLIOption, InitContext, BuildContext
from pydantic import BaseModel
from typing import Dict, Any
from dataclasses import dataclass, field

dataclass

@dataclass
class AdminCredentials:
    password: str
    username: str
    email: str

@service("live.arkitekt.admin")
class AdminService:

    def retrieve(self) -> AdminCredentials:
       ...
@dataclass
class MinioCredentials:
    password: str
    username: str
    email: str

@service("live.arkitekt.minio")
class MinioService:

    def retrieve(self) -> MinioCredentials:
       ...





@instance(AdminService, dependencies=[], options=[])
class EasyAdmin:
    username = field(subcommand="username",
            help="Which admin username to use",
            default="admin",
            show_default=True,)
    email = field(subcommand="email")


    def __init__(self) -> None:
        self.password = "admin"
        self.username = "admin"
        self.email = "admin@admin.com"

    def preflight(self, init: InitContext, minio: MinioCredentials):
        for key, value in init.kwargs.items():
            setattr(self, key, value)

        minio.retrieve()

    def build(self, buid: BuildContext):
        pass

    def retrieve(self):
        return AdminCredentials(
            password=self.password,
            username=self.username,
            email=self.email,
        )

    def get_options(self):
        with_username = CLIOption(
            subcommand="username",
            help="Which admin username to use",
            default="admin",
            show_default=True,
        )
        with_username = CLIOption(
            subcommand="password",
            help="Which password to use",
            default="admin",
            show_default=True,
        )
        with_email = CLIOption(
            subcommand="email",
            help="Which password to use",
            default="",
            show_default=True,
        )

        return [with_username, with_username, with_email]


def build_service():
    return AdminService
