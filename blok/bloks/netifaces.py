from typing import Dict, Any, Protocol
from blok import blok, InitContext, Option
from blok import service
from dataclasses import dataclass
import socket
from dataclasses import dataclass, field
from typing import Set
from blok.bloks.services.dns import DNSResult, DnsService


@dataclass
class DNSResult:
    hostnames: Set[str] = field(default_factory=set)
    ip_addresses: Set[str] = field(default_factory=set)


def get_interface_addresses(netifaces, interface, check_ip6=True):
    """
    Get IP addresses for a given network interface.
    """
    addresses = []
    try:
        interface_details = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in interface_details:
            for addr_info in interface_details[netifaces.AF_INET]:
                addresses.append(addr_info["addr"])
        if check_ip6 and netifaces.AF_INET6 in interface_details:
            for addr_info in interface_details[netifaces.AF_INET6]:
                addresses.append(addr_info["addr"])
    except ValueError:
        # If the interface doesn't support AF_INET or AF_INET6 or any other issue
        pass
    return addresses


def perform_dns_lookup(ip_address):
    """
    Perform a DNS lookup to find the hostname for a given IP address.
    """
    try:
        hostname, _, ip_addresses = socket.gethostbyaddr(ip_address)
        return hostname, ip_addresses
    except (socket.herror, socket.gaierror):
        # If the DNS lookup fails, return None
        return None, None


def get_dns_result(netifaces, check_ip6=True):
    # Get the list of all interfaces
    interfaces = netifaces.interfaces()
    dns_result = DNSResult()
    hostnames = set()
    ip_addresses = set()

    for interface in interfaces:
        addresses = get_interface_addresses(netifaces, interface, check_ip6)
        for address in addresses:
            hostname, new_addresses = perform_dns_lookup(address)
            if hostname:
                hostnames.add(hostname)
            if new_addresses:
                for new_address in new_addresses:
                    ip_addresses.add(new_address)

    dns_result.hostnames = sorted(hostnames)
    dns_result.ip_addresses = sorted(ip_addresses)

    return dns_result


@blok(
    DnsService,
    options=[Option("check_ip_six", default=False)],
    description="Uses netifaces to inspect the DNS configuration of the host.",
)
class NetifacesBlok:
    def get_dns_result(self):
        return self.result

    def preflight(self, check_ip_six):
        import netifaces

        print("Performing DNS lookup")
        self.result = get_dns_result(netifaces, check_ip_six)
        print("DNS lookup complete")

    def build(self, cwd):
        pass
