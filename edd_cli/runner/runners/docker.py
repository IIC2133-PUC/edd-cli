from logging import getLogger
from pathlib import Path
from subprocess import Popen, TimeoutExpired
from time import time

from .interface import AbstractRunner, RunErrorException

logger = getLogger(__name__)


class DockerRunner(AbstractRunner):
    def __init__(self, image="carlogauss33/edd-runner") -> None:
        self._client = None
        self._image = image

    def _create_docker_command(self, dir: Path, command: list[str]):
        docker_command = ["docker", "run"]
        docker_command += ["--volume", f"{dir}:/app"]
        docker_command += ["--workdir", "/app"]
        docker_command += ["--rm"]
        docker_command += [self._image]
        docker_command += command
        return docker_command

    def run(self, command: list[str], dir: Path, timeout=10):
        docker_command = self._create_docker_command(dir, command)
        try:
            stdout = dir.joinpath(f".stdout.{dir.name}").open("wb")
            time_path = dir.joinpath(f".time.{dir.name}")
            initial_time = time()
            process = Popen(docker_command, stdout=stdout)
            exit_code = process.wait(timeout=timeout)

            time_path.write_text(str(time() - initial_time))

            if exit_code != 0:
                raise RunErrorException(f"Command {command} failed: {exit_code}")

        except TimeoutExpired:
            raise RunErrorException(f"Command {command} timed out")
