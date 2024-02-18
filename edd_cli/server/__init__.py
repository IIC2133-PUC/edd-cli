from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from rich.progress import track

from ..finder import TestCaseFinder
from ..repository import RepositoryDownloader, RepositoryDownloadException
from ..runner import DockerRunner, Environment, TempDirGeneratorFactory
from .auth import verify_secret
from .settings import settings

repo_downloader = RepositoryDownloader(
    org=settings.github_org,
    download_dir=settings.repository_download_dir,
)

runner = DockerRunner()

dir_generator_factory = TempDirGeneratorFactory(base_path=settings.repository_temp_dir)
test_case_finder = TestCaseFinder(settings.tests_directory)

app = FastAPI()


@app.post("/assignments/{test_suite}/{user}", dependencies=[Depends(verify_secret)])
def run_tests(
    assignment: str, user: str, clean_run: bool = False, pull_if_exists: bool = True
):

    assignment_groups = test_case_finder.get_assignment(assignment)

    if assignment_groups is None:
        raise HTTPException(status_code=404, detail="Test suite not found")

    try:
        repo = f"{assignment}-{user}"
        repo_path = repo_downloader.download(repo, pull_if_exists=pull_if_exists)
    except RepositoryDownloadException:
        raise HTTPException(status_code=500, detail="Failed to download repository")

    dir_generator = dir_generator_factory.create(
        subpath=Path(user, assignment), cache=not clean_run
    )

    for test_group in assignment_groups:
        environment = Environment(repo_path, runner, dir_generator)
        environment.run_stages(test_group)

        description = f"Running tests for {test_group.name}"
        for test in track(test_group.tests, description=description):
            test_env = environment.clone()
            test_env.run_stages(test)
