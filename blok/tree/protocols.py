from typing import Protocol
from pathlib import Path


class IsRepresentable(Protocol):
    def is_representable_as(self, path: Path): ...
