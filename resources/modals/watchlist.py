from __future__ import annotations
import discord
import typing

if typing.TYPE_CHECKING:
    from extensions.cmd_watchlist import WatchList


class WatchlistReasonModal(discord.ui.Modal):
    """
    A modal allowing the user to add a user to the watchlist with a reason
    """

    def __init__(self, watchlist: WatchList, title: str, reported_user: discord.User, message: discord.Message = None, timeout=None):
        super().__init__(title=title, timeout=timeout)
        self.value = None
        # self.timeout = timeout
        # self.title = title
        self.user = reported_user
        self.message = message
        self.watchlist = watchlist

        self.reason_text = discord.ui.TextInput(label=f'Reason for reporting {reported_user}',
                                                placeholder=f"not required but recommended",
                                                style=discord.TextStyle.paragraph,
                                                required=False)
        self.add_item(self.reason_text)
    
    async def on_submit(self, itx: discord.Interaction):
        self.value = 1
        await self.watchlist.add_to_watchlist(itx, self.user, self.reason_text.value, str(getattr(self.message, "id", "")) or None)
        self.stop()
