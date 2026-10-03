"""Native path identity for read-only boundaries and new output locations."""
import ctypes
import os
from pathlib import Path
import sys


def canonical(path: Path) -> Path:
    """Match native Unix canonical spelling; Python preserves case aliases on macOS."""
    if b"\0" in os.fsencode(path):
        raise ValueError("Embedded null byte in path")
    if sys.platform != "darwin":
        return path.resolve(strict=True)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.realpath.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
    libc.realpath.restype = ctypes.c_void_p
    libc.free.argtypes = [ctypes.c_void_p]
    pointer = libc.realpath(os.fsencode(path), None)
    if not pointer:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(path))
    try:
        return Path(os.fsdecode(ctypes.string_at(pointer)))
    finally:
        libc.free(pointer)


def canonical_missing(path: Path) -> Path:
    """Resolve native spelling while permitting missing final components."""
    try:
        # Native stat preserves ENOTDIR/denial before Python normalizes '..'.
        path.stat()
        return canonical(path)
    except FileNotFoundError:
        path = path.resolve(strict=False)
    suffix = []
    while True:
        try:
            return canonical(path).joinpath(*reversed(suffix))
        except FileNotFoundError:
            if path == path.parent:
                raise
            suffix.append(path.name)
            path = path.parent
