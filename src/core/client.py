"""The main class of the bot

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import os
import asyncio
import traceback
import logging
from datetime import datetime
from typing import Any, Sequence

import discord
from discord.ext import commands
from discord.app_commands import errors

from data import Configuration
from utils import maybe
from .context import BefriContext
from .i18n import LocalizationProvider
from .loader import ExtensionLoader
from .logger import Logger

__all__ = ("Befri",)

logging.basicConfig(level=logging.ERROR)


class Befri(commands.Bot):
    """The core of the Berfi
    
    Parameters
    ----------
    config: :class:`Configuration`
        The configuration of the bot"""

    __version__ = "0.0.1a"

    __developer__ = "stngularity"
    __developer_url__ = "https://github.com/stngularity"

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(Befri, cls).__new__(cls)
            cls.instance.__init__(*args, **kwargs)

        return cls.instance

    def __init__(self, config: Configuration, **kwargs) -> None:
        self.config = config
        self.prefix = config.prefix_f or "b!"
        self.app_commands: dict[str, discord.app_commands.AppCommand] = dict()

        self.logger = Logger(
            fl_level=Logger.get_level(config.logger.file.level_f),
            fl_filename=config.logger.file.filename_f or "logs/%d.%m.%Y.log",
            cl_level=Logger.get_level(config.logger.console.level_f)
        )

        self.i18n = LocalizationProvider(self.logger)
        self.loader = ExtensionLoader(self, self.logger)

        super().__init__(
            command_prefix=commands.when_mentioned_or(self.prefix),
            help_command=None,
            intents=discord.Intents.all(),
            max_messages=config.cache.max_messages_f or 1000,
            owner_ids=config.developers_f or list(),
            allowed_mentions=discord.AllowedMentions(
                everyone=config.allowed_mentions.b_everyone,
                users=config.allowed_mentions.b_users,
                roles=config.allowed_mentions.b_roles,
                replied_user=config.allowed_mentions.b_replied_user
            ),
            status=(
                discord.Status[config.presence.status_f]
                if config.presence.status_f in discord.Status._enum_member_names_  # type: ignore
                else None
            ),
            activity=self._get_activity(),
            **kwargs
        )

    async def on_connect(self) -> None:
        """Handles the connection to Discord API event"""
        self.logger.debug(f"Connected to Discord API as {self.user} ({maybe(self.user).id})")

    async def on_ready(self) -> None:
        """Handles the bot's ready event"""
        self.logger.info("Ready!")
        await asyncio.create_task(self.sync_commands())

    async def on_command_error(self, _, exception: commands.CommandError) -> None:
        """Handles the bot's errors"""
        component = traceback.TracebackException.from_exception(exception)
        print(dir(component))
        self.logger.critical("Unexpected error during command execution:", component="component")
        self.logger.write_exception(exception)

    async def sync_commands(self) -> None:
        """Tries to synchronize slash commands that were registered by the bot
        and commands that were registered by Discord"""
        self.logger.debug("The command synchronization process has begun")
        start = datetime.today()

        await self.tree.set_translator(self.i18n)

        try:
            app_commands = await self.tree.sync()
            self.app_commands = {x.name: x for x in app_commands}
        except errors.CommandSyncFailure as error:
            self.logger.critical("Failed to synchronize global bot's commands:")
            self.logger.write_exception(error)
        except Exception as error:
            self.logger.critical("An error occurred while synchronizing commands:")
            self.logger.write_exception(error)
        else:
            took = round((datetime.today() - start).total_seconds(), 2)
            self.logger.info(f"The slash commands have been successfully synchronized in {took}s")

    async def run_tasks(self) -> None:
        """Starts tasks that need to be done right now"""
        now = datetime.now().astimezone()
        for id, task in self.loader.tasks.items():
            if task.count is not None and task.count <= 0:
                self.loader.remove_task(id)
                continue

            if not task.can_run(now):
                continue

            await task.callback(self)

        await asyncio.sleep(1)
        await asyncio.create_task(self.run_tasks())

    async def start_bot(self) -> None:
        """Loads all localization package and extensions. After that starts the bot"""
        self.i18n.scan_for_localization()
        self.logger.info(f"Loaded {len(self.i18n.packages)} localization packages")

        self.loader.scan_for_extensions()
        self.loader.load_all(localizer=self._localize_something)
        loaded = len([x for x in self.loader.extensions.values() if x.loaded])
        self.logger.info(f"Loaded {loaded} extensions out of {len(self.loader.extensions)}")

        token = os.environ.get("BOT_TOKEN")
        if token is None:
            return self.logger.critical("The token isn't specified. Specify the token before launching the bot")

        try:
            await self.start(token)
        except discord.LoginFailure:
            self.logger.critical("The token is incorrect. Specify another token before launching the bot")
            await self.http.close()
        
        await asyncio.create_task(self.run_tasks())

    def _localize_something(self, command: commands.HybridCommand, field: str) -> str | Sequence[str] | None:
        if field == "aliases":
            output = set()
            for package in self.i18n.packages.values():
                name = package.data.get(f"commands.{command.name}.name", type=str)
                output.add(name)
                aliases = package.data.get(f"commands.{command.name}.aliases", [], type=list)
                output.update(aliases)

            if None in output:
                output.remove(None)

            if command.name in output:
                output.remove(command.name)

            return list(output)

    async def get_context(
        self,
        origin: discord.Message | discord.Interaction,
        /,
        *,
        cls: type[commands.Context] = BefriContext
    ) -> Any:
        """`Any`: Gets context for message-commands"""
        return await super().get_context(origin, cls=cls)

    def _get_activity(self) -> discord.BaseActivity | None:
        """`Optional`[`BaseActivity`]: Returns the activity of the bot"""
        activity_type: str | None = self.config.presence.activity.type_f
        if activity_type == "game":
            return discord.Game(self.config.presence.activity.name_f)

        if activity_type in ["listen", "watch", "compete"]:
            return discord.Activity(type=discord.ActivityType[activity_type.rstrip("e") + "ing"],
                                    name=self.config.presence.activity.name_f)

        if activity_type == "stream":
            return discord.Streaming(name=self.config.presence.activity.name_f,
                                     url=self.config.presence.activity.url_f)

        if activity_type == "custom":
            return discord.CustomActivity(self.config.presence.activity.name_f)
