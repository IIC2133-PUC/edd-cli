from typing import IO, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from hashlib import _Hash

file_digest: "Callable[[IO, Callable[[], _Hash]], None]"

try:
    from hashlib import file_digest  # type: ignore

except ImportError:

    def file_digest(fileobj: IO, digest: Callable[[], "_Hash"], /):
        hash_func = digest()
        while True:
            chunk = fileobj.read(8192)
            if not chunk:
                break
            hash_func.update(chunk)
