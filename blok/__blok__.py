from blok.bloks.psutils import PsutilDNSBlok
from blok.bloks.dns_prompt import PromptDNSBlok
from blok.bloks.vscode import VsCodeBlok


def get_bloks():
    return [PsutilDNSBlok(), VsCodeBlok(), PromptDNSBlok()]
