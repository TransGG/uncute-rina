import discord
import discord.ext.commands as commands

from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot


class BanAppealReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.ban_appeal_reactions):
            return
        ban_appeal_webhook: discord.User | None = self.client.get_guild_attribute(
            message.guild, AttributeKeys.ban_appeal_webhook)
        if ban_appeal_webhook is None:
            raise MissingAttributesCheckFailure(AttributeKeys.ban_appeal_webhook)

        if message.author.id != ban_appeal_webhook.id:
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

        await message.add_reaction("👍")
        await message.add_reaction("🤷")
        await message.add_reaction("👎")

        field_name = appeal_embed.fields[1].name
        field_value = appeal_embed.fields[1].value
        # get appeal person's username (expected username)
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

        username: str = field_value
        try:
            thread = await message.create_thread(name=f"App-{platform[0]}-{username[:80]}",
                                                 auto_archive_duration=10080)
        except discord.errors.Forbidden:
            raise  # no permission to send message (should be reported to staff server owner I suppose)
        except discord.errors.HTTPException:
            # I expect this HTTP exception to have code=400 "BAD REQUEST"
            thread = await message.create_thread(name=f"Appeal-{platform[0]}-Malformed username",
                                                 auto_archive_duration=10080)
        await thread.join()
        joiner_msg = await thread.send("user-mention placeholder")
        # surely pinging active staffs should only make those with the original channel perms be
        # able to see it, right...?
        await joiner_msg.edit(content=f"<@&{self.client.custom_ids['active_staff_role']}>")
        await joiner_msg.delete()
