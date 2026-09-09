import typing

import discord
from discord import Poll, PollAnswer, Thread
from discord.ext import commands

from extensions.settings.objects import (
    AttributeKeys,
    ModuleKeys,
)
from resources.checks import MissingAttributesCheckFailure
from resources.customs.bot import Bot


class PollResult(typing.TypedDict, total=False):
    poll_question_text: typing.Required[str]
    victor_answer_votes: typing.Required[str]
    total_votes: typing.Required[str]
    victor_answer_id: str
    victor_answer_text: str
    victor_answer_emoji_id: str
    victor_answer_emoji_name: str
    victor_answer_emoji_animated: str


async def _test_poll_finalized_state(
        poll: discord.Poll,
        poll_thread: discord.Thread,
        poll_result_message: discord.Message,
) -> None:
    """Send messages in the poll thread for unmet expectations. Like assertions."""
    if not poll.is_finalized():
        await poll_thread.send("Poll was not finalized, but expected discord to have finished that by now! "
                               "Tallied answers may not be entirely accurate.")
    if len(poll_result_message.embeds) == 0:
        await poll_thread.send("Poll result message had no embeds, "
                               "thus I could not verify the winner server-side.")


def _calculate_victors(
        poll: discord.Poll,
) -> tuple[int, set[discord.PollAnswer]]:
    """
    Iterate poll answers to list the top vote count and winning answers.
    :param poll: The poll to check answers for.
    :return: A tuple of the answers with the highest vote count,
     and the vote count that these answers achieved to make them win.
    """
    # manually calculate the list of responses
    highest_vote = -1
    best_answers: set[discord.PollAnswer] = set()
    for answer in poll.answers:
        if answer.vote_count > highest_vote:
            highest_vote = answer.vote_count
            best_answers.clear()
        if answer.vote_count == highest_vote:
            best_answers.add(answer)
    return highest_vote, best_answers


def _extract_poll_result_embed(
        poll_result_embed: discord.Embed,
) -> PollResult:
    """
    Parse a PollResult embed into a typed dictionary.

    :param poll_result_embed: The embed to parse
    :return A new typed dictionary PollResult with the required fields.
    :raise ValueError if the embed has empty field names (as it would give empty dictionary keys).
    """
    poll_results: PollResult = {}  # type: ignore[typeddict-item]
    for field in poll_result_embed.fields:
        if field.name is None:
            raise ValueError(
                "poll result embed field name was None",
                field,
                poll_result_embed.fields,
            )
        poll_results[field.name] = field.value  # type: ignore[literal-required]
    return poll_results


async def _handle_forward_poll_result(
        poll_thread: discord.Thread,
        poll: discord.Poll,
        poll_result_message: discord.Message,
) -> None:
    """
    Handle forwarding poll results to the original thread.

    Sends and pins a formatted poll result message into the thread on
    the original poll. It then deletes the original result message.

    :param poll_thread: The thread created under the poll
    :param poll: The user-created poll.
    :param poll_result_message: The system-generated PollResult whose data should be forwarded to the thread.
    :raise ValueError: if the PollResult didn't have 1 embed or if that embed has nil field names.
    """
    await _test_poll_finalized_state(poll, poll_thread, poll_result_message)

    # Discord polls don't seem to update the original message's
    #  poll state and answer when it finishes. So,
    #  manually extract the answer from the original poll,
    #  and manually extract the answer from the PollResult system message,
    #  and compare them.
    highest_vote, best_answers = _calculate_victors(poll)

    await _handle_compare_poll_and_poll_result(
        highest_vote,
        best_answers,
        poll_thread,
        poll,
        poll_result_message,
    )  # can raise value error

    result_info_message = (
        f"**This poll closed with a total of "
        f"{poll.total_votes} votes!**\n"
    )

    if highest_vote == 0:
        result_info_message += (
            "Nobody voted. There were no 'winners'."
        )
    elif len(best_answers) == 1:
        winning_answer = next(iter(best_answers))
        victor_emoji_str = (str(winning_answer.emoji) + " ") or ""
        result_info_message += (
            f"Answer {winning_answer.id} won with "
            f"{winning_answer.vote_count} vote{'s' if winning_answer.vote_count != 1 else ''}:\n"
            f"> {victor_emoji_str}{winning_answer.text}"
        )
    else:
        result_info_message += "Multiple answers won:\n"
        for answer in sorted(best_answers, key=lambda ans: ans.id):
            victor_emoji_str = (str(answer.emoji) + " ") or ""
            result_info_message += (
                f"- Answer {answer.id} with {answer.vote_count} vote{'s' if answer.vote_count != 1 else ''}:\n"
                f"  - {victor_emoji_str}{answer.text}\n"
            )

    msg = await poll_thread.send(
        result_info_message,
        allowed_mentions=discord.AllowedMentions.none()
    )
    try:
        await msg.pin()
    except discord.Forbidden:
        await msg.reply("Couldn't pin message: Missing permissions")


async def _handle_compare_1_winner(
        best_answers: set[PollAnswer],
        poll_thread: Thread,
        poll: Poll,
        poll_results: PollResult,
) -> None:
    """Compare expected winner and correct if it needed."""
    # there is only 1 winner, so the PollResult message should also note a winner.
    expected_answer = next(iter(best_answers))
    if "victor_answer_id" not in poll_results:
        await poll_thread.send(
            f"Calculated 1 winner "
            f"(answer {expected_answer.id}, {expected_answer.vote_count} votes), "
            f"but the PollResult says there was no winner "
            f"({poll_results['victor_answer_votes']} votes)."
        )
    if int(poll_results["victor_answer_id"]) != expected_answer.id:
        await poll_thread.send(
            f"Expected 1 winner extracted from the poll: "
            f"answer {expected_answer.id},\n"
            f"but discord's result seems to say this one won instead: "
            f"answer {poll_results['victor_answer_id']}."
            f"So I guess that one is right instead..."
        )
        # set winner to apparent winner
        best_answers.clear()
        best_answers.add(
            next(
                answer
                for answer in poll.answers
                if answer.id == poll_results["victor_answer_id"]
            )
        )


async def _handle_compare_poll_and_poll_result(
        highest_vote: int,
        best_answers: set[discord.PollAnswer],
        poll_thread: discord.Thread,
        poll: discord.Poll,
        poll_result_message: discord.Message
) -> None:
    """
    Compare a poll's answer votes and the PollResult's expected winner,
     correcting if necessary.

    :param highest_vote: The highest vote count any answer obtained.
    :param best_answers: Set of answers with the highest vote count.
    :param poll_thread: The thread created under the poll.
    :param poll: The user-created poll. The thing this is all about.
    :param poll_result_message: The system-created PollResult message when the poll is ended
     (through time/expiry or by the user manually).
    :raise ValueError: if the PollResult didn't have 1 embed or if that embed has nil field names.
    """
    # get system result message about poll responses.
    if (embed_count := len(poll_result_message.embeds)) != 1:
        raise ValueError(f"PollResult message had {embed_count} embeds! Expected only 1.")
    poll_result_embed = poll_result_message.embeds[0]
    # expected required embed fields:
    #  "poll_question_text", "victor_answer_votes", "total_votes"
    # optional embed fields:
    #  "victor_answer_id", "victor_answer_text",
    #  emoji stuff: "victor_answer_emoji_id", "victor_answer_emoji_name", "victor_answer_emoji_animated"
    try:
        poll_results = _extract_poll_result_embed(poll_result_embed)
    except ValueError as ex:
        raise ValueError(*ex.args, poll_result_message)

    # Compare the data from the original poll message's poll
    #  with the data in the PollResult message embed.
    # compare winning answer vote count
    if highest_vote != int(poll_results["victor_answer_votes"]):
        await poll_thread.send(
            f"Poll votes and result vote count mismatch: "
            f"highest vote from poll was tallied to be {highest_vote}, "
            f"but the extracted winner should have {poll_results['victor_answer_votes']} votes!"
        )
    # compare sum of all votes in the poll
    if poll.total_votes != int(poll_results["total_votes"]):
        poll_vote_sum = sum(answer.vote_count for answer in poll.answers)
        await poll_thread.send(
            f"Poll total votes and poll result total votes mismatch: "
            f"poll total vote count was {poll.total_votes}, "
            f"poll result total vote count was {poll_results['total_votes']}, "
            f"calculated poll total vote count was {poll_vote_sum}!"
        )
        # update poll internal sum Xd
        poll._total_votes = int(poll_results["total_votes"])  # ruff: ignore[private-member-access]

    if len(best_answers) == 1:
        await _handle_compare_1_winner(best_answers, poll_thread, poll, poll_results)
    elif "victor_answer_id" in poll_results:
        await poll_thread.send(
            f"Calculated {len(best_answers)} winners, but "
            f"discord says there is only 1 winner ({poll_results['victor_answer_id']})"
        )
        # reset winners and only fill this winning one
        best_answers.clear()
        best_answers.add(
            next(
                answer
                for answer in poll.answers
                if answer.id == poll_results["victor_answer_id"]
            )
        )


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


async def _handle_nonpoll_messages(
        message: discord.Message,
) -> None:
    """
    Handle messages without polls.

    Delete messages that aren't system-sent PollResult messages,
     and checking expected message states. Then forwarding the
     PollResult message to the original poll's thread.

    :param message: The message to handle.
    :raise ValueError: if the message is a PollResult with malformed embed
     or if the poll it links to has no thread.
    """
    # look only for poll_result messages
    if message.type != discord.MessageType.poll_result:
        await message.delete()
        return

    original_message = await _get_original_poll_message(message)
    if original_message is None:
        return

    if original_message.thread is None:
        raise ValueError(
            "Expected poll message to have a thread",
            original_message.jump_url,
            original_message,
        )
    if original_message.poll is None:
        raise ValueError(
            "Tried forwarding poll result but the original had no poll data."
        )

    await message.forward(original_message.thread)
    await _handle_forward_poll_result(  # can raise ValueError
        original_message.thread,
        original_message.poll,
        message,
    )
    await message.delete()
    # ^ remove poll result message from poll-only channel.
    return


class StaffPollsChannelAddon(commands.Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.polls_only_channel):
            return
        if message.guild is None:
            raise ValueError("Expected the guild to have a value but it was None instead.")

        # Can raise discord.Forbidden if:
        # - Missing `Manage Messages` to delete non-poll messages.
        # - Missing `Create threads` for poll messages.
        # - Missing `Send messages in thread` to join thread and add
        #   the reaction role.
        # - Missing

        guild_attributes = self.client.get_guild_attributes(message.guild)
        polls_channel = guild_attributes.polls_only_channel
        polls_channel_reaction_role = guild_attributes.polls_channel_reaction_role

        if (polls_channel is None
                or polls_channel_reaction_role is None):
            missing = [
                key for key, value in {
                    AttributeKeys.polls_only_channel: polls_channel,
                    AttributeKeys.polls_channel_reaction_role: polls_channel_reaction_role
                }.items()
                if value is None
            ]
            raise MissingAttributesCheckFailure(
                ModuleKeys.polls_only_channel,
                missing,
            )

        if message.channel == polls_channel:
            # non-poll: delete normal user messages that aren't poll results
            if message.poll is None:
                await _handle_nonpoll_messages(message)
                return

            # everything that actually contains poll (`message.poll`)

            # Note: Poll questions can have a length of 300 characters,
            #  see [1], whereas thread names can only be up to 100
            #  characters, see [2] (inherited from channel names).
            # [1]: https://discord.com/developers/docs/resources/poll#poll-media-object-poll-media-object-structure
            # [2]: https://discord.com/developers/docs/topics/threads#thread-fields
            thread = await message.create_thread(
                name=f"Poll-{message.poll.question}"[:50],
                auto_archive_duration=10080
            )
            await thread.join()

            top_msg = await thread.send("top of the channel")
            try:
                await top_msg.pin()
            except discord.Forbidden:
                await top_msg.reply("Couldn't pin message: Missing permissions")

            joiner_msg = await thread.send("user-mention placeholder")
            await joiner_msg.edit(
                content=f"<@&{polls_channel_reaction_role.id}>"
            )
            await joiner_msg.delete()
