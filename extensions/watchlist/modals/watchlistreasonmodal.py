import discord
import typing

from resources.customs import Bot


class WatchlistReasonModal(discord.ui.Modal):
    """
    A modal allowing the user to add a user to the watchlist with
    a reason.

    :ivar add_to_watchlist_func: An async function from
     ``WatchList.add_to_watchlist(itx, user, reason, message_id,
     [warnings]) -> None`` to run with on_submit.
    :ivar message: The message that was reported / marked for
     the watchlist.
    :ivar reason_text: The reason provided by the staff member to add
     the user to the watchlist.
    :ivar timeout: The timeout before the modal closes itself.
    :ivar title: The title of the embed.
    :ivar user: The user that is being added to the watchlist.
    :ivar value: 1 if on_sumbit() was called, else None.
    """

    def __init__(
            self,
            add_to_watchlist_func: typing.Callable[
                [discord.Interaction[Bot], discord.User | discord.Member,
                 str, str | None, typing.Optional[str]],
                typing.Coroutine[typing.Any, typing.Any, None]],
            title: str,
            reported_user: discord.Member | discord.User,
            message: discord.Message | None = None,
            timeout=None
    ):
        super().__init__(title=title[:45], timeout=timeout)
        self.value = None
        # self.timeout = timeout
        # self.title = title
        self.user = reported_user
        self.message = message
        self.add_to_watchlist_func = add_to_watchlist_func

        self.reason_text = discord.ui.TextInput(
            label=f'Reason for reporting {reported_user}'[:45],
            placeholder="not required but recommended",
            style=discord.TextStyle.paragraph,
            required=False,
        )
        self.add_item(self.reason_text)

    async def on_submit(self, itx: discord.Interaction[Bot]):
        self.value = 1
        await self.add_to_watchlist_func(
            itx,
            self.user,
            self.reason_text.value,
            str(getattr(self.message, "id", "")) or None,
            ""
        )
        self.stop()
