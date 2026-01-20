"""Utilities for working with null values

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

from typing import Any, TypeVar

__all__ = ("maybe",)

T = TypeVar('T')

class _Maybe:
    def __getattribute__(self, _) -> "_Maybe":
        return self
    
    def __call__(self, *_, **__) -> Any:
        return None

def maybe(data: T | None) -> T:
    """The same as `?.` in normal languages"""
    return _Maybe() if data is None else data  # type: ignore
