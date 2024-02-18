from logging import getLogger
from pathlib import Path

from ..schema import AbstractPipeline, PathMapping
from .runners import AbstractRunner
from .temp_dirs import TempDirGenerator

logger = getLogger(__name__)


def assert_all_files_exist(files: list[PathMapping]):
    for file in files:
        if not file.source.exists():
            raise FileNotFoundError(f"File {file.source} does not exist")


class Environment:
    """"""

    def __init__(
        self,
        initial_dir: Path,
        runner: AbstractRunner,
        dir_generator: TempDirGenerator,
    ) -> None:

        self._dir = initial_dir
        self._runner = runner
        self._dir_generator = dir_generator

    def run_stages(self, group: AbstractPipeline):
        "Run stages on the current environment directory."
        for i, unresolved_step in enumerate(group.steps):
            step = unresolved_step.with_resolved_paths(group.path, self._dir)
            assert_all_files_exist(step.files)

            runner_dir = self._dir_generator.create(step)
            self._dir = runner_dir.path

            if runner_dir.cached:
                logger.info(
                    f"[cache hit] Skipping {group.display_name}[{i}]: {step.command}"
                )
                continue

            logger.info(
                f"[cache miss] Running {group.display_name}[{i}]: {step.command}"
            )
            runner_dir.prepare()
            self._runner.run(step.command, runner_dir.path)

    def clone(self):
        "Clone the environment, starting the current environment directory."
        return Environment(self._dir, self._runner, self._dir_generator)
