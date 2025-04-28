import discord
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.checks import module_enabled_check, \
    MissingAttributesCheckFailure
from resources.customs.bot import Bot


class StaffPollsChannelAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    @module_enabled_check(ModuleKeys.polls_only_channel)
    async def on_message(self, message: discord.Message):
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
                ModuleKeys.polls_only_channel, *missing)

        if message.channel == polls_channel:
            if message.poll is None:
                if message.type != discord.MessageType.poll_result:
                    await message.delete()
                    return
                # The message is a poll result.
                # Get the thread under the message reference. Note:
                #  thread IDs are the same as their parent message
                original_message = message.reference.resolved
                if original_message is None:
                    # Don't delete the result message here, to allow
                    #  inspection as to why there was no original
                    #  message for the poll_result?
                    raise Exception(
                        "Poll result did not contain a reference to "
                        "the original poll message! (Poll result id:"
                        + str(original_message.id)
                    )
                if original_message.thread is None:
                    raise Exception(
                        "Expected poll result to reference a poll with "
                        "a thread, but it had none! (Poll message id:"
                        + str(original_message.id)
                    )

                poll = original_message.poll
                poll_result_message = (
                    f"**This poll closed with a total of "
                    f"{poll.total_votes} votes!**\n"
                    f"Answer {poll.victor_answer_id} won with "
                    f"{poll.victor_count} votes:\n"
                    f"> {poll.victor_answer.media.text}"
                )
                msg = await original_message.thread.send(
                    poll_result_message,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                await msg.pin()
                await original_message.delete()
                # ^ remove poll result message from poll-only channel.
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
            await joiner_msg.edit(content=polls_channel_reaction_role.mention,
                                  allowed_mentions=discord.AllowedMentions(
                                      roles=[polls_channel_reaction_role]))
            await joiner_msg.delete()
