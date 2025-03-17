import discord


class EqualDexAdditionalInfo(discord.ui.View):
    def __init__(self, url):
        super().__init__()
        link_button = discord.ui.Button(style=discord.ButtonStyle.gray,
                                        label="More info",
                                        url=url)
        self.add_item(link_button)
