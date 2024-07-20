# blok


## Inspiration

Blok is designed to be intergrated into existing projects that want to programmatically created docker compose projects, suitable
for development and production environments. The main goal is to allow the user to create a project with a high level of configurability
and reusability.
blok is following the principles of depencency injection and inversion of control to create a project
from various "bloks" (i.e configurable services).


## Installation

```bash
pip install blok
```

## Quickstart

Create a new python file `my_cli.py` and add the following code:

```python my_cli
from blok import blok, ExecutionContext, Option, service
from blok.cli import create_cli
from typing import Protocol


@service("io.blok.minio")
class MinioService(Protocol):

    def register_bucket(self, bucket: str):
        ...

@blok(MinioService, options=[Option("port", type=int, default=9000)])
class MinioBlok:
    buckets: list[str]

    def preflight(self, port: int):
        self.buckets = []
        self.port = port

    def register_bucket(self, bucket: str):
        self.buckets.append(bucket)
        return bucket

    def build(self, context: ExecutionContext):
        service = {
            "image": "minio/minio",
            "command": ["server", "/data"],
            "volumes": [],
        }

        for bucket in self.buckets:
            context.file_tree.set_nested("mounts", bucket, {})
            service["command"].append(f"/data/{bucket}")
            service["volumes"].append(f"./mounts/{bucket}:/data/{bucket}")

        context.docker_compose.set_nested("services", "minio", service)


@blok("io.blok.data", options=[Option("port", type=int, default=8080)])
class DataBlok:
    port: int


    def preflight(self, minio: MinioBlok, port: int):
        self.port = port
        minio.register_bucket("data")
        minio.register_bucket("logs")

    def build(self, context: ExecutionContext):
        image = {
            "image": "dependend",
            "command": ["web-service", "--port", self.port],
        }
        context.docker_compose.set_nested("services", "data", image)


cli = create_cli(MinioBlok(), DataBlok())

if __name__ == "__main__":
    cli()

```

And now you can run the script to generate the docker-compose file

```bash
python my_cli.py build data .
```

This will starting from the data blok, resolve all dependencies and build the docker-compose setup
in the directory creating a `docker-compose.yml` file and the necessary mounts.


```tree
- my_cli.py
- docker-compose.yml
- mounts
    - data
    - logs
```


### Pass arguments to the bloks

All bloks can register options that can be passed to the blok via the cli (or in the future other renderers). The options are passed to the blok by prepending the blok name (or the blok class name) with `--` and the option name. For example to pass the port to the data blok you can run:

```bash

python my_cli.py build data --data-port 8080
```

### Diffable Projects

The blok project is designed to be diffable. This means that you can run the script multiple times and the output will be the same. This is achieved by using a file tree to store the state of the project and only writing the changes to the file system once you confirm it. Also
if you run the script with one argument it will only show the changes that will be made to the project.

```bash
python my_cli.py build data --data-port 8080
```

Wil Resulst in:

```
Differences                                                                          
├── Will Modify: /docker-compose.yml/services/data/command/2/a                       
│     Old: 7000                                                                      
│     New: 8080                                                                      
└── Will Modify: /__blok__.yml/data_port                                             
      Old: 7000                                                                      
      New: 8080   
```
You can then choose to apply the changes.

### Blok Dependencies

Bloks can define dependencies on other bloks by adding them as arguments to the `preflight` method. The blok will then be resolved and passed to the blok. For example the `DataBlok` has a dependency on the `MinioService` and can access it via the `minio` argument in the `preflight` method.

#### Depedency Resolution

One of the core ideas is that services that bloks can depend on
have various implementations. For example you could create a custom implemention of the MinioService and other bloks that depend on the MinioService could on dependency resolution choose the custom implementation.

You can force a specific blok by passing the `-b` flag to the cli. For example to force the MinioService

```
python my_cli.py build data -b minio
````


