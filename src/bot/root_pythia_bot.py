"""The bot module, which handles discord interface"""

from os import getenv
import sys
import logging

import discord
from discord.ext import commands

from api.rootme_api import RootMeAPIManager
from api.rate_limiter import RateLimiter
from bot.root_pythia_cogs import RootPythiaCommands
from bot.dummy_db_manager import DummyDBManager


CHANNEL_ID = getenv("CHANNEL_ID")


def craft_intents():
    # Intents int: 19456 means:
    # - Send messages
    # - Embed Links
    # - Read messages/View Channels
    # configured in the discord dev portal https://discord.com/developers/applications
    # Notice that the bot doesn't required the intent "Send messages in threads"
    intents = discord.Intents(value=19456)

    # Disable privilegied and enbale message_content privilegied intent to enable commands
    intents.message_content = True
    intents.messages = True
    intents.typing = False
    intents.guild_typing = False
    intents.presences = False

    return intents


########### Create bot object #################
_DESCRIPTION = (
    "RootPythia is a Discord bot fetching RootMe API to notify everyone"
    "when a user solves a new challenge!"
)
_PREFIX = "!"
_INTENTS = craft_intents()

BOT = commands.Bot(command_prefix=_PREFIX, description=_DESCRIPTION, intents=_INTENTS)

# Create Bot own logger, each Cog will also have its own
BOT.logger = logging.getLogger(__name__)


########### Setup bot events response ###############


@BOT.event
async def on_ready():
    # is this call secure??
    logging.debug("channel id: %s", CHANNEL_ID)

    # Create Rate Limiter, API Manager, and DB Manager objects
    rate_limiter = RateLimiter()
    api_manager = RootMeAPIManager(rate_limiter)
    db_manager = DummyDBManager(api_manager)

    # Fetch main channel and send initialization message
    BOT.channel = await BOT.fetch_channel(CHANNEL_ID)
    await BOT.channel.send("Channel initliazed")

    # Register cogs
    await BOT.add_cog(RootPythiaCommands(BOT, db_manager))


@BOT.event
async def on_error(event, *args, **kwargs):
    if event == "on_ready":
        BOT.logger.error(
            "Event '%s' failed (probably from invalid channel ID), close connection and exit...",
            event,
        )
        await BOT.close()
        sys.exit(1)
    else:
        # maybe this call is too intrusive/verbose...
        await BOT.channel.send(f"{event} event failed, please check logs for more details")

        BOT.logger.exception("Unhandled exception in '%s' event", event)
