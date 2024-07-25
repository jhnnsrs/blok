from pathlib import Path
import signal
import time
import subprocess
import click
from blok.blok import Command
from blok.registry import BlokRegistry
from blok.renderer import Renderer, Panel

# List to keep track of subprocesses
subprocesses = []


def signal_handler(sig, frame):
    print("Main process received interrupt signal")
    terminate_all_subprocesses()
    print("All subprocesses terminated")
    exit(0)


def terminate_all_subprocesses():
    for p in subprocesses:
        if p.poll() is None:  # Check if process is still running
            print(f"Terminating subprocess with PID: {p.pid}")
            p.terminate()
    for p in subprocesses:
        p.wait()


def secure_path_combine(x: Path, y: Path) -> Path:
    # Resolve the combined path
    mother_path = x.resolve()
    combined_path = (mother_path / y).resolve()

    # Check if the combined path is within the mother path
    if mother_path in combined_path.parents or mother_path == combined_path:
        return combined_path
    else:
        raise ValueError(
            f"The user-defined path traverses out of the mother path. {list(combined_path.parents)} but requested {mother_path}"
        )


@click.pass_context
def entrypoint(
    ctx: click.Context,
    registry: BlokRegistry,
    renderer: Renderer,
    blok_file_name: str,
    **kwargs,
):
    path = Path(kwargs.pop("path"))
    yes = kwargs.pop("yes", False)
    select = kwargs.pop("select", [])
    nd = kwargs.pop("no_docker", False)

    if nd:
        if not select:
            raise click.ClickException("No up commands selected and no-docker flag set")
    renderer.render(
        Panel("Lets up this project", title="Welcome to Blok!", style="bold magenta")
    )

    up_commands = ctx.obj.get("up_commands", {})

    selected_commands = []

    if select:
        print("Selecting commands")
        for key in select:
            if key in up_commands:
                selected_commands.append(up_commands[key])
            else:
                raise click.ClickException(f"Command with key {key} not found")

    else:
        selected_commands = list(up_commands.values())

    leading_command = None

    if nd:
        if not select:
            raise click.ClickException(
                "No up commands selected and no-docker flag set. If setting -nd flag, please select up commands via -s flag"
            )
        leading_command = selected_commands.pop(0)
    else:
        leading_command = {"command": ["docker", "compose", "up"], "cwd": "."}

    print("Running leading command", leading_command["command"])

    if selected_commands:
        if yes or renderer.confirm(
            "Run additional up commands? \n\t"
            + "\n\t".join(map(lambda x: " ".join(x["command"]), selected_commands))
            + "\n"
        ):
            print("Running up commands")
        else:
            raise click.Abort("User aborted")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        for command in selected_commands:
            rel_path = secure_path_combine(path, Path(command["cwd"]))
            p = subprocess.Popen(
                command["command"],
                cwd=rel_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocesses.append(p)
            print(f"Started subprocess {command['command']} with PID: {p.pid}")

    try:
        rel_path = secure_path_combine(path, Path(leading_command["cwd"]))
        subprocess.run(" ".join(leading_command["command"]), shell=True, cwd=rel_path)
    except subprocess.CalledProcessError as e:
        print(f"Error running docker-compose up: {e}")
        terminate_all_subprocesses()
        exit(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected")
        terminate_all_subprocesses()
        signal_handler(signal.SIGINT, None)
    finally:
        terminate_all_subprocesses()
