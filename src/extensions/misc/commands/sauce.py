"""`/sauce` command.

[ `/sauce` ]
If called without arguments, it attempts to retrieve message attachments and
locate the sauce.

[ `/sauce [link to message | message id]` ]
Can be used with a reference to a message. It will then do the same thing as
without arguments, but will take the attachment from the specified message.

[ `/sauce [link to image]` ]
Or you can just put a link to the image.

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

from urllib.parse import ParseResult as URL, quote_plus, urlparse
from typing import Any, Final

import aiohttp
import simdjson
import discord
from discord import app_commands
from discord.app_commands import locale_str as ls
from discord.ext import commands

from core import BefriContext
from utils import container, message, gallery_item, button

__all__ = ("sauce",)

SEARCH_ENDPOINT: Final[str] = "https://api.trace.moe/search?cutBorders&anilistInfo&url={url}"


def parse_url(string: str | None) -> URL | None:
    """Parses the specified string as a URL. If it is not a URL, returns `None`"""
    if string is None:
        return None

    try:
        parsed = urlparse(string)
        if parsed.scheme not in ["http", "https"]:
            return

        return parsed if all([parsed.scheme, parsed.netloc]) else None

    except AttributeError:
        return None

def is_discord(url: URL) -> bool:
    return False if url.hostname is None else ".".join(url.hostname.split(".")[1:]) == "discord.com"

def get_genres(ctx: BefriContext, genres: list[str]) -> list[str]:
    return [ctx.i18n.get_text(f"genres.{x.lower()}", x) for x in genres]

def get_titles(result: dict[str, Any]) -> tuple[str, set[str]]:
    titles = result["anilist"]["title"]
    main_title = titles["romaji"] or titles["english"] or titles["native"]
    
    other_titles = [v for v in titles.values() if v is not None and v != main_title]
    other_titles.extend(result["anilist"]["synonyms"])
    return main_title, set(other_titles)

def format_time(time: float) -> str:
    hours = round(time // 3600)
    minutes = round((time - hours*3600) // 60)
    seconds = round(time - hours*3600 - minutes*60, 2)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

@commands.hybrid_command(name=ls("sauce"), description=ls("Finds anime based on the specified frame from it"))
@app_commands.rename(query=ls("query"))
@app_commands.describe(query=ls("Link to the message or its ID"))
@app_commands.allowed_contexts(True, True, True)
async def sauce(
    ctx: BefriContext,
    query: str | None = None,
) -> discord.Message | None:
    """[ `/sauce [message | image link]` ] Searching for the source of the specified image"""
    image_url = None
    parsed = parse_url(query)

    # link to image
    if parsed is not None:
        image_url = query

    # link to message or message id
    if (
        (parsed is not None and is_discord(parsed) and "/channels/" in parsed.path)
        or (query is not None and query.isdigit())
    ):
        message_ref = await commands.MessageConverter().convert(ctx, query)  # type: ignore
        if len(message_ref.attachments) == 0:
            return await ctx.send_error(text=ctx.i("errors.no_attachments_by_url"))

        image_url = message_ref.attachments[0].url

    # reply to message
    if image_url is None and ctx.message.reference is not None:
        channel = ctx.bot.get_channel(ctx.message.reference.channel_id)
        message_ref = await channel.fetch_message(ctx.message.reference.message_id)  # type: ignore
        if len(message_ref.attachments) == 0:
            return await ctx.send_error(text=ctx.i("errors.no_attachments_by_reference"))

        image_url = message_ref.attachments[0].url

    # attachments to the message that invoked the command
    if image_url is None and len(ctx.message.attachments) > 0:
        image_url = ctx.message.attachments[0].url
    
    # if there are no indications that the image is specified
    if image_url is None:
        return await ctx.send_error(text=ctx.i("error.no_image"))

    async with aiohttp.request("GET", SEARCH_ENDPOINT.format(url=quote_plus(image_url))) as response:
        raw = await response.read()

    data = simdjson.loads(raw)
    if data["error"] != "":
        return await ctx.send(f"```py\n{data['error']}\n```")
    
    result = data["result"][0]
    __import__("rich").print(result)

    if result["similarity"] < 0.25:
        return await ctx.send_error(text=ctx.i("error.not_similar_enough"))
    
    main_title, other_titles = get_titles(result)

    genres = ", ".join(f"`{x}`" for x in get_genres(ctx, result["anilist"]["genres"]))

    season = ctx.i(f"result.seasons.{result['anilist']['season'].lower()}")
    notes = [f"{season} {result['anilist']['startDate']['year']}"]
    if result["anilist"]["isAdult"]:
        notes.append(ctx.i("result.notes.adult"))

    cont = container()
    cont.text(f"### {ctx.i('result.title')}")
    cont.gallery(gallery_item(f"{result['video']}?size=l"))

    cont.text(ctx.i("result.fields.title", title=f"`{main_title}`")
              + f"\n{ctx.i('result.fields.genres', genres=genres)}"
              + f"\n{ctx.i('result.fields.notes', notes=', '.join('`' + x + '`' for x in notes))}")
    
    cont.action_row(button(
        label=ctx.i("result.buttons.myanimelist"),
        style=discord.ButtonStyle.link, 
        url=f"https://myanimelist.net/anime/{result['anilist']['idMal']}"
    ))

    other_titles_formated = "\n".join(f"- `{x}`" for x in other_titles)

    cont.separator()
    cont.text(f"{ctx.i('result.fields.other_titles')}\n{other_titles_formated}")

    similarity = f"`{round(result['similarity']*100, 1)}%`"
    episode = f"`{result['episode'] or ctx.i18n.get_text('none.var2')}`"
    frame = f"`{format_time(result['from'])}` — `{format_time(result['to'])}`"

    cont.separator()
    cont.text(f"### {ctx.i('result.metadata')}\n"
              + f"\n{ctx.i('result.fields.similarity', similarity=similarity)}"
              + f"\n{ctx.i('result.fields.episode', episode=episode)}"
              + f"\n{ctx.i('result.fields.frame', frame=frame)}")

    await (message().container(cont)).send(ctx)
