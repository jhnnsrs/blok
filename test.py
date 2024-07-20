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
