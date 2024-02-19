import shutil
from datetime import datetime, timedelta
from pathlib import Path


def dir_last_use(dir: Path) -> datetime:
    "Returns the last time the directory was used."
    return max(
        (datetime.fromtimestamp(path.stat().st_atime) for path in dir.rglob("*")),
        default=datetime.fromtimestamp(0),
    )


def dir_last_modified(dir: Path) -> datetime:
    "Returns the last time the directory was modified."
    return max(
        (datetime.fromtimestamp(path.stat().st_mtime) for path in dir.rglob("*")),
        default=datetime.fromtimestamp(0),
    )


def dir_size(dir: Path) -> int:
    "Returns the size of the directory in bytes."
    return sum(f.stat().st_size for f in dir.glob("**/*") if f.is_file())


def dir_clear_old(dir: Path, min_age: timedelta):
    "Clears sub-directories older than `min_age` seconds in the given directory."
    for subdir in dir.glob("*"):
        if not subdir.is_dir():
            continue

        age = datetime.now() - dir_last_use(subdir)

        if min_age < age:
            shutil.rmtree(subdir)
