from __future__ import annotations
import discord
import typing

if typing.TYPE_CHECKING:
    from extensions.cmd_watchlist import WatchList


class WatchlistReasonModal(discord.ui.Modal):
    """
    A modal allowing the user to add a user to the watchlist with a reason.

    Attributes
    -----------
    add_to_watchlist_func: :class:`typing.Callable[
            [discord.Interaction, discord.User, str, str | None],
            typing.Coroutine[Any, Any, None]]`
        An async function from WatchList.add_to_watchlist(itx, user, reason, message_id) -> None to run with on_submit.
    message: :class:`discord.Message` | :class:`None`
        The message that was reported / marked for the watchlist.
    reason_text: :class:`str`
        The reason provided by the staff member to add the user to the watchlist.
    timeout: :class:`int`
        The timeout before the modal closes itself.
    title: :class:`str`
        The title of the embed.
    user: :class:`discord.User`
        The user that is being added to the watchlist.
    value: :class:`int` | :class:`None`
        1 if on_sumbit() was called, else None.
    """

    def __init__(
            self,
            add_to_watchlist_func: typing.Callable[
                [discord.Interaction, discord.User | discord.Member, str, str | None, str],
                typing.Coroutine[typing.Any, typing.Any, None]],
            title: str,
            reported_user: discord.User,
            message: discord.Message = None,
            timeout=None
    ):
        super().__init__(title=title, timeout=timeout)
        self.value = None
        # self.timeout = timeout
        # self.title = title
        self.user = reported_user
        self.message = message
        self.add_to_watchlist_func = add_to_watchlist_func

        self.reason_text = discord.ui.TextInput(label=f'Reason for reporting {reported_user}',
                                                placeholder=f"not required but recommended",
                                                style=discord.TextStyle.paragraph,
                                                required=False)
        self.add_item(self.reason_text)

    async def on_submit(self, itx: discord.Interaction):
        self.value = 1
        await self.add_to_watchlist_func(itx, self.user, self.reason_text.value,
                                         str(getattr(self.message, "id", "")) or None, self.message.id)
        self.stop()
