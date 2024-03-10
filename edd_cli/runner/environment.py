from logging import getLogger
from pathlib import Path
from shutil import rmtree

from edd_cli.runner.runners.interface import RunErrorException

from ..schema.results import TestOkResult
from ..schema.tests import AbstractPipeline, PathMapping, ResolvedTestStage
from ..utils.paths import path_to_show
from .runners import AbstractRunner
from .temp_dirs import TempDirGenerator, TempDir

logger = getLogger(__name__)

def assert_all_files_exist(files: list[PathMapping]):
    for file in files:
        if not file.source.exists():
            raise RunErrorException(f"File {path_to_show(file)} does not exist")


class InvalidResultException(Exception):
    "Raised when the last command does not output a valid result (float)."


class Environment:
    """"""

    def __init__(
        self,
        initial_dir: Path,
        runner: AbstractRunner,
        dir_generator: TempDirGenerator,
        *,
        starting_time=0,
    ) -> None:

        self._dir = initial_dir
        self._runner = runner
        self._dir_generator = dir_generator
        self._time = starting_time
        self._last_step: ResolvedTestStage | None = None
        self._last_group: AbstractPipeline | None = None

    def run_stages(self, group: AbstractPipeline):
        "Run stages on the current environment directory."
        self._last_group = group
        for i, unresolved_step in enumerate(group.steps):
            self._last_step = unresolved_step.with_resolved_paths(group.path, self._dir)
            assert_all_files_exist(self._last_step.files)

            runner_dir = self._dir_generator.create(self._last_step)
            command = self._last_step.command
            name = group.display_name
            considered_in_time = unresolved_step.time_it

            self._dir = runner_dir.path

            if runner_dir.cached:
                logger.info(f"[cache hit] Skipping {name}[{i}]: {command}")
            else:
                logger.info(f"[cache miss] Running {name}[{i}]: {command}")
                self.__run(runner_dir, command)

            self._time += self._get_current_step_time() if considered_in_time else 0

    def __run(self, runner_dir: TempDir, command: list[str]):
        runner_dir.prepare()  # init dir
        try:
            self._runner.run(command, self._dir)
        except Exception:
            # rm if failed
            rmtree(self._dir, ignore_errors=True)
            raise

    def clone(self):
        "Clone the environment, starting the current environment directory."
        return Environment(
            self._dir, self._runner, self._dir_generator, starting_time=self._time
        )

    def get_result(self):
        assert self._last_step is not None
        assert self._last_group is not None

        return TestOkResult(
            name=self._last_group.display_name,
            time=self._time,
            percentage=self._get_percentage(),
        )

    def _get_current_step_time(self):
        time = float(self._dir.joinpath(f".time.{self._dir.name}").read_text())
        return time

    def _get_percentage(self):
        "Get's the result of the last command run."
        try:
            result = self._dir.joinpath(f".stdout.{self._dir.name}").read_text()
            return float(result)
        except Exception:
            raise InvalidResultException() from None
