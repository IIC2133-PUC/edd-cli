from logging import getLogger
from pathlib import Path
from subprocess import Popen, TimeoutExpired
from time import time

from .interface import AbstractRunner, RunErrorException

logger = getLogger(__name__)


class DirectRunner(AbstractRunner):
    "Runs the command directly in the current environment."

    def __init__(self) -> None:
        pass

    def run(self, command: list[str], dir: Path, timeout=10):
        stdout = dir.joinpath(f".stdout.{dir.name}").open("wb")
        time_path = dir.joinpath(f".time.{dir.name}")
        initial_time = time()
        try:
            process = Popen(command, stdout=stdout, cwd=dir)
            exit_code = process.wait(timeout=timeout)
            time_path.write_text(str(time() - initial_time))

            if exit_code != 0:
                raise RunErrorException(f"Command {command} failed: {exit_code}")

        except TimeoutExpired:
            raise RunErrorException(f"Command {command} timed out")
