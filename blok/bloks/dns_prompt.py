from typing import Dict, Any, Protocol
from blok import blok, InitContext, Option
from blok import service
from dataclasses import dataclass
import socket
from dataclasses import dataclass, field
from typing import Set
from blok.bloks.services.dns import DNSResult, DnsService
from inquirer import prompt


@dataclass
class DNSResult:
    hostnames: Set[str] = field(default_factory=set)
    ip_addresses: Set[str] = field(default_factory=set)


@blok(
    DnsService,
    options=[
        Option(
            "hostnames",
            help="A list of hostnames to resolve",
            multiple=True,
        ),
        Option(
            "ip_addresses",
            help="A list of IP addresses to resolve",
            multiple=True,
        ),
    ],
    description="Will use the command prompts to get the hostnames.",
)
class PromptDNSBlok:
    def get_dns_result(self):
        return self.result

    def preflight(self, hostnames: list[str], ip_addresses: list[str]):
        self.result = DNSResult(hostnames=hostnames, ip_addresses=ip_addresses)

    def build(self, cwd):
        pass
