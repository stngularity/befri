"""Utilities for working with paths

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import os
from pathlib import Path
from typing import IO, Any

__all__ = ("from_root", "ropen")


def from_root(*path: str) -> str:
    """`str`: Returns path from project's source root to specified object"""
    return os.path.join(Path(__file__).resolve().parent.parent.parent, *path)

def ropen(*path: str, mode: str) -> IO[Any]:
    """`str`: Gets the path via :func:`from_root` and opens it"""
    return open(from_root(*path), mode, encoding=("" if "b" in mode else "utf8"))
