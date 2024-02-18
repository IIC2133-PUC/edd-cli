from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, PrivateAttr


class Assignment(BaseModel):
    name: str
    updated_at: datetime


class PathMapping(BaseModel):
    source: Path
    target: Path

    def __repr__(self):
        return f"{self.source}:{self.target}"


class ResolvedTestStage(BaseModel):
    files: list[PathMapping]
    command: list[str]


def resolve_paths(paths: list[str | PathMapping], base_dir: Path):
    resolved_paths: list[PathMapping] = []

    for path in paths:
        if isinstance(path, PathMapping):
            source = (base_dir / path.source).resolve()
            resolved_path = PathMapping(source=source, target=path.target)
            resolved_paths.append(resolved_path)
        elif "*" in path:
            for glob_path in base_dir.resolve().glob(path):
                target = glob_path.relative_to(base_dir)
                resolved_path = PathMapping(source=glob_path, target=target)
                resolved_paths.append(resolved_path)
        else:
            source = (base_dir / path).resolve()
            resolved_path = PathMapping(source=source, target=Path(path))
            resolved_paths.append(resolved_path)

    return resolved_paths


class TestStage(BaseModel):
    require: list[str | PathMapping]
    include: list[str | PathMapping]
    command: list[str]
    time_it: bool = False

    def with_resolved_paths(self, include_dir: Path, require_dir: Path):
        files: list[PathMapping] = []
        files.extend(resolve_paths(self.include, include_dir))
        files.extend(resolve_paths(self.require, require_dir))
        return ResolvedTestStage(files=files, command=self.command)


class AbstractPipeline(BaseModel):
    name: str | None
    steps: list[TestStage]

    _dir: Path = PrivateAttr(default=Path.cwd())

    def set_dir_path(self, path: Path):
        self._dir = path

    @property
    def display_name(self):
        return self.name or self.path.name

    @property
    def path(self):
        if self._dir is None:
            raise Exception("dir is not set")
        return self._dir


class TestCase(AbstractPipeline):
    pass


class TestGroup(AbstractPipeline):
    _tests: list[TestCase] = PrivateAttr(default_factory=list)

    def add_test(self, test: TestCase):
        self._tests.append(test)

    @property
    def tests(self):
        return self._tests
