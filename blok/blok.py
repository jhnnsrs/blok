from typing import List, runtime_checkable, Protocol
import typing as t
from blok.models import Option, NestedDict
from blok.service import Service
from dataclasses import dataclass
from blok.renderer import Renderer
import inspect

from blok.utils import check_service_compliance


T = t.TypeVar("T")


@dataclass
class InitContext:
    dependencies: t.Dict[str, "Blok"]
    kwargs: t.Dict[str, t.Any]

    def get_service(self, identifier: t.Type[T]) -> "T":
        try:
            if hasattr(identifier, "get_identifier"):
                return self.dependencies[identifier.get_identifier()]
            else:
                assert isinstance(
                    identifier, str
                ), "Identifier must be a string or a service/blok class"
                return self.dependencies[identifier]
        except KeyError:
            raise ValueError(
                f"Service with identifier {identifier} not found in dependencies"
            )


@dataclass
class ExecutionContext:
    docker_compose: NestedDict
    file_tree: NestedDict


@runtime_checkable
class Blok(Protocol):
    def get_blok_name(self) -> str: ...

    def get_identifier(self) -> str: ...

    def get_dependencies(self) -> List[str]: ...

    def entry(self, render: Renderer): ...

    def build(self, context: ExecutionContext): ...
    def preflight(self, init: InitContext): ...
    def get_options(self, name: str) -> List[Option]: ...


def inspect_dependable_params(function):
    signature = inspect.signature(function)
    parameters = signature.parameters
    dependencies = []
    dependency_mapper = {}

    for index, (name, param) in enumerate(parameters.items()):
        if index == 0:
            # This is the self parameter
            continue

        else:
            # Check if the parameter is **kwargs like

            cls = param.annotation

            if param.annotation == InitContext:
                dependency_mapper["__context__"] = name
                continue

            if hasattr(cls, "get_identifier"):
                dependencies.append(cls.get_identifier())
                dependency_mapper[cls.get_identifier()] = name
                continue

            dependency_mapper["__kwarg__" + str(index)] = name

    return dependencies, dependency_mapper


def service(service_identifier: t.Union[str, Service]):
    def decorator(cls):
        cls.__service_identifier__ = (
            service_identifier
            if isinstance(service_identifier, str)
            else service_identifier.get_identifier()
        )
        cls.__is_service__ = True

        if not hasattr(cls, "get_identifier"):
            cls.get_identifier = classmethod(lambda self: self.__service_identifier__)

        return cls

    return decorator


def build_mapped_preflight_function(preflight_function, dependency_mapper):
    def mapped_preflight_function(self, context):
        kwargs = {}
        for identifier, name in dependency_mapper.items():
            if identifier.startswith("__kwarg__"):
                try:
                    kwargs[name] = context.kwargs[name]
                except KeyError:
                    raise ValueError(
                        f"Missing required argument {name} in preflight function. Neither a dependency nor a context argument with the same name was found. Available arguments: {context.kwargs.keys()}"
                    )

            elif identifier == "__context__":
                kwargs[name] = context

            else:
                kwargs[name] = context.dependencies[identifier]

        try:
            preflight_function(self, **kwargs)
        except TypeError as e:
            raise TypeError(
                f"Error while running preflight function {preflight_function.__name__} with arguments {kwargs} {context.kwargs}"
            ) from e
        except Exception as e:
            raise e

    return mapped_preflight_function


def blok(
    service_identifier: t.Union[str, Service],
    blok_name: t.Optional[str] = None,
    options: t.Optional[List[Option]] = None,
    dependencies: t.Optional[List[str]] = None,
):
    def decorator(cls):
        try:
            cls.__service_identifier__ = (
                service_identifier
                if isinstance(service_identifier, str)
                else service_identifier.get_identifier()
            )
            cls.__is_blok__ = True
            cls.__dependencies__ = (
                dependencies or []
            )  # Cannot use set because we need to maintain order
            cls.__options__ = options or []

            if not hasattr(cls, "get_blok_name"):
                cls.get_blok_name = classmethod(
                    lambda cls: blok_name or cls.__name__.lower().replace("blok", "")
                )
            else:
                assert isinstance(
                    getattr(cls, "get_blok_name"), classmethod
                ), "get_blok_name must be a class method"

            if not hasattr(cls, "get_identifier"):
                cls.get_identifier = classmethod(lambda cls: cls.__service_identifier__)

            if not hasattr(cls, "preflight"):
                cls.preflight = lambda self, context: None
            else:
                init_function = getattr(cls, "preflight")
                init_dependencies, dependency_mapper = inspect_dependable_params(
                    init_function
                )
                cls.preflight = build_mapped_preflight_function(
                    init_function, dependency_mapper
                )
                for i in init_dependencies:
                    if i not in cls.__dependencies__:
                        cls.__dependencies__.append(i)

            if not hasattr(cls, "get_identifier"):
                cls.get_identifier = classmethod(lambda cls: cls.__service_identifier__)

            if not hasattr(cls, "get_dependencies"):
                cls.get_dependencies = lambda cls: cls.__dependencies__

            if not hasattr(cls, "get_options"):
                cls.get_options = lambda cls: cls.__options__

            if not hasattr(cls, "entry"):
                cls.entry = lambda self, renderer: None

            if not hasattr(cls, "build"):
                cls.build = lambda self, context: None

            if isinstance(service_identifier, str):
                pass
            elif inspect.isclass(service_identifier):
                check_service_compliance(cls, service_identifier)

            else:
                raise ValueError("Service must be a string or a service class")

        except Exception as e:
            raise ValueError(f"Error while creating blok {cls.__name__}") from e

        return cls

    return decorator
