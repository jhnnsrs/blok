from typing import List, runtime_checkable, Protocol
import typing as t


class Service(Protocol):
    def get_identifier(self) -> str:
        raise NotImplementedError("This method must be implemented by the subclass")


def service(name: str):
    def decorator(cls):
        if not hasattr(cls, "get_identifier"):
            cls.get_identifier = classmethod(lambda self: name)

        try:
            return runtime_checkable(cls)
        except TypeError as e:
            raise TypeError(f"Could not create Blok Service from {cls}. Blok services need to inherit from 'typing.Protocol'") from e

    return decorator
