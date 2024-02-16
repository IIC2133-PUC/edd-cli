from pathlib import Path

import docker

from .abstract_runner import AbstractRunner


class DockerRunner(AbstractRunner):
    def __init__(self, image="carlogauss33/edd-runner") -> None:
        self._client = None
        self._image = image

    def setup(self):
        self.client.images.pull(self._image)

    @property
    def client(self):
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def run(self, command: list[str], dir: Path):
        return self.client.containers.run(
            self._image,
            command,
            working_dir=str(dir),
            remove=True,
            volumes={str(dir): {"bind": str(dir), "mode": "rw"}},
        )
