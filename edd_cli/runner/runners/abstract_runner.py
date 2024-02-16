from abc import ABC, abstractmethod
from pathlib import Path


class AbstractRunner(ABC):
    "Interface for running commands in a directory."

    @abstractmethod
    def run(self, command: list[str], dir: Path):
        "Runs the command in the given directory."
        raise NotImplementedError
