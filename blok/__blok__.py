from blok.bloks.netifaces import NetifacesBlok
from blok.bloks.dns_prompt import PromptDNSBlok
from blok.bloks.vscode import VsCodeBlok


def get_bloks():
    return [NetifacesBlok(), VsCodeBlok(), PromptDNSBlok()]
