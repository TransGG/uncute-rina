import discord


BLACKLISTED_CHANNELS = [959626329689583616, 960984256425893958, 960984642717102122, 961794293704581130]


def is_vc_custom(
        voice_channel: discord.VoiceChannel,
        customvc_category_id: int,
        customvc_hub_id: int,
        customvc_channel_blacklist: list[int]
) -> bool:
    """Check if a voice channel is custom-made by Rina through the customvc Hub.

    :param voice_channel: The voice channel to test if it is a custom voice channel.
    :param customvc_category_id: The category id where custom voice channels are allowed to be created.
    :param customvc_hub_id: The voice channel id of the channel members should join to create a custom voice channel.
    :param customvc_channel_blacklist: A list of voice channel ids that may definitely not be removed when
     the last person leaves.

    :return: Whether the channel is a custom voice channel or not.
    """
    if voice_channel.category is None:
        return False
    return (
            voice_channel.category.id in [customvc_category_id] and
            voice_channel.id != customvc_hub_id and  # avoid deleting the hub channel
            voice_channel.id not in customvc_channel_blacklist and
            not voice_channel.name.startswith('〙')
    )  # new blacklisted channels: "#General" "#Quiet", "#Private" and "#Minecraft"


def edit_permissionoverwrite(
        perms: discord.PermissionOverwrite,
        overwrites: dict[str, bool]
) -> discord.PermissionOverwrite:
    perms_dict = dict(perms)
    perms_dict.update(overwrites)
    return discord.PermissionOverwrite(**perms_dict)
