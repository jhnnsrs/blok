from typing import List, runtime_checkable, Protocol
import typing as t
from dataclasses import dataclass

from blok.dependency import Dependency


@dataclass
class ServiceMeta:
    name: t.Optional[str]
    identifier: str
    description: t.Optional[str]


class Service(Protocol):
    def get_blok_service_meta(self) -> ServiceMeta:
        raise NotImplementedError("This method must be implemented by the subclass")


def service(
    identifier: str, description: t.Optional[str] = None, name: t.Optional[str] = None
):
    def decorator(cls):
        cls.__blok_meta__ = ServiceMeta(
            identifier=identifier, description=description or "", name=name
        )
        cls.__is_service__ = True

        if not hasattr(cls, "get_blok_service_meta"):
            cls.get_blok_service_meta = classmethod(lambda self: self.__blok_meta__)

        if not hasattr(cls, "as_dependency"):
            cls.as_dependency = lambda optional, default: Dependency(
                service=cls.__blok_meta__.identifier,
                optional=optional,
                description=cls.__blok_meta__.description,
                default=default,
            )

        try:
            return runtime_checkable(cls)
        except TypeError as e:
            raise TypeError(
                f"Could not create Blok Service from {cls}. Blok services need to inherit from 'typing.Protocol'"
            ) from e

    return decorator
