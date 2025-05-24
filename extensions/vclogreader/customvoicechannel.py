import discord


class CustomVoiceChannel:
    def __init__(
            self,
            channel_id: int,
            name: str,
            members: list[discord.Member]
    ):
        """
        Create a custom :py:type:`~discord.VoiceChannel` to reuse
        similar code.

        :param channel_id: The id of the channel.
        :param name: The name of the channel.
        :param members: A list of members currently connected to
         the voice channel.

        :return: A string representation of the channel as mention.
        """
        self.id = channel_id
        self.name = name
        self.mention = "<#" + str(channel_id) + ">"
        self.members = members
