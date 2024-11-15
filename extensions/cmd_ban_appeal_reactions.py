import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot


class BanAppealReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id in self.client.custom_ids["ban_appeal_webhook_ids"]:
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
                return # prevent crashing later in the program.
            
            await message.add_reaction("👍")
            await message.add_reaction("🤷")
            await message.add_reaction("👎")
            
            # get appeal person's username (expected username)
            platform_field_name = appeal_embed.fields[1].name.lower()
            if "reddit username" in platform_field_name:
                platform = "reddit"
            elif "minecraft username" in platform_field_name:
                platform = "minecraft"
            elif "revolt username" in platform_field_name:
                platform = "revolt"
            elif "discord username" in platform_field_name:
                platform = "discord"
            else:
                raise AssertionError(f"Embed field 2 name of ban appeal webhook should contain 'discord/reddit/revolt/minecraft username' but was '{appeal_embed.fields[1].name}' / '{appeal_embed.fields[1].value}' instead!")

            username: str = appeal_embed.fields[1].value
            try:
                await message.create_thread(name=f"App-{platform[0]}-{username}", auto_archive_duration=10080)
            except discord.errors.Forbidden:
                raise # no permission to send message (should be reported to staff server owner i suppose)
            except discord.errors.HTTPException:
                # I expect this HTTP exception to have code=400 "BAD REQUEST"
                await message.create_thread(name=f"Appeal-Malformed username", auto_archive_duration=10080)



async def setup(client):
    await client.add_cog(BanAppealReactionsAddon(client))
