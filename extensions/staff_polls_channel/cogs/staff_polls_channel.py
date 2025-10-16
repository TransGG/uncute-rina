import discord
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.checks import MissingAttributesCheckFailure
from resources.customs.bot import Bot


async def _handle_forward_poll_result(
        poll_message: discord.Message
):
    """
    Handle forwarding poll results to the original thread.

    Sends and pins a formatted poll result message into the thread on
    the original poll. It then deletes the original result message.

    :param poll_message: A message containing the poll, and a thread
     created by Rina.

    :raise Exception: If the poll message has no thread.
    """
    if poll_message.thread is None:
        raise Exception(
            "Expected poll result to reference a poll with "
            "a thread, but it had none! (Poll message id:"
            + str(poll_message.id)
        )

    poll = poll_message.poll
    if poll is None:
        raise ValueError(
            "Tried forwarding poll result but the original had no poll data."
        )

    result_info_message = (
        f"**This poll closed with a total of "
        f"{poll.total_votes} votes!**\n"
    )

    if poll.victor_answer is None:
        result_info_message += (
            "There was no winner."
        )
    else:
        answer_emoji = poll.victor_answer.emoji
        if answer_emoji is None:
            victor_emoji_str = ""
        else:
            victor_emoji_str = str(answer_emoji)

        result_info_message += (
            f"Answer {poll.victor_answer.id} won with "
            f"{poll.victor_answer.vote_count} votes:\n"
            f"> {victor_emoji_str}{poll.victor_answer.text}"
        )

    msg = await poll_message.thread.send(
        result_info_message,
        allowed_mentions=discord.AllowedMentions.none()
    )
    await msg.pin()


async def _get_original_poll_message(
        message: discord.Message
) -> discord.Message | None:
    """
    Retrieve the original poll message from cache or fetch it.

    :param message: A 'poll result' system message with a reference
     to the original poll message.
    :return: The original message with a `poll` attribute, or None if
     fetching the original message resulted in a
     :py:class:~discord.NotFound error (likely because it was deleted).
    """
    # The message is a poll result.
    # Get the thread under the message reference. Note:
    #  thread IDs are the same as their parent message
    if (message.reference is None
            or message.reference.message_id is None):
        return None
    original_message = message.reference.resolved
    if isinstance(original_message, discord.DeletedReferencedMessage):
        return None

    if original_message is None:
        # message not in cache
        try:
            original_message = await message.channel.fetch_message(
                message.reference.message_id)
        except discord.NotFound:
            # original poll was deleted.
            return None

    return original_message


class StaffPollsChannelAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.polls_only_channel):
            return

        # Can raise discord.Forbidden if:
        # - Missing `Manage Messages` to delete non-poll messages.
        # - Missing `Create threads` for poll messages.
        # - Missing `Send messages in thread` to join thread and add
        #   the reaction role.
        # - Missing

        polls_channel: discord.TextChannel | None
        polls_channel_reaction_role: discord.Role | None
        polls_channel, polls_channel_reaction_role = \
            self.client.get_guild_attribute(
                message.guild,
                AttributeKeys.polls_only_channel,
                AttributeKeys.polls_channel_reaction_role,
            )
        if (polls_channel is None
                or polls_channel_reaction_role is None):
            missing = [key for key, value in {
                AttributeKeys.polls_only_channel: polls_channel,
                AttributeKeys.polls_channel_reaction_role:
                    polls_channel_reaction_role}.items()
                if value is None]
            raise MissingAttributesCheckFailure(
                ModuleKeys.polls_only_channel, missing)

        if message.channel == polls_channel:

            if message.poll is None:
                if message.type != discord.MessageType.poll_result:
                    await message.delete()
                    return

                original_message = await _get_original_poll_message(message)
                if original_message is None:
                    return

                await _handle_forward_poll_result(original_message)
                await message.delete()
                # ^ remove poll result message from poll-only channel.
                return

            # Note: Poll questions can have a length of 300 characters,
            #  see [1], whereas thread names can only be up to 100
            #  characters, see [2] (inherited from channel names).
            # [1]: https://discord.com/developers/docs/resources/poll#poll-media-object-poll-media-object-structure # noqa: E501
            # [2]: https://discord.com/developers/docs/topics/threads#thread-fields # noqa: E501
            thread = await message.create_thread(
                name=f"Poll-{message.poll.question}"[:50],
                auto_archive_duration=10080
            )
            await thread.join()

            top_msg = await thread.send("top of the channel")
            await top_msg.pin()

            joiner_msg = await thread.send("user-mention placeholder")
            await joiner_msg.edit(
                content=f"<@&{polls_channel_reaction_role.id}>"
            )
            await joiner_msg.delete()
