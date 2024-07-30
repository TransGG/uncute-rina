import discord
from typing import Callable

def createButton(
        label: str,
        style: discord.ButtonStyle,
        callback: Callable,
        label_is_emoji: bool = False
    ) -> discord.Button:
    """
    Create a button for a view with a label/emoji, style, and callback.
    
    Parameters
    -----------
    label: :class:`str` | :class:`discord.Emoji` | :class:`discord.PartialEmoji`
        The label (text) of the button.
    style: :class:`discord.ButtonStyle`
        The button color.
    callback: :class:`Callable`
        The function to call when the button is clicked.
    label_is_emoji: :class:`bool`, optional
        Whether the given label should be used as button icon instead. Default: False.
    
    Returns
    --------
    :class:`discord.Button`
        A button with the given properties.
    """
    if label_is_emoji:
        button = discord.ui.Button(emoji=label, style=style)
    else:
        button = discord.ui.Button(label=label, style=style)
    button.callback = callback
    return button


class GenericTwoButtonView(discord.ui.View):
    def __init__(
            self,
            button_true: tuple[str, discord.ButtonStyle] = ("Confirm", discord.ButtonStyle.green),
            button_false: tuple[str, discord.ButtonStyle] = ("Cancel", discord.ButtonStyle.red),
            timeout: float | None = None
    ):
        """
        Create a new view with two buttons. Clicking the first button will set self.value to True, and 
        the second button sets it to False. Timing out will leave it at None.
        
        Parameters
        -----------
        button_true: :class:`tuple[str, discord.ButtonStyle]`, optional
            The first button's label (text) and color. Default: ("Confirm", discord.ButtonStyle.green).
        button_false: :class:`tuple[str, discord.ButtonStyle]`, optional
            The second button's label (text) and color. Default: ("Cancel", discord.ButtonStyle.red).
        timeout: :class:`_type_`, optional
            How long the user has before the buttons disable and the view.wait() finishes. Default: None.
        """
        super().__init__()
        self.value: bool | None = None
        self.timeout: float | None = timeout

        self.add_item(button_true[0], button_true[1], self.on_button_true)
        self.add_item(button_false[0], button_false[1], self.on_button_false)

    async def on_button_true(self, _itx: discord.Interaction, _button: discord.ui.Button):
        self.value = True
        self.stop()

    async def on_button_false(self, _itx: discord.Interaction, _button: discord.ui.Button):
        self.value = False
        self.stop()
        