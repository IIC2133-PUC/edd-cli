import hashlib
import shutil
from pathlib import Path

from ..schema.schema import PathMapping, ResolvedTestStage


class TempDirGeneratorFactory:
    def __init__(self, base_path: Path):
        self._base_path = base_path

    def create(self, *, cache: bool, subpath: Path = Path()):
        return TempDirGenerator(self._base_path / subpath, cache)


class TempDirGenerator:
    "Creates temporary directories for test stages."

    def __init__(self, base_path: Path, cache: bool):
        self.base_path = base_path

        self._cache = cache

    def create(self, stage: ResolvedTestStage):
        file_hash = hashlib.sha256()
        for file in stage.files:
            hashlib.file_digest(open(file.source, "rb"), lambda: file_hash)

        command_hash = hashlib.md5()
        for command in stage.command:
            command_hash.update(command.encode())

        dir_name = f"{command_hash.hexdigest()}-{file_hash.hexdigest()}"
        path = (self.base_path / dir_name).resolve()

        cached = self._cache and path.exists() and path.is_dir()

        if cached and not self._cache:
            shutil.rmtree(path)

        return TempDir(path, stage.files, cached)


class TempDir:
    "Temporary directory with files. Does not exist until `prepare` is called."

    def __init__(self, path: Path, files: list[PathMapping], cached: bool):
        self.path = path
        self.cached = cached
        self._files = files

    def prepare(self):
        if self.path.exists():
            shutil.rmtree(self.path)

        for file in self._files:
            target = self.path / file.target
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(file.source, target)

        return self.path
