"""The entrypoint of Befri

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import sys
import asyncio

from packaging.version import parse
from dotenv import load_dotenv

from core import Befri
from data import Configuration, Design
from utils import from_root

__all__ = ("main",)

load_dotenv(from_root(".env"))


async def main() -> None:
    """A entrypoint of Befri"""
    version = parse(Befri.__version__)
    channel = "canary" if version.is_prerelease else "stable"

    Design.set_data(Configuration.load(from_root("design.yml")))

    bot = Befri(Configuration.load(from_root("config.yml")))
    bot.logger.write_file_header()
    bot.logger.info(f"Starting Befri v{Befri.__version__} ({channel} channel)", component="launcher")

    try:
        await bot.start_bot()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await bot.close()
        bot.logger.info("The bot was stopped manually", component="launcher")
    except Exception as error:
        bot.logger.critical("An error occurred while the bot was running:", component="launcher")
        bot.logger.write_exception(error)
    finally:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
