import typing

import discord
import discord.ext.commands as commands

from extensions.qotw.utils import create_thread
from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.abc import GuildMessage
from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot


class BanAppealReactionsAddon(commands.Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.ban_appeal_reactions):
            return
        message = typing.cast(GuildMessage, message)
        ban_appeal_webhook_id = self.client.get_guild_attributes(
                message.guild).ban_appeal_webhook_id
        if ban_appeal_webhook_id is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.ban_appeal_reactions,
                [AttributeKeys.ban_appeal_webhook_id])

        if message.webhook_id != ban_appeal_webhook_id:
            return

        if len(message.embeds) == 0:
            return

        appeal_embed: discord.Embed = message.embeds[0]
        if len(appeal_embed.fields) < 3:
            # it should have 5 fields:
            #    "Which of the following are you appealing?" |  multiple choice
            #    "What is your Discord username?"            |  open question
            #    "Why were you banned?"                      |  open question
            #    "Why do you wish to be unbanned?"           |  open question
            #    "Do you have anything else to add?"         |  open question
            return  # prevent crashing later in the program.

        field_name = appeal_embed.fields[1].name
        field_value = appeal_embed.fields[1].value
        # get appeal person's username (expected username)
        assert field_name is not None, (
            f"Expected the webhook to send an embed with field names but the "
            f"field with value `{field_value}` had a name of `{field_name}`!"
        )
        platform_field_name = field_name.lower()
        if "reddit username" in platform_field_name:
            platform = "reddit"
        elif "minecraft username" in platform_field_name:
            platform = "minecraft"
        elif "revolt username" in platform_field_name:
            platform = "revolt"
        elif "discord username" in platform_field_name:
            platform = "discord"
        else:
            raise AssertionError(
                f"Embed field 2 name of ban appeal webhook should contain "
                f"'discord/reddit/revolt/minecraft username' but was "
                f"'{field_name}' / '{field_value}' "
                f"instead!"
            )

        username: str = field_value or "Empty username"
        def reaction_role_lambda(attrs: ServerAttributes):
            return attrs.ban_appeal_reaction_role

        await create_thread(
            self.client,
            message,
            f"App-{platform[0]}-{username[:80]}",
            reaction_role_lambda,
            AttributeKeys.ban_appeal_reaction_role,
            emojis=[discord.PartialEmoji.from_str(emoji)
                    for emoji in ("👍", "🤷", "👎")]
        )
