from blok import blok, InitContext, ExecutionContext, CLIOption, create_cli


@blok("minio_service")
class MinioBlok:
    def __init__(self):
        self.buckets = []

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


@blok("api_service", dependencies=["minio_service"], options=[CLIOption("port", type=int, default=8080)])
class DataBlok:
    def __init__(self):
        self.register_buckets: []

    def init(self, context: InitContext):
        self.minio_service = context.dependencies.get("minio_service")
        self.minio_service.register_bucket("data")
        self.minio_service.register_bucket("logs")

    def build(self, context: ExecutionContext):
        image = {
            "image": "dependend",
            "command": ["-port", self.port],
        }
        context.docker_compose.set_nested("services", "data", image)


cli = create_cli(MinioBlok(), DataBlok())
cli()
