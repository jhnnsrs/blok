import typing as t
from dataclasses import dataclass


@dataclass
class Option:
    subcommand: str
    show_default: t.Union[bool, str, None] = None
    prompt: t.Union[bool, str] = False
    confirmation_prompt: t.Union[bool, str] = False
    prompt_required: bool = True
    hide_input: bool = False
    is_flag: t.Optional[bool] = None
    flag_value: t.Optional[t.Any] = None
    count: bool = False
    allow_from_autoenv: bool = True
    help: t.Optional[str] = None
    hidden: bool = False
    show_choices: bool = True
    show_envvar: bool = False
    type: t.Optional[t.Union[t.Any, t.Any]] = None
    required: bool = False
    default: t.Optional[t.Union[t.Any, t.Callable[[], t.Any]]] = None
    callback: t.Optional[t.Callable[[t.Any, t.Any, t.Any], t.Any]] = None
    nargs: t.Optional[int] = None
    multiple: bool = False
    metavar: t.Optional[str] = None
    expose_value: bool = True
    is_eager: bool = False
    shell_complete: t.Optional[
        t.Callable[
            [t.Any, t.Any, str],
            t.Union[t.List[t.Any], t.List[str]],
        ]
    ] = None


class NestedDict(dict):
    def set_nested(self, *keys_and_value):
        *keys, value = keys_and_value
        d = self  # Reference to the current level of the nested dictionary

        # Iterate through all keys except the last one
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = NestedDict()
            d = d[k]

        # Merge with existing if it's a dict, otherwise set the value
        last_key = keys[-1]
        if isinstance(d.get(last_key), dict) and isinstance(value, dict):
            d[last_key].update(value)
        else:
            d[last_key] = value
