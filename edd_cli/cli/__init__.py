import logging
from pathlib import Path
from typing import Annotated

from rich.logging import RichHandler
from rich.progress import track
from typer import Option, Typer

from ..runner import DockerRunner, Environment, TempDirGenerator, get_tests_groups

app = Typer()


Dir = Annotated[Path, Option(exists=True, dir_okay=True, file_okay=False)]

default_repo_dir = Path.cwd()
default_test_dir = Path.cwd().joinpath("tests")

runner = DockerRunner()


@app.command()
def server():
    from ..run_server import run_server

    run_server()


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


@app.callback()
def set_logging_level(
    verbose: bool = Option(False, "-v", "--verbose"),
    debug: bool = Option(False, "-d", "--debug"),
    quiet: bool = Option(False, "-q", "--quiet"),
    disable_rich: bool = Option(False, "--disable-rich"),
):
    import os

    if debug:
        logging_level = logging.DEBUG
    elif verbose:
        logging_level = logging.INFO
    elif quiet:
        logging_level = logging.WARNING
    else:
        logging_level = logging.INFO

    if disable_rich:
        os.environ["NO_COLOR"] = "1"
        os.environ["TERM"] = "dumb"
        logging.basicConfig(level=logging_level)
    else:
        logging.basicConfig(
            level=logging_level, handlers=[RichHandler(rich_tracebacks=True)]
        )
