import pytest
import discord
from resources.customs.bot import Bot


def test_bot():
    # Arrange
    bot = Bot(api_tokens={}, version="1.0",
              rina_db=None, async_rina_db=None,
              intents=discord.Intents.default(),
              command_prefix=None,
              case_insensitive=True,
              activity=discord.Game(name="with slash (/) commands!"),
              allowed_mentions=discord.AllowedMentions(everyone=False))

    # Act

    # Assert
