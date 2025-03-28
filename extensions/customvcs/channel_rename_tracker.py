from datetime import datetime, timedelta


recently_renamed_vcs: dict[int, list[datetime]] = {}  # make your own vcs!


def clear_vc_rename_log(channel_id: int) -> None:
    global recently_renamed_vcs
    try:
        del recently_renamed_vcs[channel_id]
    except KeyError:
        # Voice channel probably hasn't been renamed yet
        pass


def try_store_vc_rename(channel_id: int, max_rename_limit: int = 2) -> None | int:
    """
    Store a new voice channel rename in the storage dictionary.

    Parameters
    -----------
    channel_id: :class:`discord.VoiceChannel`
        The voice channel that will be renamed.
    max_rename_limit: :class:`int`
        (optional) The amount of times to allow the channel to be renamed in 10 minutes. Default: 2

    Returns
    --------
    :class:`None`
        unix epoch of the first rename time if the voice channel has been renamed max_rename_limit times
        in 10 minutes already.
    :class:`int`
        if the voice channel's rename timestamp was successfully stored.
    """
    global recently_renamed_vcs
    if channel_id in recently_renamed_vcs:
        # if there have been 2 or more renames for this channel
        if len(recently_renamed_vcs[channel_id]) >= max_rename_limit:
            # if those renames were made within the last 10 minutes
            if datetime.now().astimezone() - recently_renamed_vcs[channel_id][0] < timedelta(seconds=600):
                return int(recently_renamed_vcs[channel_id][0].timestamp())
            # clear rename queue log and continue command
            # (discord allows 2 renames in 10 minutes but can queue rename events, hence '[2:]')
            recently_renamed_vcs[channel_id] = recently_renamed_vcs[channel_id][2:]
    else:
        # create and continue command
        recently_renamed_vcs[channel_id] = []
    recently_renamed_vcs[channel_id].append(datetime.now().astimezone())
    return None
