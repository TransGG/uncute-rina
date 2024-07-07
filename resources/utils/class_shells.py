import discord


class CustomInteraction:
    def __init__(self, member: discord.Member):
        self.user = member
        self.guild = member.guild
