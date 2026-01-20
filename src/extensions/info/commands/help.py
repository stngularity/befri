"""`/help` command.

I'm tired...  I'm really tired...  What am I doing wrong?  Why is the simplest
`help` command so complicated?

[ `/help` ]
If called without arguments, it provides brief help on categories (extensions)
and commands in them.

[ `/help [category]` ]
If a category is specified in the  arguments, it provides a description of the
category and a list of commands with their descriptions.

[ `/help [command]` ]
If a command is specified in the arguments,   it provides a description of the
command, a list of command aliases, usage help, and usage examples.

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

# TODO: help for commands

from typing import Any, AsyncGenerator, Callable, Coroutine

import discord
from discord import app_commands
from discord.app_commands import locale_str as ls
from discord.ext import commands

from core import BefriContext, Extension
from data import Design as D
from utils import MessageBuilder, button, container, message

__all__ = ("help",)

CMB = Coroutine[None, None, MessageBuilder]


@commands.hybrid_command(name=ls("help"), description=ls("Reference for bot commands and command categories"))
@app_commands.rename(category=ls("category"), command=ls("command"))
@app_commands.describe(category=ls("Name of commands category"), command=ls("Name of bot command"))
@app_commands.choices(category=[
    app_commands.Choice(name=ls("Information", key="categories.info.name"), value="info")
])
@app_commands.allowed_contexts(True, True, True)
async def help(
    ctx: BefriContext,
    command: str | None = None,
    *,
    category: app_commands.Choice[str] | None = None
) -> discord.Message | None:
    """[ `/help [command] [category]` ] Command reference"""
    if command is None and category is None:
        output = await build_help_home(ctx)
        return await output.send(ctx)
    
    if not (category is None or (extension := ctx.bot.loader.extensions.get(category.value)) is None):
        output = await build_help_category(ctx, extension)
        return await output.send(ctx)

async def get_command_list_for(extension: Extension, ctx: BefriContext) -> AsyncGenerator[commands.HybridCommand | app_commands.AppCommand, None]:
    """Generates a list of commands available in the current context"""
    for command_id in extension.commands.keys():
        bot_command = ctx.bot.get_command(command_id)
        if bot_command is None or not isinstance(bot_command, commands.HybridCommand):
            continue

        if not (await bot_command.can_run(ctx)):
            continue

        if len(ctx.bot.app_commands) == 0:
            yield bot_command

        app_command = ctx.bot.app_commands.get(command_id)
        if app_command is None:
            continue

        yield app_command

async def build_help_home(ctx: BefriContext) -> MessageBuilder:
    """[ `/home` ] Builds the help home page"""
    cont = container()
    cont.text(f"### {ctx.i('response_home.title')}\n{ctx.i('response_home.comment')}")
    
    for id, extension in ctx.bot.loader.extensions.items():
        icon = D.emoji(extension.get("icon") or "unknown")
        name = ctx.i18n.get_text(f"categories.{id}.name")

        command_list = list()
        async for command in get_command_list_for(extension, ctx):
            command_list.append(f"`{ctx.bot.prefix}{command.name}`" if isinstance(command, commands.HybridCommand) 
                                else f"</{command.name}:{command.id}>")

        cont.separator()
        cont.section(f"### {icon} {name}", " ".join(command_list), accessory=button(
            ctx.i("response_home.detail_button_name"), callback=send_help_wrap(ctx, build_help_category, extension)))

    cont.separator()
    cont.text(f"-# {ctx.i18n.get_text('common.footer')}")
    return message().container(cont.build())

async def build_help_category(ctx: BefriContext, extension: Extension) -> MessageBuilder:
    """[ `/home [category]` ] Builds the help for category"""
    name = ctx.i18n.get_text(f"categories.{extension.id}.name")
    description = ctx.i18n.get_text(f"categories.{extension.id}.description")

    cont = container()
    cont.section(f"### {ctx.i('response_category.title', name=name)}", f"{description}.", accessory=button(
        ctx.i("response_category.back_button_name"), callback=send_help_wrap(ctx, build_help_home)))

    cont.separator()

    i = 0
    async for command in get_command_list_for(extension, ctx):
        usage = ctx.i18n.get_text(f"commands.{command.name}.usage")
        description = ctx.i18n.get_text(f"commands.{command.name}.description")

        bc_line = f"`{ctx.bot.prefix}{command.name}{(' ' + usage) if len(usage) > 0 else ''}`"
        ac_line = f"</{command.name}:{command.id}>" if isinstance(command, app_commands.AppCommand) else None
        line_s = "\n" if i != 0 else ""

        cont.text(f"{line_s}{(ac_line + '  (') if ac_line else ''}{bc_line}{')' if ac_line else ''}\n> {description}")
        i += 1

    cont.separator()
    cont.text(f"-# {ctx.i('response_command.footer')}")
    return message().container(cont.build())

def send_help_wrap(
    ctx: BefriContext,
    builder: Callable[[BefriContext], CMB] | Callable[[BefriContext, Any], CMB],
    *args: Any
) -> Callable[[discord.Interaction], Coroutine[None, None, Any]]:
    """Yes, wrapper. Yes, to convey context and extra args. Any problems?"""
    async def send_help(interaction: discord.Interaction) -> Any:
        new_ctx = BefriContext.fake_from_interaction(interaction, message=ctx.message, command=ctx.command)
        help_page = (await builder(new_ctx, *args)).build_view()
        if interaction.user != ctx.author:
            return await interaction.response.send_message(view=help_page, ephemeral=True)

        await interaction.response.edit_message(view=help_page)

    return send_help
