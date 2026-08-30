import typing

import discord

from extensions.tags.modals import CreateTagModal
from resources.abc import GuildInteraction
from resources.customs import Bot


class EditTagModal(CreateTagModal):
    tag_name: discord.ui.TextInput = discord.ui.TextInput(
        label="Tag ID",
        placeholder="id of the tag listed when searching",
        max_length=256,
    )

    def __init__(
            self,
            tag_name: str,
            title: str,
            description: str,
            report_to_staff: bool,
            color: tuple[int, int, int],
    ) -> None:

        self.tag_name.default = tag_name
        self.embed_title.default = title
        self.description.default = description
        self.report_to_staff.default = str(report_to_staff)
        self.color.default = f"{color[0]},{color[1]},{color[2]}"

        super().__init__()
        self._children.append(self._children.pop(0))  # re-append embed title
        self._children.append(self._children.pop(0))  # re-append embed description
        self._children.append(self._children.pop(0))  # re-append report to staff
        self._children.append(self._children.pop(0))  # re-append embed color
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

        if itx.guild is None:
            raise ValueError("Expected the guild to have a value but it was None instead.")
        guild_itx = typing.cast(GuildInteraction[Bot], itx)
        self.return_interaction = guild_itx
