"""The message builder

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Self

import discord
from discord import MediaGalleryItem, ui

if TYPE_CHECKING:
    from core import BefriContext

__all__ = ("ViewBuilder", "MessageBuilder", "container", "message", "thumbnail", "button", "select", "gallery_item")

MISSING: Any = discord.utils.MISSING


class ViewBuilder:
    """Class for creating views"""

    def __init__(self) -> None:
        self._children = []

    def text(self, content: str | None, *, id: int | None = None) -> Self:
        if content is None:
            return self

        self._children.append(ui.TextDisplay(content, id=id))
        return self

    def separator(
        self,
        visible: bool = True,
        spacing: discord.SeparatorSpacing = discord.SeparatorSpacing.small
    ) -> Self:
        self._children.append(ui.Separator(visible=visible, spacing=spacing))
        return self

    def action_row(self, *children: ui.Item, id: int | None = None) -> Self:
        self._children.append(ui.ActionRow(*children, id=id))
        return self

    def section(self, *children: str, accessory: ui.Item, id: int | None = None) -> Self:
        self._children.append(ui.Section(*children, accessory=accessory, id=id))
        return self

    def gallery(self, *items: MediaGalleryItem, id: int | None = None) -> Self:
        self._children.append(ui.MediaGallery(*items, id=id))
        return self

    def file(self, media: str | discord.File | discord.UnfurledMediaItem, *, spoiler: bool = False) -> Self:
        self._children.append(ui.File(media, spoiler=spoiler))
        return self

class ContainerBuilder(ViewBuilder):
    """Class for creating containers"""

    def __init__(self, color: int | None = None, spoiler: bool = False) -> None:
        super().__init__()
        self._color = color
        self._spoiler = spoiler

    def build(self, *, id: int | None = None) -> ui.Container:
        return ui.Container(
            *self._children,
            accent_color=self._color,
            spoiler=self._spoiler,
            id=id
        )

class MessageBuilder(ViewBuilder):
    """Class for creating messages"""

    def __init__(self, content: str | None = None) -> None:
        super().__init__()
        self._content = content
        self._poll: discord.Poll | None = None
    
    def container(self, container: ui.Container | ContainerBuilder) -> Self:
        if isinstance(container, ContainerBuilder):
            container = container.build()

        self._children.append(container)
        return self

    def poll(
        self,
        question: str,
        answers: list[str | tuple[str, discord.PartialEmoji | discord.Emoji | str]],
        duration: datetime.timedelta,
        *,
        multiple: bool = False,
        emoji: discord.PartialEmoji | discord.Emoji | None
    ) -> Self:
        self._poll = discord.Poll(discord.PollMedia(question, emoji), duration, multiple=multiple)
        for answer in answers:
            a_text = answer if isinstance(answer, str) else answer[0]
            a_emoji = None if isinstance(answer, str) else answer[1]
            self._poll.add_answer(text=a_text, emoji=a_emoji)

        return self

    def build_view(self, *, timeout: float = 180) -> ui.LayoutView:
        view = ui.LayoutView(timeout=timeout)
        for child in self._children:
            view.add_item(child)
        
        return view

    async def send(
        self,
        ctx: "BefriContext",
        *,
        delete_after: float | None = None,
        view_timeout: float = 180
    ) -> discord.Message:
        return await ctx.send(
            content=self._content,
            delete_after=delete_after,
            view=None if len(self._children) == 0 else self.build_view(timeout=view_timeout),
            poll=self._poll or MISSING
        )

def container(color: int | None = None, spoiler: bool = False) -> ContainerBuilder:
    return ContainerBuilder(color, spoiler)

def message(content: str | None = None) -> MessageBuilder:
    return MessageBuilder(content)

def thumbnail(
    media: str | discord.File | discord.UnfurledMediaItem,
    *,
    description: str | None = None,
    spoiler: bool = False
) -> ui.Thumbnail:
    return ui.Thumbnail(media, description=description, spoiler=spoiler)

def gallery_item(
    media: str | discord.File | discord.UnfurledMediaItem,
    *,
    description: str | None = None,
    spoiler: bool = False
) -> discord.MediaGalleryItem:
    return discord.MediaGalleryItem(media, description=description, spoiler=spoiler)

def button(
    label: str | None = None,
    emoji: discord.PartialEmoji | discord.Emoji | str | None = None,
    style: discord.ButtonStyle = discord.ButtonStyle.secondary,
    url: str | None = None,
    *,
    row: int | None = None,
    disabled: bool = False,
    id: int | None = None,
    callback: Callable[[discord.Interaction], Coroutine[None, None, Any]] | None = None
) -> ui.Button:
    button = ui.Button(style=style, label=label, disabled=disabled, id=id, url=url, emoji=emoji, row=row)
    if callback is not None:
        button.__setattr__("callback", callback)

    return button

def select(
    id: str,
    options: list[discord.SelectOption],
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    *,
    row: int | None = None,
    required: bool = True,
    disabled: bool = False,
    callback: Callable[[discord.Interaction], Coroutine[None, None, Any]] | None = None
) -> ui.Select:
    select = ui.Select(custom_id=id, placeholder=placeholder, min_values=min_values, max_values=max_values,
                       options=options, disabled=disabled, required=required, row=row)

    if callback is not None:
        select.__setattr__("callback", callback)

    return select
