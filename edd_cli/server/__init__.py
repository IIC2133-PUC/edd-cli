from datetime import timedelta
from pathlib import Path
from zipfile import ZipFile

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..finder import TestCaseFinder
from ..repository import RepositoryDownloader, RepositoryDownloadException
from ..runner import DockerRunner, Orchestrator, TempDirGeneratorFactory
from ..schema.results import AssignmentResults
from ..schema.tests import Assignment
from ..utils.dir import dir_clear_old, dir_last_modified, dir_size
from .auth import verify_secret
from .settings import settings

repo_downloader = RepositoryDownloader(
    org=settings.github_org,
    download_dir=settings.repository_download_dir,
)

runner = DockerRunner(image=settings.docker_image)

dir_generator_factory = TempDirGeneratorFactory(base_path=settings.output_temp_dir)
test_case_finder = TestCaseFinder(settings.tests_directory)


app = FastAPI(
    title="EDD Server",
    description="Server for running tests on student repositories.",
    version="0.2.0",
    dependencies=[Depends(verify_secret)],
)


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


@app.get("/assignments", tags=["assignments"])
def list_assignments() -> list[Assignment]:
    return test_case_finder.list_assignments()


@app.get("/assignments/{test_suite}.zip", tags=["assignments"])
def download_assignment(test_suite: str) -> FileResponse:
    dir_path = test_case_finder.get_assignment_path(test_suite)
    if dir_path is None:
        raise HTTPException(status_code=404, detail="Test suite not found")

    zip_path = dir_path.with_suffix(".zip")

    dir_mage = dir_last_modified(dir_path).timestamp()

    if not zip_path.is_file() or zip_path.stat().st_mtime < dir_mage:
        with ZipFile(zip_path, "w") as zipf:
            for file in dir_path.rglob("*"):
                zipf.write(file, file.relative_to(dir_path))

    return FileResponse(zip_path)


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

    results = Orchestrator(repo_path, runner, dir_generator).run(assignment_groups)

    return AssignmentResults(name=assignment, user=user, results=results)
