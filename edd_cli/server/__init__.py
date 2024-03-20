from datetime import timedelta
from logging import getLogger
from pathlib import Path
from zipfile import ZipFile

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from ..finder import TestCaseFinder
from ..repository import RepositoryDownloader, RepositoryDownloadException
from ..runner import DockerRunner, Orchestrator, TempDirGeneratorFactory
from ..schema.results import AssignmentResults
from ..schema.tests import Assignment, TestGroup
from ..utils.dir import dir_clear_old, dir_last_modified, dir_size
from .auth import verify_secret
from .settings import settings

logger = getLogger(__name__)

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


@app.get("/assignments/{assignment}.zip", tags=["assignments"])
def download_assignment(assignment: str) -> FileResponse:
    dir_path = test_case_finder.get_assignment_path(assignment)
    if dir_path is None:
        raise HTTPException(status_code=404, detail="Test suite not found")

    zip_path = dir_path.with_suffix(".zip")

    dir_mage = dir_last_modified(dir_path).timestamp()

    if not zip_path.is_file() or zip_path.stat().st_mtime < dir_mage:
        with ZipFile(zip_path, "w") as zipf:
            for file in dir_path.rglob("*"):
                zipf.write(file, file.relative_to(dir_path))

    return FileResponse(zip_path)


class CallbackResponse(BaseModel):
    user: str
    assignment: str


def _run_tests(
    assignment: str,
    user: str,
    clean_run: bool,
    repo_path: Path,
    assignment_groups: list[TestGroup],
) -> AssignmentResults:
    dir_generator = dir_generator_factory.create(
        subpath=Path(assignment, user), cache=not clean_run
    )

    results = Orchestrator(repo_path, runner, dir_generator).run(assignment_groups)

    return AssignmentResults(name=assignment, user=user, results=results)


def _run_tests_tasks(
    assignment: str,
    user: str,
    clean_run: bool,
    repo_path: Path,
    assignment_groups: list[TestGroup],
    callback_url: HttpUrl,
) -> None:
    results = _run_tests(assignment, user, clean_run, repo_path, assignment_groups)
    final_callback_url = str(callback_url) + f"/{assignment}/{user}"
    response = httpx.post(final_callback_url, content=results.model_dump_json())
    logger.info(
        f"Callback to {callback_url} returned {response.status_code}: {response.text}"
    )


run_tests_callback_router = APIRouter()


@run_tests_callback_router.post(
    "{$callback_url}/{$request.path.assignment}/{$request.path.user}", status_code=200
)
def test_result():
    "Callback called by the server to report the results of the tests."


@app.post(
    "/assignments/{assignment}/{user}",
    tags=["assignments"],
    callbacks=run_tests_callback_router.routes,
    responses={200: {"model": AssignmentResults}, 202: {"model": CallbackResponse}},
)
def run_tests(
    assignment: str,
    user: str,
    background_tasks: BackgroundTasks,
    clean_run: bool = False,
    pull_if_exists: bool = True,
    callback_url: HttpUrl | None = None,
) -> AssignmentResults | CallbackResponse:
    assignment_groups = test_case_finder.get_assignment(assignment)

    if assignment_groups is None:
        raise HTTPException(status_code=404, detail="Test suite not found")

    try:
        repo = f"{assignment}-{user}"
        repo_path = repo_downloader.download(repo, pull_if_exists=pull_if_exists)
    except RepositoryDownloadException:
        raise HTTPException(status_code=500, detail="Failed to download repository")

    if callback_url:
        background_tasks.add_task(
            _run_tests_tasks,
            assignment,
            user,
            clean_run,
            repo_path,
            assignment_groups,
            callback_url,
        )
        return CallbackResponse(user=user, assignment=assignment)

    return _run_tests(assignment, user, clean_run, repo_path, assignment_groups)
