from logging import getLogger
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.progress import track
from rich.table import Table
from typer import Option

from ..finder import get_tests_groups
from ..runner import DockerRunner, Orchestrator, TempDirGenerator

default_repo_dir = Path.cwd()
default_test_dir = Path.cwd().joinpath("tests")

runner = DockerRunner()

logger = getLogger(__name__)


def server():
    from ..server import __main__  # noqa: F401


Dir = Annotated[Path, Option(exists=True, dir_okay=True, file_okay=False)]

dir_generator = TempDirGenerator(base_path=Path(".edd-cache"))


def run(
    test_dir: Dir = default_test_dir,
    repo_dir: Dir = default_repo_dir,
    clean_run: bool = Option(False, "-c", "--clean-run"),
):
    console = Console()
    dir_generator.cache = not clean_run
    test_groups = get_tests_groups(test_dir)
    orchestrator = Orchestrator(repo_dir, runner, dir_generator)

    for g in orchestrator.iter_run_assignment_group(test_groups):
        if g.result.verdict == "error":
            console.print(f"Error preparing {g.name} ({g.result.error})", style="red")
            continue

        table = Table(title=f"{g.name} Test cases")
        table.add_column("Test case")
        table.add_column("Verdict")
        table.add_column("Error")
        table.add_column("Time")
        table.add_column("Score")

        desc = f"Running tests for {g.name}"
        for t in track(g.iter_run_group_test(), description=desc, total=len(g.tests)):
            if t.verdict == "error":
                table.add_row(t.name, "[red]Error", t.error, "", "")
            else:
                table.add_row(t.name, "[green]Ok", "", str(t.time), str(t.percentage))
        console.print(table)
