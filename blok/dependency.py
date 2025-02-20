from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Dependency:
    service: str
    optional: bool = False
    description: Optional[str] = None
    default: bool = True
