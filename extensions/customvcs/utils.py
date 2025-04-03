import discord


BLACKLISTED_CHANNELS = [959626329689583616, 960984256425893958, 960984642717102122, 961794293704581130]
# todo attribute: this list shouldn't be hardcoded


def is_vc_custom(
        voice_channel: discord.VoiceChannel,
        customvc_category: discord.CategoryChannel,
        customvc_hub: discord.VoiceChannel,
        customvc_channel_blacklist: list[int]
) -> bool:
    """Check if a voice channel is custom-made by Rina through the customvc Hub.

    :param voice_channel: The voice channel to test if it is a custom voice channel.
    :param customvc_category: The category where custom voice channels are allowed to be created.
    :param customvc_hub: The voice channel that members should join to create a custom voice channel.
    :param customvc_channel_blacklist: A list of voice channel that may definitely not be removed when
     the last person leaves.

    :return: Whether the channel is a custom voice channel or not.
    """
    if voice_channel.category is None:
        return False
    return (
        voice_channel.category == customvc_category and
        voice_channel.id != customvc_hub.id and  # avoid deleting the hub channel
        voice_channel not in customvc_channel_blacklist and
        not voice_channel.name.startswith('〙')
    )  # new blacklisted channels: "#General" "#Quiet", "#Private" and "#Minecraft"


def edit_permissionoverwrite(
        perms: discord.PermissionOverwrite,
        overwrites: dict[str, bool]
) -> discord.PermissionOverwrite:
    perms_dict = dict(perms)
    perms_dict.update(overwrites)
    return discord.PermissionOverwrite(**perms_dict)
