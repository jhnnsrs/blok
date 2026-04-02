from typing import Set
from dataclasses import dataclass, field

from blok import blok, Option
from blok.bloks.services.dns import DnsService, DNSResult
import psutil
import socket
import ipaddress


@dataclass
class DNSResult:
    hostnames: Set[str] = field(default_factory=set)
    ip_addresses: Set[str] = field(default_factory=set)


def is_valid_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return not (
            ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_unspecified
            or ip_obj.is_reserved
        )
    except ValueError:
        return False


def get_dns_result(check_ip6: bool = True) -> DNSResult:
    dns_result = DNSResult()
    hostnames = set()
    ip_addresses = set()

    interfaces = psutil.net_if_addrs()

    for interface, addrs in interfaces.items():
        for addr in addrs:
            family = addr.family.name
            if family == "AF_INET" or (check_ip6 and family == "AF_INET6"):
                ip = addr.address
                if not is_valid_ip(ip):
                    continue
                try:
                    print(f"Resolving {ip} from interface '{interface}'")
                    hostname, _, resolved_ips = socket.gethostbyaddr(ip)
                    hostnames.add(hostname)
                    ip_addresses.update(resolved_ips)
                except (socket.herror, socket.gaierror):
                    continue

    dns_result.hostnames = set(sorted(hostnames))
    dns_result.ip_addresses = set(sorted(ip_addresses))
    return dns_result


@blok(
    DnsService,
    options=[Option("check_ip_six", default=False)],
    description="Uses psutil to inspect the DNS configuration of the host, excluding loopback and link-local addresses.",
)
class PsutilDNSBlok:
    def get_dns_result(self):
        return self.result

    def preflight(self, check_ip_six):
        print("Performing DNS lookup using psutil")
        self.result = get_dns_result(check_ip_six)
        print("DNS lookup complete")

    def build(self, cwd):
        pass
