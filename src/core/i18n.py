"""Managing bot localization packages

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import os
from dataclasses import dataclass
from typing import Any, Final

from discord import Locale
from discord.ext import commands
from discord.app_commands import Translator, TranslationContextLocation, locale_str
from discord.app_commands.translator import TranslationContextTypes

from data import Configuration, EmojisFormat
from utils import from_root
from .logger import Logger

__all__ = ("Author", "LocalizationPackage", "LocalizationProvider", "ContextLocalization")


@dataclass
class Author:
    """The data class for storing the localization package author
    
    Parameters
    ----------
    name: `str`
        Name of the localization package author. Stored by the `name` key. For example, `stngularity`
    
    email: `Optional`[`str`]
        Email address of the localization package author. Stored by the `email` key. For example,
        `stngularity@gmail.com`

    discord: `Optional`[`int`]
        Discord ID of the author of the localization package. Stored by the `discord` key. For example,
        `813065322453925940`
    
    github: `Optional`[`str`]
        The GitHub username of the author of the localization package. Stored by the `github` key. For example,
        `stngularity`"""

    name: str
    email: str | None
    discord: int | None
    github: str | None

    def __repr__(self) -> str:
        return f"<Author name={self.name} email={self.email} discord={self.discord} github={self.github}>"

    def __str__(self) -> str:
        return self.name

    @property
    def github_url(self) -> str | None:
        """`str`: The URL of the GitHub user's profile"""
        return None if self.github is None else f"https://github.com/{self.github}"

@dataclass
class LocalizationPackage:
    """The data class for storing the localization packages
    
    Parameters
    ----------
    filename: `str`
        The name of localization package. For example, `english.yml`
    
    natural_name: `str`
        The natural name of localization package. Stored by the `natural_name` key. For example, `English`
    
    discord_locale: `str`
        The locale name in Discord API. Stored by the `discord_locale` key. For example, `en-US`
    
    authors: `list`[:class:`Author`]
        The object of the localization package author
        
    data: :class:`Configuration`
        Localization package data"""

    filename: str
    natural_name: str
    discord_locale: str
    authors: list[Author]
    data: Configuration

    def __repr__(self) -> str:
        return f"<LocalizationPackage {self.filename} discord_locale={self.discord_locale} authors={self.authors}>"

    def __str__(self) -> str:
        return f"{self.natural_name} [{self.discord_locale}] ({self.filename})"

class LocalizationProvider(Translator):
    """The class of localization provider.

    It is also an implementation of :class:`Translator`"""

    LANGUAGES_FOLDER: Final[str] = from_root("languages")

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._packages: dict[str, LocalizationPackage] = dict()

    @property
    def packages(self) -> dict[str, LocalizationPackage]:
        """A dictionary where the key is the locale code and the value is the localization package object"""
        return self._packages

    def scan_for_localization(self) -> None:
        """Scans the bot's languages folder and registers everything"""
        for file in os.listdir(self.LANGUAGES_FOLDER):
            path = os.path.join(self.LANGUAGES_FOLDER, file)
            if not os.path.isfile(path) or not file.endswith((".yml", ".yaml")):
                continue

            data = Configuration.load(path)
            if not data.contains("natural_name", "discord_locale", "authors"):
                self._logger.error(f"Failed to load {file} localization package: one of the required keys is missing")
                continue

            self._packages[data.discord_locale] = package = LocalizationPackage(
                filename=data._path,
                natural_name=data.natural_name,
                discord_locale=data.discord_locale,
                authors=[Author(
                    name=x["name"],
                    email=x.get("email"),
                    discord=x.get("discord"),
                    github=x.get("github")
                ) for x in data.authors],
                data=data
            )

            authors = ", ".join(str(x) for x in package.authors)
            self._logger.debug(f"Loaded `{package.natural_name}` localization package by `{authors}`")

    async def unload(self) -> None:
        """Unloads localization packages"""
        self._packages.clear()

    async def translate(self, string: locale_str, locale: Locale, ctx: TranslationContextTypes) -> str | None:
        """`Optional`[`str`]: Gets the translated text for specified string"""
        if locale.value not in self._packages:
            return
        
        package = self._packages[locale.value]
        if ctx.location == TranslationContextLocation.command_name:
            key = f"commands.{ctx.data.name}.name"
        
        if ctx.location == TranslationContextLocation.command_description:
            key = f"commands.{ctx.data.name}.description"

        if ctx.location == TranslationContextLocation.group_name:
            key = f"groups.{ctx.data.name}.name"
        
        if ctx.location == TranslationContextLocation.group_description:
            key = f"groups.{ctx.data.name}.description"
        
        if ctx.location == TranslationContextLocation.parameter_name:
            key = f"commands.{ctx.data.command.name}.arguments.{ctx.data.name}.name"
        
        if ctx.location == TranslationContextLocation.parameter_description:
            key = f"commands.{ctx.data.command.name}.arguments.{ctx.data.name}.description"
        
        if ctx.location == TranslationContextLocation.choice_name:
            key = string.extras.get("key")
        
        if key is None:
            return string.message
        
        return package.data.get(key, string.message, type=str).format(e=EmojisFormat())

class ContextLocalization:
    """Class for accessing localization from context"""

    def __init__(self, package: LocalizationPackage, ctx: commands.Context) -> None:
        self._package = package
        self._ctx = ctx

    def get(self, key: str, **kwargs) -> str:
        """`str`: Gets the translated text for the specified :param:`key`
        
        The key starts with the current command
        
        Parameters
        ----------
        key: `str`
            The dot-separated string key to get text from localization"""
        return key if self._ctx.command is None else self.get_text(f"commands.{self._ctx.command.name}.{key}", **kwargs)

    def get_text(self, key: str, default: Any | None = None, **kwargs) -> str:
        """`str`: Gets the translated text for the specified :param:`key`

        Parameters
        ----------
        key: `str`
            The dot-separated string key to get text from localization"""
        output = self._package.data.get(key, default or key, type=str)
        return output.format(e=EmojisFormat(), developer=self._ctx.bot.__developer__,
                             developer_url=self._ctx.bot.__developer_url__, **kwargs)

    def get_list(self, key: str, **kwargs) -> list[Any]:
        """`list`[`Any`]: Gets the translated list for the specified :param:`key`

        Parameters
        ----------
        key: `str`
            The dot-separated string key to get text from localization"""
        output = self._package.data.get(key, list(), type=list)
        return [el.format(e=EmojisFormat(), **kwargs) if isinstance(el, str) else el for el in output]

    def get_bool(self, value: bool) -> str:
        """`str`: Gets the translated boolean value"""
        return self.get_text(f"boolean.{'yes' if value else 'no'}") or "None"
