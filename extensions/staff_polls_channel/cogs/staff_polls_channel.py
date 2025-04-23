import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot


class StaffPollsChannelAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == self.client.custom_ids["staff_polls_channel_id"]:
            if message.poll is None:
                await message.delete()
                return

            try:
                thread = await message.create_thread(name=f"Poll-{message.poll.question}", auto_archive_duration=10080)
                await thread.join()
                joiner_msg = await thread.send("user-mention placeholder")
                await joiner_msg.edit(content=f"<@&{self.client.custom_ids['active_staff_role']}>")
                await joiner_msg.delete()
                top_msg = await thread.send("top of the channel")
                await top_msg.pin()
            except:
                pass