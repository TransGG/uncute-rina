from datetime import UTC, datetime, timedelta

import discord

from resources.abc import MessageableGuildChannel
from resources.checks import is_staff
from resources.customs.bot import Bot
from resources.utils import log_to_guild


class WrongChannelError(Exception):
    pass


class NoPermissionError(Exception):
    pass


def get_selfies_channels(client: Bot) -> set[MessageableGuildChannel]:
    """
    Helper to get a set of selfie channels.
    :param client: The client with which to get server settings
    :return: A set of selfie channels.
    :raises: ValueError: If the client provided has not initialized its server settings.
    """
    if client.server_settings is None:
        raise ValueError("Can't get selfies: server settings is None")
    return {
        settings.attributes.selfies_channel
        for settings in client.server_settings.values()
        if (settings.attributes.selfies_channel is not None
            and settings.enabled_modules.selfies_channel_deletion)
    }


def check_permissions(channel: MessageableGuildChannel) -> None:
    """
    Check the permissions for sending to this selfies channel.

    :param channel: The selfies channel to test permissions for.
    :raises WrongChannelError: If the channel is not the right type for a selfies channel.
    """
    if not isinstance(channel, discord.abc.Messageable):
        raise WrongChannelError(f"Channel {channel.id} ({channel.name}) is not messageable!")
    if not isinstance(channel, discord.abc.GuildChannel):
        raise WrongChannelError(f"Channel {channel.id} ({channel.name}) is not in a guild!")

    permissions = channel.permissions_for(channel.guild.me)
    if not permissions.read_messages:
        raise NoPermissionError(f"No permissions to read messages in {channel.id} ({channel.name})")
    if not permissions.read_message_history:
        raise NoPermissionError(f"No permissions to read message history in {channel.id} ({channel.name})")
    if not permissions.send_messages:
        raise NoPermissionError(f"No permissions to send messages in {channel.id} ({channel.name})")
    if not permissions.manage_messages:
        raise NoPermissionError(f"No permissions to manage (delete) messages in {channel.id} ({channel.name})")


async def delete_selfies(
        client: Bot,
        selfies_channel: MessageableGuildChannel,
) -> None:
    time_now = datetime.now(UTC)

    message_delete_count: int = 0
    queued_message_deletions: list[discord.Message] = []
    async for message in selfies_channel.history(
        limit=None,
        before=(datetime.now().astimezone() - timedelta(days=6, hours=23, minutes=30)),
        oldest_first=True,
    ):
        if (
                "[info]" in message.content.lower()
                and is_staff((client, selfies_channel.guild), message.author)
        ):
            continue
        message_date = message.created_at
        if time_now - message_date > timedelta(days=13, hours=23, minutes=30):
            # 14 days, too old to remove by bulk
            message_delete_count += 1
            await message.delete()
        elif time_now - message_date > timedelta(days=7):
            # technically redundant due to loop's "before" kwarg,
            #  but better safe than sorry
            queued_message_deletions.append(message)

        if len(queued_message_deletions) >= 100:
            # can only bulk delete up to 100 msgs
            message_delete_count += len(queued_message_deletions[:100])
            await selfies_channel.delete_messages(
                queued_message_deletions[:100],
                reason="Delete selfies older than 7 days",
            )
            queued_message_deletions = queued_message_deletions[100:]

    if queued_message_deletions:
        # count remaining messages
        message_delete_count += len(queued_message_deletions)
        # delete last few messages
        await selfies_channel.delete_messages(
            queued_message_deletions,
            reason="Delete selfies older than 7 days"
        )

    await selfies_channel.send(
        f":clock12: Selfies: Removed {message_delete_count} messages older than 7 days!",
    )


async def delete_all_selfies(client: Bot) -> None:
    selfies_channels = get_selfies_channels(client)
    for channel in selfies_channels:
        try:
            check_permissions(channel)
        except (WrongChannelError, NoPermissionError) as ex:
            await log_to_guild(
                client,
                channel.guild,
                f":warning: :clock12: Error deleting selfies in "
                f"guild {channel.guild.id} ({channel.guild.name}): "
                f"{ex}"
            )
            continue
        await log_to_guild(
            client,
            channel.guild,
            f":clock12: Automatic scheduler deleted selfies older than 7 days, "
            f"in {channel.mention} ({channel.id}).",
        )

        await delete_selfies(client, channel)


def start_selfies_delete_scheduler(client: Bot) -> None:
    next_run_time = datetime.now(tz=UTC).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(days=1)

    client.sched.add_job(
        delete_all_selfies,
        args=(client,),
        misfire_grace_time=60 * 60 * 3,
        id="selfie_deletion_job",
        trigger="interval",
        next_run_time=next_run_time,
        hours=24,  # "interval" trigger argument
    )
