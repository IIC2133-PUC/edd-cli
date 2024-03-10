from pathlib import Path
from ..schema.tests import PathMapping


def path_to_show(path: PathMapping) -> Path:
    # base case: not paths in common
    if path.source.name != path.target.name:
        return Path(path.source.name)

    # show common parts
    common = []
    i = 1
    while len(path.source.parts) >= i and len(path.target.parts) >= i and path.source.parts[-i] == path.target.parts[-i]:
        common.append(path.source.parts[-i])
        i += 1
    return Path(*common[::-1])
