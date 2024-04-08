from logging import getLogger
from pathlib import Path
from typing import Annotated

import pydantic_core
from rich.console import Console
from rich.progress import track
from rich.table import Table
from typer import Option

from ..finder import get_tests_groups
from ..runner import (
    AbstractRunner,
    DirectRunner,
    DockerRunner,
    Orchestrator,
    TempDirGenerator,
)

default_repo_dir = Path.cwd()
default_test_dir = Path("tests")

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


def list_test_groups(test_dir: Dir = default_test_dir):
    test_groups = get_tests_groups(test_dir)
    console = Console()
    for group in test_groups:
        table = Table(title=group.display_name, show_header=False)
        table.add_column("i")
        table.add_column("Test case")
        for i, test in enumerate(group.tests):
            table.add_row(str(i), test.name)
        console.print(table)


def run_cloned_folders(
    output_file: Path, repos_dir: Dir = Path("repos"), test_dir: Dir = default_test_dir
):
    runner = DirectRunner()
    repos = [repo for repo in repos_dir.iterdir() if repo.is_dir()]
    with output_file.open("wb") as output:
        for repo in track(repos):
            result = run_cloned_folder(repo, test_dir, runner)
            json = pydantic_core.to_json(result)
            output.write(json)
            output.write(b"\n")


def run_cloned_folder(repo_dir: Path, test_dir: Path, runner: AbstractRunner):
    assignment_groups = get_tests_groups(test_dir)
    return Orchestrator(repo_dir, runner, dir_generator).run(assignment_groups)
