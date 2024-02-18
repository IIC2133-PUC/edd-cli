from pathlib import Path
from typing import Annotated

from rich.progress import track
from typer import Option, Typer

from ..finder import get_tests_groups
from ..runner import DockerRunner, Environment, TempDirGenerator

default_repo_dir = Path.cwd()
default_test_dir = Path.cwd().joinpath("tests")

runner = DockerRunner()

app = Typer()


@app.command()
def server():
    from ..server import __main__  # noqa: F401


Dir = Annotated[Path, Option(exists=True, dir_okay=True, file_okay=False)]


@app.command()
def run(
    test_dir: Dir = default_test_dir,
    repo_dir: Dir = default_repo_dir,
    clean_run: bool = Option(False, "-c", "--clean-run"),
):

    test_groups = get_tests_groups(test_dir)
    dir_generator = TempDirGenerator(base_path=Path(".edd-cache"), cache=not clean_run)

    for test_group in test_groups:
        environment = Environment(repo_dir, runner, dir_generator)
        environment.run_stages(test_group)

        description = f"Running tests for {test_group.name}"
        for test in track(test_group.tests, description=description):
            test_env = environment.clone()
            test_env.run_stages(test)
