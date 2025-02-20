from typing import List, get_origin, runtime_checkable, Protocol
import typing as t
from blok.models import Option, NestedDict
from blok.service import Service
from dataclasses import dataclass
from blok.renderer import Renderer
import inspect
from typing import Optional, get_args, Union

from blok.utils import check_service_compliance
from blok.dependency import Dependency

T = t.TypeVar("T")


@dataclass
class InitContext:
    dependencies: t.Dict[str, "Blok"]
    kwargs: t.Dict[str, t.Any]

    def get_service(self, identifier: t.Type[T]) -> "T":
        try:
            if hasattr(identifier, "get_blok_meta"):
                return self.dependencies[identifier.get_blok_meta().service_identifier]
            elif hasattr(identifier, "get_blok_service_meta"):
                return self.dependencies[identifier.get_blok_service_meta().identifier]
            else:
                assert isinstance(
                    identifier, str
                ), "Identifier must be a string or a service/blok class"
                return self.dependencies[identifier]
        except KeyError:
            raise ValueError(
                f"Service with identifier {identifier} not found in dependencies {list(self.dependencies.keys())}"
            )


@dataclass
class Command:
    command: List[str]
    help: str = "The command to run"
    cwd: str = "The directory to run the command in"


@dataclass
class ExecutionContext:
    docker_compose: NestedDict
    file_tree: NestedDict
    install_commands: NestedDict
    up_commands: NestedDict


@dataclass
class BlokMeta:
    name: str
    description: str
    service_identifier: str
    tags: List[str]
    dependencies: List[Dependency]


@dataclass
class ServiceMeta:
    name: str
    description: str
    service_identifier: str


@runtime_checkable
class Blok(Protocol):
    def get_blok_meta(self) -> BlokMeta: ...

    def entry(self, render: Renderer): ...

    def build(self, context: ExecutionContext): ...

    def preflight(self, init: InitContext): ...

    def get_options(self, name: str) -> List[Option]: ...


def is_optional_type(annotation):
    """Check if a type is Optional[X], which is a Union[X, None]."""
    try:
        return type(None) in get_args(annotation)
    except TypeError:
        return False


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

            if param.annotation == InitContext:
                dependency_mapper["__context__"] = name
                continue

            if is_optional_type(param.annotation):
                cls = next(i for i in get_args(param.annotation) if i != type(None))
                is_optional = True
            else:
                cls = param.annotation
                is_optional = False

            if hasattr(cls, "get_blok_service_meta"):
                dependencies.append(
                    Dependency(
                        service=cls.get_blok_service_meta().identifier,
                        optional=is_optional,
                        description=cls.get_blok_service_meta().description,
                    )
                )
                dependency_mapper[cls.get_blok_service_meta().identifier] = name
                continue

            if hasattr(cls, "get_blok_meta"):
                dependencies.append(
                    Dependency(
                        service=cls.get_blok_meta().service_identifier,
                        optional=is_optional,
                        description=cls.get_blok_meta().description,
                    )
                )
                dependency_mapper[cls.get_blok_meta().service_identifier] = name
                continue

            dependency_mapper["__kwarg__" + str(index)] = name

    return dependencies, dependency_mapper


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
                kwargs[name] = context.dependencies.get(identifier, None)
        try:
            preflight_function(self, **kwargs)
        except TypeError as e:
            raise TypeError(
                f"Error while running preflight function {preflight_function.__name__} with arguments {kwargs} {context.kwargs}"
            ) from e
        except Exception as e:
            raise e

    return mapped_preflight_function


def convert_to_dependency(dependency):
    if isinstance(dependency, str):
        return Dependency(service=dependency, key=dependency)
    elif isinstance(dependency, Dependency):
        return dependency
    else:
        raise ValueError("Dependency must be a string or a Dependency object")


def blok(
    service_identifier: t.Union[str, Service],
    blok_name: t.Optional[str] = None,
    options: t.Optional[List[Option]] = None,
    dependencies: t.Optional[List[t.Union[str, Dependency]]] = None,
    tags: t.Optional[List[str]] = None,
    description=None,
):
    def decorator(cls):
        initial_blok_meta = BlokMeta(
            name=blok_name or cls.__name__.lower().replace("blok", ""),
            description=description or "",
            service_identifier=(
                service_identifier
                if isinstance(service_identifier, str)
                else service_identifier.get_blok_service_meta().identifier
            ),
            tags=tags or [],
            dependencies=(
                [convert_to_dependency(i) for i in dependencies] if dependencies else []
            ),
        )

        try:
            cls.__blok_meta__ = initial_blok_meta
            cls.__blok_options__ = options or []
            cls.__is_blok__ = True

            if not hasattr(cls, "get_options"):
                cls.get_options = lambda self: self.__blok_options__

            if not hasattr(cls, "preflight"):
                cls.preflight = lambda self, context: None
            else:
                init_function = getattr(cls, "preflight")
                preflight_dependencies, dependency_mapper = inspect_dependable_params(
                    init_function
                )
                cls.preflight = build_mapped_preflight_function(
                    init_function, dependency_mapper
                )

                already_key_dependencies = [
                    i.service for i in initial_blok_meta.dependencies
                ]

                for i in preflight_dependencies:
                    if i.service not in already_key_dependencies:
                        initial_blok_meta.dependencies.append(i)

            if not hasattr(cls, "get_blok_meta"):
                cls.get_blok_meta = classmethod(lambda cls: initial_blok_meta)
            else:
                assert isinstance(
                    getattr(cls, "get_blok_meta"), classmethod
                ), "get_blok_meta must be a class method"

            if not hasattr(cls, "entry"):
                cls.entry = lambda self, renderer: None

            if not hasattr(cls, "build"):
                cls.build = lambda self, context: None

            if not hasattr(cls, "get_options"):
                cls.get_options = lambda self: self.__blok_options__

            if not hasattr(cls, "as_dependency"):
                cls.as_dependency = lambda optional, default: Dependency(
                    service=cls.__blok_meta__.service_identifier,
                    optional=optional,
                    description=cls.__blok_meta__.description,
                    default=default,
                )

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
