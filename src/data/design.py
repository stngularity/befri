"""Interface for working with design configuration

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import re

from .config import Configuration

__all__ = ("Design", "EmojisFormat")


class Design:
    """The interface for working with `design.yml` file"""

    @staticmethod
    def set_data(data: Configuration) -> None:
        """Sets the content of the `design.yml` file
        
        Parameters
        ----------
        data: :class:`Configuration`
            The content of `design.yml` file as configuration"""
        Design._data = data

    @staticmethod
    def reload() -> None:
        """Reloads the `design.yml` file"""
        if Design._data is not None:
            Design._data.reload()

    @staticmethod
    def _hex_to_number(hex: str) -> int:
        if re.match(r"[a-f0-9]{6}", hex.lower()) is None:
            return 0

        return int.from_bytes(bytes.fromhex(hex), "big")

    @staticmethod
    def color(name: str) -> int:
        """`str`: Returns color by specified :param:`name`"""
        if Design._data is None:
            return 0

        return Design._hex_to_number(Design._data.get(f"colors.{name}", type=str, default=""))

    @staticmethod
    def emoji(name: str) -> str:
        """`str`: Returns emoji by specified :param:`name`"""
        if Design._data is None:
            return ""

        return Design._data.get(f"emojis.{name}", type=str, default="")

    @staticmethod
    def icon(name: str) -> str:
        """`str`: Returns icon by specified :param:`name`"""
        if Design._data is None:
            return ""

        return Design._data.get(f"icons.{name}", type=str, default="")

class EmojisFormat:
    """The interface for using emojis in localization"""

    def __getattr__(self, name: str) -> str:
        return Design.emoji(name)
