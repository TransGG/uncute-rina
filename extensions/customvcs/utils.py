import discord


def is_vc_custom(
        voice_channel: discord.VoiceChannel,
        customvc_category_id: int,
        customvc_hub_id: int,
        customvc_channel_blacklist: list[int]
) -> bool:
    """Check if a voice channel is custom-made by Rina through the customvc Hub.

    Parameters
    -----------
    voice_channel: :class:`discord.VoiceChannel`:
        The voice channel to test for customness.
    customvc_category_id: :class:`int`
        The category id where custom voice channels are allowed to be created.
    customvc_hub_id: :class:`int`
        The voice channel id of the channel members should join to create a custom voice channel.
    customvc_channel_blacklist: :class:`int`
        A list of voice channel ids that may definitely not be removed when the last person leaves.

    Returns
    --------
    :class:`bool`:
        Whether the channel is a custom voice channel or not.
    """
    return (
            voice_channel.category.id in [customvc_category_id] and
            voice_channel.id != customvc_hub_id and  # avoid deleting the hub channel
            voice_channel.id not in customvc_channel_blacklist and
            not voice_channel.name.startswith('〙')
    )  # new blacklisted channels: "#General" "#Quiet", "#Private" and "#Minecraft"
