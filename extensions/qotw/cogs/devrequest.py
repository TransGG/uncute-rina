import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from extensions.qotw.utils import create_thread, ping_open_threads
from extensions.settings.objects import AttributeKeys, ModuleKeys, ServerSettings, ServerAttributes
from resources.abc import GuildInteraction
from resources.checks import (
    is_staff_check,
    MissingAttributesCheckFailure,
    module_enabled_check,  # for dev request thread ping
)
from resources.customs import Bot

emoji_color_options = {
    "🔴": discord.Colour.from_rgb(r=255, g=100, b=100),
    "🟡": discord.Colour.from_rgb(r=255, g=255, b=172),
    "🟢": discord.Colour.from_rgb(r=100, g=255, b=100),
    "🔵": discord.Colour.from_rgb(r=172, g=172, b=255)
}


class DevRequest(commands.Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    @app_commands.command(
        name="developer_request",
        description="Suggest a bot idea to the TransPlace developers!"
    )
    @app_commands.describe(suggestion="What idea would you like to share?")
    @module_enabled_check(ModuleKeys.dev_requests)
    async def developer_request(
            self,
            itx: GuildInteraction[Bot],
            suggestion: app_commands.Range[str, 25, 1500],
    ) -> None:
        developer_request_channel = itx.client.get_guild_attributes(
                itx.guild).developer_request_channel
        if developer_request_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.dev_requests,
                [AttributeKeys.developer_request_channel],
            )

        if len(suggestion) > 4000:
            await itx.response.send_message(
                "Your suggestion won't fit! Please make your suggestion "
                "shorter. If you have a special request, you could make a "
                "ticket too (in #contact-staff)",
                ephemeral=True)
            return

        await itx.response.defer(ephemeral=True)

        title = "BotRQ-" + suggestion.replace("\\n", "\n")[:48]
        def reaction_role_lambda(attrs: ServerAttributes):
            return attrs.developer_request_reaction_role

        await create_thread(
            itx.client,
            (itx.user, developer_request_channel, suggestion),
            title,
            reaction_role_lambda,
            AttributeKeys.developer_request_reaction_role,
            emojis=[discord.PartialEmoji.from_str(emoji)
                    for emoji in ("⬆️", "⬇️")]
        )
        await itx.followup.send(
            "Successfully added your suggestion! The developers will review "
            "your idea, and perhaps inform you when it gets added :D",
            ephemeral=True
        )

    @app_commands.command(
        name="ping_open_dev_requests",
        description="Send a message in closed green dev request threads"
    )
    @is_staff_check
    @module_enabled_check(ModuleKeys.dev_requests)
    async def ping_open_developer_requests(
            self,
            itx: GuildInteraction[Bot]
    ) -> None:
        await itx.response.defer(ephemeral=True)
        watchlist_channel = itx.client.get_guild_attributes(
            itx.guild).developer_request_channel
        if watchlist_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.dev_requests,
                [AttributeKeys.developer_request_channel])

        def is_dev_thread_open(
                _: discord.Thread,
                msg: discord.Message
        ) -> bool:
            return msg.embeds[0].color in [
                emoji_color_options["🟡"],
                emoji_color_options["🔵"]
            ]

        cmd_ping = itx.client.get_command_mention(
            "ping_open_dev_requests")
        ping_msg = (
            itx.user.mention
            + f" poked this thread with {cmd_ping}.\n"
              f"This channel got a message because it was "
              f"archived and the request wasn't marked as "
              f"completed or rejected."
        )
        await ping_open_threads(
            itx,
            watchlist_channel,
            is_dev_thread_open,
            ping_msg,
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(
            self,
            payload: discord.RawReactionActionEvent
    ) -> None:
        if not self.client.is_module_enabled(
                payload.guild_id, ModuleKeys.dev_requests):
            return
        assert payload.guild_id is not None
        dev_request_channel: discord.TextChannel | None = \
            self.client.get_guild_attributes(
                payload.guild_id).developer_request_channel
        if dev_request_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.dev_requests,
                [AttributeKeys.developer_request_channel],
            )

        if (dev_request_channel.id != payload.channel_id
                or payload.member is None):
            return

        if getattr(payload.emoji, "name", None) not in emoji_color_options:
            return

        message = await dev_request_channel.fetch_message(payload.message_id)
        if not self.client.is_me(message.author):
            return
        if len(message.embeds) != 1:
            return
        embed = message.embeds[0]
        embed.colour = emoji_color_options[payload.emoji.name]
        await message.edit(embed=embed)
        await message.remove_reaction(payload.emoji.name, payload.member)
