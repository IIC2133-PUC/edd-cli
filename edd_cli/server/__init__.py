from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from ..finder import TestCaseFinder
from ..repository import RepositoryDownloader, RepositoryDownloadException
from ..runner import DockerRunner, Orchestrator, TempDirGeneratorFactory
from ..schema.results import AssignmentResults
from ..schema.tests import Assignment
from ..utils.dir import dir_clear_old, dir_size
from .auth import verify_secret
from .settings import settings

repo_downloader = RepositoryDownloader(
    org=settings.github_org,
    download_dir=settings.repository_download_dir,
)

runner = DockerRunner()

dir_generator_factory = TempDirGeneratorFactory(base_path=settings.output_temp_dir)
test_case_finder = TestCaseFinder(settings.tests_directory)


app = FastAPI(
    title="EDD Server",
    version="0.1.0",
    dependencies=[Depends(verify_secret)],
)


@app.get("/assignments", tags=["assignments"])
def list_assignments() -> list[Assignment]:
    return test_case_finder.list_assignments()


class CacheSize(BaseModel):
    repos: int
    output: int


@app.get("/cache", tags=["cache"])
def get_cache_size() -> CacheSize:
    repos = dir_size(settings.repository_download_dir)
    output = dir_size(settings.output_temp_dir)
    return CacheSize(repos=repos, output=output)


@app.delete("/cache", tags=["cache"])
def remove_cache(seconds_old: int) -> CacheSize:
    delta = timedelta(seconds=seconds_old)
    dir_clear_old(settings.repository_download_dir, delta)
    dir_clear_old(settings.output_temp_dir, delta)
    return get_cache_size()


@app.post("/assignments/{test_suite}/{user}", tags=["assignments"])
def run_tests(
    assignment: str, user: str, clean_run: bool = False, pull_if_exists: bool = True
) -> AssignmentResults:

    assignment_groups = test_case_finder.get_assignment(assignment)

    if assignment_groups is None:
        raise HTTPException(status_code=404, detail="Test suite not found")

    try:
        repo = f"{assignment}-{user}"
        repo_path = repo_downloader.download(repo, pull_if_exists=pull_if_exists)
    except RepositoryDownloadException:
        raise HTTPException(status_code=500, detail="Failed to download repository")

    dir_generator = dir_generator_factory.create(
        subpath=Path(assignment, user), cache=not clean_run
    )

    orchestrator = Orchestrator(repo_path, runner, dir_generator)
    results = orchestrator.run(assignment_groups)

    return AssignmentResults(name=assignment, user=user, results=results)
