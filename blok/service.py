from typing import List, runtime_checkable, Protocol
import typing as t


class Service(Protocol):
    def get_identifier(self) -> str:
        raise NotImplementedError("This method must be implemented by the subclass")


def service(name: str):
    def decorator(cls):
        cls.__service_identifier__ = name

        if not hasattr(cls, "get_identifier"):
            cls.get_identifier = lambda self: self.__service_identifier__

        return cls

    return runtime_checkable(decorator)
