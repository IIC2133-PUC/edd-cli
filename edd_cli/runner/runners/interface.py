from abc import ABC, abstractmethod
from pathlib import Path


class RunErrorException(Exception):
    "Error raised when a command fails to run."

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AbstractRunner(ABC):
    "Interface for running commands in a directory."

    @abstractmethod
    def run(self, command: list[str], dir: Path):
        """
        Runs the command in the given directory.
        @throws RunErrorException if the command fails.
        """
        raise NotImplementedError
