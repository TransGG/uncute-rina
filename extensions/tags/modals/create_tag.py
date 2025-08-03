import typing

import discord

from resources.customs import Bot, GuildInteraction


class CreateTagModal(discord.ui.Modal):
    embed_title = discord.ui.TextInput(
        label='Title',
        placeholder='Title of the tag embed...',
        max_length=256,
    )

    description = discord.ui.TextInput(
        label='Description',
        style=discord.TextStyle.long,
        placeholder='Description of the tag embed...\n'
                    'Use %%/command%% to reference a command!',
        max_length=4000,
        # technically max length would be 4096, but discord only accepts
        #  up to 4000 characters in modal text fields :I
    )

    report_to_staff = discord.ui.TextInput(
        label='Report anonymous usage to staff',
        placeholder='Boolean: True or False',
        min_length=4,
        max_length=5,
    )

    color = discord.ui.TextInput(
        label='Color (RGB)',
        placeholder='Embed color, E.g. "255,255,255"',
        required=False,
        min_length=5,  # enough for "0,0,0"
        max_length=13,  # enough for "123, 123, 123"
    )

    def __init__(self):
        super().__init__(title="Create a custom tag.")

        self.return_interaction: GuildInteraction[Bot] | None = None

    async def on_submit(self, itx: discord.Interaction[Bot]):  # pyright: ignore [reportIncompatibleMethodOverride] # noqa
        itx.response: discord.InteractionResponse  # type: ignore
        if itx.guild is None:
            await itx.response.send_message(
                "Discord did not provide any Guild information when you "
                "submitted this modal. Make sure you ran this in a server and "
                "weren't kicked out halfway through or something. If you "
                "think this is unintended, please report it to TransPlace"
                "staff/developers.",
                ephemeral=True,
            )
            return

        assert itx.guild is not None
        guild_itx = typing.cast(GuildInteraction[Bot], itx)
        self.return_interaction = guild_itx
