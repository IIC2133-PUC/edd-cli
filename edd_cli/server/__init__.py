from pathlib import Path

from fastapi import FastAPI
from rich.progress import track

from ..repository import RepositoryDownloader
from ..runner import DockerRunner, Environment, TempDirGenerator, get_tests_groups

app = FastAPI()

repo_downloader = RepositoryDownloader(
    org="IIC2133-PUC", download_dir=Path(".edd-repos")
)
runner = DockerRunner()


@app.post("/run/{test_suite}/{user}")
def run_tests(test_suite: str, user: str, clean_run: bool = False):
    # TODO: validar testSuit y remplazar aquí
    test_groups = get_tests_groups(Path("./tests"))
    repo_path = repo_downloader.download(f"{test_suite}-{user}")

    dir_generator = TempDirGenerator(
        base_path=Path(".edd-cache", user, test_suite), cache=not clean_run
    )

    for test_group in test_groups:
        environment = Environment(repo_path, runner, dir_generator)
        environment.run_stages(test_group)

        description = f"Running tests for {test_group.name}"
        for test in track(test_group.tests, description=description):
            test_env = environment.clone()
            test_env.run_stages(test)
