from logging import getLogger
from pathlib import Path
from subprocess import Popen

from rich.progress import Progress, SpinnerColumn, TextColumn

logger = getLogger(__name__)

download_progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}. "),
    transient=True,
)


class RepositoryDownloader:
    def __init__(self, org: str, download_dir: Path):
        self.org = org
        self.download_dir = download_dir.resolve()

    def download(self, repo: str):
        download_path = self.download_dir / self.org / repo
        download_path.parent.mkdir(parents=True, exist_ok=True)

        with download_progress as progress:
            if (download_path / ".git").exists():
                progress.add_task(f"Pulling repository {repo}")
                process = Popen(["git", "pull", "-f"], cwd=download_path)
            else:
                progress.add_task(f"Cloning repository {repo}")
                url = f"git@github.com:{self.org}/{repo}.git"
                process = Popen(["git", "clone", url, repo], cwd=download_path.parent)

            return_code = process.wait()
            if return_code != 0:
                raise Exception(f"Failed to download repository {repo}")

        logger.info(f"Repository {self.org}/{repo} downloaded")

        return download_path

        return download_path
