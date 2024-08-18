from typing import Dict, Any, Protocol
from blok import blok, InitContext, Option
from blok import service
from dataclasses import dataclass
import socket
from dataclasses import dataclass, field
from typing import Set


@dataclass
class DNSResult:
    hostnames: Set[str] = field(default_factory=set)
    ip_addresses: Set[str] = field(default_factory=set)


@service("io.blok.dns", description=" A service to perform DNS lookups.")
class DnsService(Protocol):
    def get_dns_result() -> DNSResult:
        pass
