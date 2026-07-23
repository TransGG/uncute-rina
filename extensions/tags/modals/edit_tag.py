import typing

import discord

from extensions.tags.modals import CreateTagModal
from resources.abc import GuildInteraction
from resources.customs import Bot


class EditTagModal(CreateTagModal):
    def __init__(
            self,
            title: str,
            description: str,
            report_to_staff: bool,
            color: tuple[int, int, int],
    ) -> None:
        self.embed_title.default = title
        self.description.default = description
        self.report_to_staff.default = str(report_to_staff)
        self.color.default = f"{color[0]},{color[1]},{color[2]}"

        super().__init__()
        self.title = "Editing a custom tag..."

        self.return_interaction: GuildInteraction[Bot] | None = None

    async def on_submit(
            self,
            itx: discord.Interaction[Bot]  # type: ignore[override]
            # ^ (Interaction vs Interaction[Bot])
    ) -> None:
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
