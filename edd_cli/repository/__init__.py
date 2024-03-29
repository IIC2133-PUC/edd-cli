from logging import getLogger
from pathlib import Path
from subprocess import Popen

from rich.progress import Progress, SpinnerColumn, TextColumn

logger = getLogger(__name__)


class RepositoryDownloadException(Exception):
    pass


class RepositoryDownloader:
    def __init__(self, org: str, download_dir: Path):
        self.org = org
        self.download_dir = download_dir.resolve()

    def download(self, repo: str, *, pull_if_exists: bool = True):
        download_path = self.download_dir / self.org / repo
        download_path.parent.mkdir(parents=True, exist_ok=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}. "),
            transient=True,
        ) as progress:
            if (download_path / ".git").exists():
                if not pull_if_exists:
                    logger.info(f"Repository {self.org}/{repo} already downloaded")
                    return download_path

                progress.add_task(f"Pulling repository {repo}")
                process = Popen(["git", "pull", "-f"], cwd=download_path)
            else:
                progress.add_task(f"Cloning repository {repo}")
                process = Popen(
                    ["gh", "repo", "clone", f"{self.org}/{repo}", repo],
                    cwd=download_path.parent,
                )

            return_code = process.wait()

            if return_code != 0:
                raise RepositoryDownloadException(
                    f"Failed to download repository {repo}"
                )

        logger.info(f"Repository {self.org}/{repo} downloaded")

        return download_path
