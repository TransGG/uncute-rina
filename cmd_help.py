from import_modules import *

class OtherAddons(commands.Cog):
    async def print_help_text(self, itx):
        """
        A function to give the user Rina's list of public commands () (interaction response)

        ### Parameters
        --------------
        command_string:  :class:`str`
            Command you want to convert into a mention (without slash in front of it)
        ### Returns
        -----------
        command mention: :class:`str`
            The command mention, or input if not found
        """

        out = f"""\
Hi there! This bot has a whole bunch of commands. Let me introduce you to some:
{self.client.get_command_mention('add_poll_reactions')}: Add an up-/downvote emoji to a message (for voting)
{self.client.get_command_mention('commands')} or {self.client.get_command_mention('help')}: See this help page
{self.client.get_command_mention('compliment')}: Rina can compliment others (matching their pronoun role)
{self.client.get_command_mention('convert_unit')}: Convert a value from one to another! Distance, speed, currency, etc.
{self.client.get_command_mention('dictionary')}: Search for an lgbtq+-related or dictionary term!
{self.client.get_command_mention('equaldex')}: See LGBTQ safety and rights in a country (with API)
{self.client.get_command_mention('math')}: Ask Wolfram|Alpha for math or science help
{self.client.get_command_mention('nameusage gettop')}: See how many people are using the same name
{self.client.get_command_mention('pronouns')}: See someone's pronouns or edit your own
{self.client.get_command_mention('qotw')} and {self.client.get_command_mention('developer_request')}: Suggest a Question Of The Week or Bot Suggestion to staff
{self.client.get_command_mention('reminder reminders')}: Make or see your reminders
{self.client.get_command_mention('roll')}: Roll some dice with a random result
{self.client.get_command_mention('tag')}: Get information about some of the server's extra features
{self.client.get_command_mention('todo')}: Make, add, or remove items from your to-do list
{self.client.get_command_mention('toneindicator')}: Look up which tone tag/indicator matches your input (eg. /srs)

Make a custom voice channel by joining "Join to create VC" (use {self.client.get_command_mention('tag')} `tag:customvc` for more info)
{self.client.get_command_mention('editvc')}: edit the name or user limit of your custom voice channel
{self.client.get_command_mention('vctable about')}: Learn about making your voice chat more on-topic!
"""
# Check out the #join-a-table channel: In this channel, you can claim a channel for roleplaying or tabletop games for you and your group!
# The first person that joins/creates a table gets a Table Owner role, and can lock, unlock, or close their table.
# {self.client.get_command_mention('table lock')}, {self.client.get_command_mention('table unlock')}, {self.client.get_command_mention('table close')}
# You can also transfer your table ownership to another table member, after they joined your table: {self.client.get_command_mention('table newowner')}\
# """
        await itx.response.send_message(out, ephemeral=True)

    @app_commands.command(name="help", description="A help command to learn more about me!")
    async def help(self, itx: discord.Interaction):
        await self.print_help_text(itx)

    @app_commands.command(name="commands", description="A help command to learn more about me!")
    async def commands(self, itx: discord.Interaction):
        await self.print_help_text(itx)

async def setup(client):
    await client.add_cog(OtherAddons(client))