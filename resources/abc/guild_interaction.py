import discord

from discord._types import ClientT


class GuildInteraction(discord.Interaction[ClientT]):
    guild: discord.Guild
    channel: (
        discord.abc.GuildChannel
        | discord.Thread
        | None
    )  # type: ignore[assignment]
