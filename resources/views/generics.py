from __future__ import annotations

from abc import abstractmethod

import discord
import typing
import types

from resources.customs import Bot


def create_simple_button(
        label: str,
        style: discord.ButtonStyle,
        callback: typing.Callable[
            [discord.Interaction[Bot]],
            typing.Coroutine[typing.Any, typing.Any, typing.Any]],
        disabled: bool = False,
        label_is_emoji: bool = False,
) -> discord.ui.Button:
    """
    Create a button for a view with a label/emoji, style, and callback.

    :param label: The label (text) of the button.
    :param style: The button color.
    :param callback: The function to call when the button is clicked.
    :param disabled: Whether the button is clickable by the user.
    :param label_is_emoji: Whether the given label should be used as
     button icon instead. Default: False.

    :return: A button with the given properties.
    """
    if label_is_emoji:
        button = discord.ui.Button(emoji=label, style=style, disabled=disabled)
    else:
        button = discord.ui.Button(label=label, style=style, disabled=disabled)
    button.callback = callback
    return button


class GenericTwoButtonView(discord.ui.View):
    def __init__(
            self,
            button_true: tuple[str, discord.ButtonStyle] = (
                "Confirm", discord.ButtonStyle.green),
            button_false: tuple[str, discord.ButtonStyle] = (
                "Cancel", discord.ButtonStyle.red),
            timeout: float | None = None
    ):
        """
        Create a new view with two buttons. Clicking the first button
        will set :py:attr:`value` to True, and the second button sets it
        to False. Timing out will leave it at None.

        :param button_true: The first button's label (text) and color.
        :param button_false: The second button's label (text) and color.
        :param timeout: How long the user has before the buttons disable
         and the view.wait() finishes.
        """
        super().__init__()
        self.value: bool | None = None
        self.timeout: float | None = timeout

        self.add_item(create_simple_button(
            button_true[0], button_true[1], self.on_button_true
        ))
        self.add_item(create_simple_button(
            button_false[0], button_false[1], self.on_button_false
        ))

    async def on_button_true(self, _: discord.Interaction[Bot]):
        self.value = True
        self.stop()

    async def on_button_false(self, _: discord.Interaction[Bot]):
        self.value = False
        self.stop()


class PageView(discord.ui.View):
    @property
    def page_down_style(self) -> tuple[discord.ButtonStyle, bool]:
        """
        Gives the button style depending on the current page: If
        decrementing the page index would make it out of bounds, make
        it gray; else blurple. If loop_around_pages is disabled, the
        gray buttons will be disabled too.

        :return: A tuple of the button color and whether the button
         should be disabled.
        """
        disabled = (self.page == 0
                    and not self.loop_around_pages)
        # set color to gray if clicking the button would make the page
        #  out of bounds and thus loop around.
        if self.page == 0:
            button_style = discord.ButtonStyle.gray
        else:
            button_style = discord.ButtonStyle.blurple
        
        return button_style, disabled

    @property
    def page_up_style(self) -> tuple[discord.ButtonStyle, bool]:
        """
        Gives the button style depending on the current page: If
        incrementing the page index would make it out of bounds, make
        it gray; else blurple. If loop_around_pages is disabled, gray
        buttons will be disabled too.

        :return: A tuple of the button color and whether the button
         should be disabled.
        """
        disabled = (self.page == self.max_page_index
                    and not self.loop_around_pages)
        # set color to gray if clicking the button would make the page
        #  out of bounds and thus loop around.
        if self.page == self.max_page_index:
            button_style = discord.ButtonStyle.gray
        else:
            button_style = discord.ButtonStyle.blurple

        return button_style, disabled

    @abstractmethod
    async def update_page(self, itx: discord.Interaction[Bot], view: PageView):
        """
        Update the page message. This typically involves calculating the
        message content for the message and updating the original message.

        :param itx: The interaction gained from the button or modal
         interaction by the user.
        :param view: The view class instance.
        """
        pass

    def __init__(
            self,
            starting_page: int,
            max_page_index: int,
            page_update_function: typing.Callable[
                                      [discord.Interaction[Bot], PageView],
                                      types.CoroutineType[
                                          typing.Any, typing.Any, None]
                                  ] | None = None,
            prepended_buttons: list[discord.ui.Button] | None = None,
            appended_buttons: list[discord.ui.Button] | None = None,
            loop_around_pages: bool = True,
            timeout=None
    ):
        super().__init__(timeout=timeout)
        if prepended_buttons is None:
            # putting [] as default param makes it mutable,
            #  shared across instances -_-
            prepended_buttons = []
        if appended_buttons is None:
            appended_buttons = []
        self.page: int = starting_page
        if page_update_function is not None:
            self.update_page = page_update_function
        self.loop_around_pages = loop_around_pages

        self.max_page_index: int = max_page_index

        for pre_button in prepended_buttons:
            self.add_item(pre_button)

        page_up_style: tuple[discord.ButtonStyle, bool] \
            = self.page_up_style
        page_down_style: tuple[discord.ButtonStyle, bool] \
            = self.page_down_style
        
        self.page_down_button = create_simple_button(
            "◀️",
            page_down_style[0],
            self.on_page_down,
            disabled=page_down_style[1]
        )
        self.page_up_button = create_simple_button(
            "▶️",
            page_up_style[0],
            self.on_page_up,
            disabled=page_up_style[1]
        )
        self.add_item(self.page_down_button)
        self.add_item(self.page_up_button)

        for post_button in appended_buttons:
            self.add_item(post_button)

    async def on_page_down(self, itx: discord.Interaction[Bot]):
        if self.page - 1 < 0:  # below lowest index
            self.page = self.max_page_index  # set to the highest index
        else:
            self.page -= 1

        self.update_button_colors()
        await self.update_page(itx, self)

    async def on_page_up(self, itx: discord.Interaction[Bot]):
        if self.page + 1 > self.max_page_index:  # above highest index
            self.page = 0  # set to the lowest index
        else:
            self.page += 1

        self.update_button_colors()
        await self.update_page(itx, self)

    def update_button_colors(self) -> None:
        """
        Updates the buttons of the view to match the new page number:
        gray if it's the first/last page, else blurple. Gray buttons
        will also be disabled if loop_around_pages is False.

        To change the buttons in the discord message, run `update_page`.
        """
        self.page_down_button.style, self.page_down_button.disabled \
            = self.page_down_style
        self.page_up_button.style, self.page_up_button.disabled \
            = self.page_up_style
