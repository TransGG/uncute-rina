import discord


class CustomVoiceChannel:
    def __init__(self, id: int, name: str, members: list[discord.Member]):
        """
        Create a custom discord.VoiceChannel to reuse similar code.

        ### Parameters
        id: :class:`int`
            The id of the channel.
        name: :class:`str`
            The name of the channel.
        members: :class:`list[discord.Member]`
            A list of members currently connected to the voice channel.

        ### Attributes
        mention: :class:`str`
            A string representation of the channel as mention.
        """
        self.id = id
        self.name = name
        self.mention = "<#" + str(id) + ">"
        self.members = members
