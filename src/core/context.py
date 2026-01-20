"""Implementation of the context with some changes

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

from typing import TYPE_CHECKING, Any, Sequence

import discord
from discord import ui
from discord.ext import commands
from discord.ext.commands.view import StringView

from data import Design
from utils import message, container
from .i18n import ContextLocalization

if TYPE_CHECKING:
    from .client import Befri

__all__ = ("BefriContext",)

MISSING: Any = discord.utils.MISSING


class BefriContext(commands.Context):
    """Implementation of the context with some changes"""

    bot: "Befri"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    @property
    def i18n(self) -> ContextLocalization:
        """:class:`ContextLocalization`: Reference to localization for the current context"""
        language = "en-US"  # TODO: Get language from database
        if self.interaction is not None:
            language = self.interaction.locale.value
        
        package = self.bot.i18n.packages.get(language) or self.bot.i18n.packages["en-US"]
        return ContextLocalization(package=package, ctx=self)

    def i(self, key: str, **kwargs: Any) -> str:
        return self.i18n.get(key, **kwargs)

    @staticmethod
    def fake_from_interaction(
        interaction: discord.Interaction,
        *,
        message: discord.Message | None = None,
        command: commands.Command[Any, ..., Any] | None = None
    ) -> "BefriContext":
        """:class:`BefriContext`: Creates and returns a context instance from the interaction"""
        return BefriContext(message=(message or interaction.message), bot=interaction.client, view=StringView(""),
                            command=(command or interaction.command), interaction=interaction)

    async def send(
        self,
        content: str | None = None,
        *,
        file: discord.File | None = None,
        files: Sequence[discord.File] | None = None,
        delete_after: float | None = None,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage | None = None,
        view: ui.LayoutView | ui.View | None = None,
        poll: discord.Poll | None = None,
    ) -> discord.Message:
        """`Message`: Sends a message to the channel where the message
        that called the command is located"""
        if self.interaction is None:
            return await super().send(  # type: ignore
                content=content,
                file=file,
                files=files,
                delete_after=delete_after,
                reference=reference or self.message,
                view=view,
                poll=poll
            )
    
        return await super().send(  # type: ignore
            content=content,
            file=file,
            files=files,
            delete_after=delete_after,
            view=view,
            ephemeral=True
        )

    async def send_error(
        self,
        *,
        type: str | None = None,
        text: str | None = None,
        icon: str = "error",
        **kwargs
    ) -> discord.Message:
        """`Message`: Sends error to user"""
        cont = container(Design.color("error"))
        text = text or self.i18n.get_text(f"errors.{type}", **kwargs)
        cont.text(f"{Design.emoji(icon if type is None else ('error_' + type))} {text}")
        return await message().container(cont.build()).send(self)
