"""Extract a path's filesystem metadata in a single stat call."""

from __future__ import annotations

import os
import stat
from typing import Any, Dict, Union

__all__ = ["extract_metadata"]


def extract_metadata(path: Union[str, bytes, "os.PathLike[Any]"]) -> Dict[str, Any]:
    """Return size, mtime, ctime, mode, owner uid, and gid for *path*.

    Why one function instead of a class? The wrapper exists to guarantee a
    single ``os.stat`` call per path and to expose its results under
    self-documenting keys. A class with setters or caching would invite callers
    to re-stat the same path repeatedly; a bare function makes the one-call
    contract explicit.

    Errors are not caught here. A missing path raises ``OSError`` straight
    through — catching and returning ``None`` or an empty dict would make a
    real failure look like "file present but empty", which is the worse of the
    two failures. Callers who want soft failure wrap ``try/except OSError``.
    """

    # Suppress the Windows-only ``follow_symlinks`` debate entirely: on
    # Windows this argument is simply ignored, so passing it unconditionally
    # is harmless and keeps the behaviour deterministic on POSIX.
    info = os.stat(path, follow_symlinks=False)

    return {
        "size": info.st_size,
        "mtime": info.st_mtime,
        "ctime": info.st_ctime,
        "mode": info.st_mode,
        "uid": info.st_uid,
        "gid": info.st_gid,
        "is_symlink": stat.S_ISLNK(info.st_mode),
    }
