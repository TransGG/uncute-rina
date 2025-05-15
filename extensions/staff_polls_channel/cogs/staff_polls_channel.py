import discord
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.checks import MissingAttributesCheckFailure
from resources.customs.bot import Bot


async def _handle_forward_poll_result(
        poll_result_message: discord.Message,
        poll_message: discord.Message
):
    """
    Handle forwarding poll results to the original thread.

    Sends and pins a formatted poll result message into the thread on
    the original poll. It then deletes the original result message.

    :param poll_result_message: A system message signifying the end
     of the original poll. It should have a reference to the original
     poll. It will be deleted after the poll message information
     has been forwarded.
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

    poll_result_embed: discord.Embed = poll_result_message.embeds[0]
    poll_data: dict[str, str | int | bool] = {
        field.name: field.value
        for field in poll_result_embed.fields
    }

    result_info_message = (
        f"**This poll closed with a total of "
        f"{poll_data.get('total_votes', 'NaN')} votes!**\n"
    )

    if poll_data.get("victor_answer_id") is None:
        result_info_message += (
            "There was no winner."
        )
    else:
        if poll_data.get("victor_answer_emoji_name") is None:
            victor_emoji_str = ""
        else:
            emoji_anim = poll_data.get("victor_answer_emoji_animated", False)
            if emoji_anim is not False:
                # todo: check if emoji_anim is `true` or `"True"` or something
                print(emoji_anim)
            emoji_name = poll_data.get("victor_answer_emoji_name")
            # ^ required for PartialEmoji
            emoji_id = poll_data.get("victor_answer_emoji_id")
            victor_emoji = discord.PartialEmoji(
                name=emoji_name, id=emoji_id, animated=emoji_anim
            )
            victor_emoji_str = f"{victor_emoji} "  # with space after it

        result_info_message += (
            f"Answer {poll_data.get('victor_answer_id')} won with "
            f"{poll_data.get('victor_answer_votes')} votes:\n"
            f"> {victor_emoji_str}{poll_data.get('victor_answer_text')}"
        )
    msg = await poll_message.thread.send(
        result_info_message,
        allowed_mentions=discord.AllowedMentions.none()
    )
    await msg.pin()
    await poll_result_message.delete()
    # ^ remove poll result message from poll-only channel.


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
    original_message = message.reference.resolved
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
        if None in (polls_channel, polls_channel_reaction_role):
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

                await _handle_forward_poll_result(message, original_message)
                return

            # Note: Poll questions can have a length of 300 characters,
            #  see [1], whereas thread names can only be up to 100
            #  characters, see [2] (inherited from channel names).
            # [1]: https://discord.com/developers/docs/resources/poll#poll-media-object-poll-media-object-structure # noqa
            # [2]: https://discord.com/developers/docs/topics/threads#thread-fields # noqa
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
