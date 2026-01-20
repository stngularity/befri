"""Logger for events related to the bot

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import sys
import traceback
from enum import IntEnum, auto
from pathlib import Path
from datetime import datetime
from typing import Final

from rich.console import Console
from rich.theme import Theme

from utils import ropen

__all__ = ("LoggerLevel", "Logger")


class LoggerLevel(IntEnum):
    """Enumeration of all levels of bot events"""

    DISABLED = -1
    INFO = 0
    WARNING = WARN = auto()
    ERROR = auto()
    CRITICAL = CRIT = auto()
    DEBUG = auto()

class Logger:
    """A logger of bot-related events"""

    CONSOLE: Final[Console] = Console(theme=Theme({
        "info": "blue",
        "warning": "yellow",
        "error": "red",
        "critical": "black on red",
        "debug": "bright_black",
        "gray": "bright_black"
    }), soft_wrap=True)

    FILE_FORMAT: Final[str] = "[{time}] [{level}] {component}: {message}\n"
    CONSOLE_FORMAT: Final[str] = "\\[{time}] [{level}]\\[ {level:9}][/] [gray]{component}:[/] [white]{message}[/]"

    FILE_DATETIME_FORMAT: Final[str] = "%d.%m.%Y %H:%M:%S.%f %z"
    CONSOLE_DATETIME_FORMAT: Final[str] = "%d.%m.%Y %H:%M:%S %z"

    def __init__(
        self,
        *,
        fl_level: LoggerLevel = LoggerLevel.DEBUG,
        fl_filename: str = "logs/%d.%m.%Y.log",
        cl_level: LoggerLevel = LoggerLevel.CRITICAL
    ) -> None:
        self._fl_level = fl_level
        self._fl_filename = fl_filename
        self._cl_level = cl_level

        if fl_level != LoggerLevel.DISABLED and len(fl_filename.split("/")) > 1:
            Path(fl_filename).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_level(value: str | None) -> LoggerLevel:
        """:class:`LoggerLevel`: Searches for and returns the logger level by the specified :param:`value`"""
        try:
            return LoggerLevel.DISABLED if not value else LoggerLevel[value.upper()]
        except KeyError:
            return LoggerLevel.DISABLED

    def write_file_header(self) -> None:
        """Writes header to logs file"""
        if self._fl_level == LoggerLevel.DISABLED:
            return

        now = datetime.now().astimezone()
        with ropen(now.strftime(self._fl_filename), mode="a") as writer:
            writer.write(f"#Date: {now.strftime(self.FILE_DATETIME_FORMAT)}\n")
            writer.write("#Fields: time level component message\n")

    def write(self, message: str, *, level: LoggerLevel, component: str | None = None) -> None:
        """Writes specified :param:`message` to logs"""
        now = datetime.now().astimezone()
        component = component or Path(sys._getframe(2).f_code.co_filename).name[:-3]

        if level <= self._cl_level:
            self.CONSOLE.print(self.CONSOLE_FORMAT.format(
                time=now.strftime(self.CONSOLE_DATETIME_FORMAT),
                level=level.name.lower(),
                component=component,
                message=message
            ))

        if level > self._fl_level:
            return

        with ropen(now.strftime(self._fl_filename), mode="a") as writer:
            writer.write(self.FILE_FORMAT.format(
                time=now.strftime(self.FILE_DATETIME_FORMAT),
                level=level.name.lower(),
                component=component,
                message=message
            ))

    def write_exception(self, exception: Exception) -> None:
        """"Writes specified :param:`exception` to logs"""
        now = datetime.now().astimezone()
        traceback_e = traceback.TracebackException.from_exception(exception)

        if LoggerLevel.CRITICAL <= self._cl_level:
            self.CONSOLE.print("".join(traceback_e.format()))

        if LoggerLevel.CRITICAL <= self._fl_level:
            return

        with ropen(now.strftime(self._fl_filename), mode='a') as writer:
            writer.write("#traceback:start\n")
            writer.write("".join(traceback_e.format()))
            writer.write("#traceback:end\n")

    def info(self, message: str, *, component: str | None = None) -> None:
        """Writes specified informative :param:`message` to logs"""
        self.write(message, level=LoggerLevel.INFO, component=component)

    def warning(self, message: str, *, component: str | None = None) -> None:
        """Writes specified warning :param:`message` to logs"""
        self.write(message, level=LoggerLevel.WARNING, component=component)

    def error(self, message: str, *, component: str | None = None) -> None:
        """Writes specified error :param:`message` to logs"""
        self.write(message, level=LoggerLevel.ERROR, component=component)

    def critical(self, message: str, *, component: str | None = None) -> None:
        """Writes specified critical errror :param:`message` to logs"""
        self.write(message, level=LoggerLevel.CRITICAL, component=component)

    def debug(self, message: str, *, component: str | None = None) -> None:
        """Writes specified debug :param:`message` to logs"""
        self.write(message, level=LoggerLevel.DEBUG, component=component)
