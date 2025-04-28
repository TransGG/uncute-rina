from datetime import datetime, timedelta


recently_renamed_vcs: dict[int, list[datetime]] = {}  # make your own vcs!


def clear_vc_rename_log(channel_id: int) -> None:
    """
    Helper function to clear the cached timestamps of renames of a custom vc.

    :param channel_id: The channel to clear the rewrite timestamps for.
    """
    try:
        del recently_renamed_vcs[channel_id]
    except KeyError:
        # Voice channel probably hasn't been renamed yet
        pass


def try_store_vc_rename(channel_id: int, max_rename_limit: int = 2) -> None | int:
    """
    Store a new voice channel rename in the storage dictionary.

    :param channel_id: The voice channel that will be renamed.
    :param max_rename_limit: (optional) The amount of times to allow the channel to be renamed in 10 minutes.

    :return: ``None`` if the voice channel's rename timestamp was successfully stored; or the channel's first
     rename timestamp if it was edited more than *max_rename_limit* times in the past 10 minutes.
    """
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
