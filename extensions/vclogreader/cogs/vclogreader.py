import traceback  # to pass traceback into error return message
from datetime import datetime, timezone  # to plot and sort voice chat logs

import matplotlib.pyplot as plt
import pandas as pd  # to plot voice channel timeline graph
import typing

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.checks import is_staff_check, MissingAttributesCheckFailure, \
    module_enabled_check  # cuz it's a staff command
from resources.customs import Bot

from extensions.vclogreader.vcloggraphdata import VcLogGraphData
from extensions.vclogreader.customvoicechannel import CustomVoiceChannel


channel_separator_table = str.maketrans({"<": "", "#": "", ">": ""})


def extract_id_and_name(embed: discord.Embed, field_number: int) -> tuple[str, str]:
    """
    A helper function to extract id and name from Logger Bot or Anna's
    voice channel logs.

    :param embed: The embed to extract from.
    :param field_number: The field number inside the id containing
     the channel information.
    :return: A tuple of the extracted id and name.
    """
    # split "<#234567> (Channel Name)" to "234567"
    channel_id = (
        embed.fields[field_number].value
        .split("#", 1)[1]
        .split(">", 1)[0]
    )
    # split "<#234567> (Channel Name)" to "Channel Name"
    channel_name = (
        embed.fields[field_number].value
        .split(">", 1)[1]
        .split("(", 1)[1][:-1]
    )
    return channel_id, channel_name


async def _get_vc_activity(
        voice_log_channel: discord.abc.Messageable,
        min_time: float,
        max_time: float,
        msg_limit: int
) -> list[tuple[float, tuple[int, str], tuple[int, str] | None, tuple[int, str] | None]]:
    """
    Retrieve the most recent voice channel activity from the logger channel and convert into neat string.

    :param voice_log_channel: Channel from which you want to get the voice channel logs / information.
    :param min_time: A unix epoch timestamp for the earliest logs to fetch (up to how long ago).
    :param max_time: A unix epoch timestamp for the latest logs to fetch (up to how recent).
    :param msg_limit: How many log messages to look through.

    :return: A list of (timestamp, user, previous_channel?, new_channel?). Typically, at least one of
     previous_channel or new_channel has a value.
    """
    # list of [(username, user_id), (joined_channel_id), (left_channel_id)]
    output: list[tuple[
        float,
        tuple[int, str],
        tuple[int, str] | None,
        tuple[int, str] | None]
    ] = []

    async for message in voice_log_channel.history(after=datetime.fromtimestamp(min_time, tz=timezone.utc),
                                                   before=datetime.fromtimestamp(max_time, tz=timezone.utc),
                                                   limit=msg_limit,
                                                   oldest_first=True):
        # oldest_first is by default true, since "after" != None, oldest_first will be true anyway.
        # Might as well make it definitive.

        # For context: the embed message sent by the Logger bot looks like this:
        #   author / image of user that sent message (author.name = username + descriminator
        #     (#0 in new discord update))
        #  case 1: the user joins/leaves a voice channel
        #   description: **username#0** joined/left voice channel vc_name
        #   fields[0].name: Channel
        #   fields[0].value: <#123456> (name)
        #   fields[1].name: ID
        #   fields[1].value: "```ini\nUser = 123456789\nChannel = 123456```"
        #  case 2: the user moves from one channel to another
        #   description: **username#0** moved from <#123456> (name1) to <#234567> (name2)
        #   fields[0].name: Current channel they are in    << New >>
        #   fields[0].value: <#234567> (name1)
        #   fields[0].name: Previously occupied channel    << Old >>
        #   fields[0].value: <#123456> (name2)
        #   fields[1].name: ID
        #   fields[1].value: "```ini\nUser = 123456789\nNew = 234567\nOld = 123456```"

        for embed in message.embeds:
            username = embed.description.split("**", 2)[1].split("#", 1)[0]
            # split **mysticmia#0** to mysticmia (taking discord usernames can't contain hashtags (cuz they can't))
            # print("Username = ", username)
            try:
                event_type = embed.description.split("**", 2)[2].split(" voice channel: ")[-2].split(") ")[-1].strip()
                # remove bold name and everything after the first word, to only select 'moved', 'joined', or 'left'.
                #  This transforms "**mysticmia#0** (Mia) joined voice channel: General.
                #             into " (Mia) joined voice channel: General."
                #             into " (Mia) joined"
                #             into "joined"
                # or, in the case there is no nickname/display name: " joined", which is why you have to strip it
                # too.
                # Note: this would break if a user has the nickname "a voice channel: b" since type would be "a"
            except IndexError:
                # this doesn't work if the user moved from one channel to another:
                #    "**mysticmia#0** (Mia) moved from ⁠〙 Quiet (〙 Quiet) to ⁠〙 General 2 (〙 General 2)."
                # ... Honestly, I think it's probably safe to assume the user "moved" in this case. There isn't any
                # fool-proof way to test otherwise.
                event_type = "moved"
                # Will get an assertion error if it's not, anyway, so I'll leave it as it is for now.

            # print("Type = ", type)
            # print("Embed field count = ", len(embed.fields))
            user_data = []
            previous_channel_data = []
            current_channel_data = []

            try:
                if embed.fields[0].name == "Action":
                    # actions like server deafening or muting someone also get logged, but are
                    # irrelevant for this diagram/command.
                    continue
                # Could be done more efficiently but oh well. Not like this is suitable for any
                # other bot either anyway. And I'm limited by discord API anyway.

                if len(embed.fields) == 3:  # user moved channels (3 fields: previous/current channel, and IDs)
                    if event_type != "moved":
                        raise AssertionError(f"type '{event_type}' is not a valid type (should be 'moved')")
                    current_id, current_name = extract_id_and_name(embed, 0)
                    current_channel_data.append(current_id)
                    current_channel_data.append(current_name)
                    previous_id, previous_name = extract_id_and_name(embed, 1)
                    previous_channel_data.append(previous_id)
                    previous_channel_data.append(previous_name)
                elif len(embed.fields) == 2:
                    if event_type == "joined":
                        current_id, current_name = extract_id_and_name(embed, 0)
                        current_channel_data.append(current_id)
                        current_channel_data.append(current_name)
                    elif event_type == "left":
                        previous_id, previous_name = extract_id_and_name(embed, 0)
                        previous_channel_data.append(previous_id)
                        previous_channel_data.append(previous_name)
                    else:
                        raise AssertionError(
                            f"type '{event_type}' is not a valid type (should be 'joined' or 'left')")
                else:
                    raise AssertionError(
                        f"Embed fields count was expected to be 3 or 2. Instead, it was '{len(embed.fields)}'")
            except IndexError:
                # TODO: try to figure out why it crashed that one time. Now with more details
                # edit: Some actions, such as server-deafening another user, give a different log message.
                if len(embed.fields) == 0:
                    raise Exception("Embed has no fields!")
                else:
                    if len(embed.fields[0].value.split("#", 1)) < 2:
                        raise Exception(
                            f"First embed field '{embed.fields[0].value}' does not have hashtags for its ID!")
                    raise Exception(f"Embed field '{embed.fields[0].value}' has some other error or something D:")

            # remove the ```ini\n  ...   ``` from the embed field
            id_data = (embed.fields[-1]
                       .value
                       .replace("```ini", "")[:-3]
                       .strip())

            for line in id_data.splitlines():
                key, value = line.split(" = ")
                if key == "User":
                    user_data.append(value)
                elif key == "New":
                    current_channel_data.append(value)
                elif key == "Old":
                    previous_channel_data.append(value)
                elif key == "Channel":
                    if event_type == "joined":
                        current_channel_data.append(value)
                    elif event_type == "left":
                        previous_channel_data.append(value)
                    else:
                        raise AssertionError(
                            f"type '{event_type}' is not a valid type "
                            f"(should be 'joined' or 'left')")
                else:
                    raise AssertionError(
                        f"key '{key}' is not a valid key (should be "
                        f"'User', 'Old', 'New', or 'Channel')")
            user_data.append(username)

            event_timestamp = embed.timestamp.timestamp()

            try:
                "A list of (timestamp, user, previous_channel?, new_channel?). Typically, at least one of"
                "previous_channel or new_channel has a value."
                event_user = (int(user_data[0]), user_data[1])

                if len(previous_channel_data) == 0:
                    previous_channel = None
                else:
                    previous_channel = (int(previous_channel_data[0]),
                                        previous_channel_data[1])

                if len(current_channel_data) == 0:
                    current_channel = None
                else:
                    current_channel = (int(current_channel_data[0]),
                                       current_channel_data[1])
            except ValueError:
                raise AssertionError(f"IDs were not numeric!\nFull error:\n{traceback.format_exc()}")

            data = (event_timestamp, event_user, previous_channel, current_channel)
            output.append(data)

    return output


async def _make_bar_graph(
        df, lower_bound, sorted_usernames, upper_bound, voice_channel
):
    df["Diff"] = df.Finish - df.Start
    color = "crimson"
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.suptitle(f"VC data in '{voice_channel.id}' from T-{lower_bound / 60} to T-{upper_bound / 60}")
    labels = []
    for i, task in enumerate(df.groupby("User")):
        labels.append(task[0])
        graph_data = task[1][["Start", "Diff"]]
        ax.broken_barh(graph_data.values, (i - 0.4, 0.8), color=color)
    ax.set_xticks(ax.get_xticks())
    # workaround to remove upcoming warning (warning about changing labels without preventing potential overlaps)
    tick_labels = [x.get_position()[0] for x in ax.xaxis.get_ticklabels()]
    label_time_text_format = "%H:%M"
    if tick_labels[-1] - tick_labels[0] < 5 * 60:
        label_time_text_format = "%H:%M:%S"
    elif tick_labels[-1] - tick_labels[0] > 86400:
        label_time_text_format = "%Y-%m-%dT%H:%M"
    ax.set_xticklabels(
        [datetime.fromtimestamp(x, tz=timezone.utc).strftime(label_time_text_format) for x in tick_labels],
        rotation=30)
    # Default y-tick labels have a font size of rcParams['axes.titlesize'], which corresponds to 'large'.
    #      https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_yticklabels.html
    #   'large' is relative to the default font size, which is rcParams['font.size'] (default 10.0)
    #      https://matplotlib.org/stable/api/font_manager_api.html#matplotlib.font_manager.FontProperties.set_size
    #    The text sizes are as follows: ['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large']
    #    Their values are as follows:   [   5.79,      6.94,     8.33,    10.0,     12.0,     14.4,      17.2]
    #      https://stackoverflow.com/questions/62288898/matplotlib-values-for-the-xx-small-x-small-small-medium-large-x-large-xx
    #    Each text size is 1.2x bigger than the previous, with `medium` by default 10.0
    # On the default scale (large), a graph can fit about 12 names. That would give 12*12=144 fontsize in a graph.
    # When more users are shown (eg. 30), that would bring the font size to 144 / 30 = 4.8,
    scaling_label_size = min(max(144 / max(len(sorted_usernames), 1), 4), 12)  # clamp to 4 <= size <= 12 (default)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, scaling_label_size)
    ax.set_xlabel("time (utc+0)")
    plt.tight_layout()
    plt.savefig('outputs/vcLogs.png', dpi=300)


async def _format_data_for_graph(
        events, max_time, min_time, select_user_ids, voice_channel
):
    intermediate_data: dict[int, dict[
        typing.Literal["name", "time_temp", "timestamps"],
        str | None | float | list[tuple[float, float]]
    ]] = {}
    for event in events:
        unix, user, from_channel, to_channel = event
        from_channel = from_channel[0] if from_channel else from_channel
        # set as its ID if not None (prevent TypeError: 'NoneType' object is not subscriptable)
        to_channel = to_channel[0] if to_channel else to_channel
        user_id = user[0]
        if len(select_user_ids) != 0 and user_id not in select_user_ids:
            continue
        if voice_channel.id not in [from_channel, to_channel]:
            continue
        if user[0] not in intermediate_data:
            intermediate_data[user_id] = {"name": user[1], "time_temp": None, "timestamps": []}

        if from_channel == voice_channel.id:
            if intermediate_data[user_id]["time_temp"] is None:
                intermediate_data[user_id]["timestamps"].append((min_time, unix))
            else:
                intermediate_data[user_id]["timestamps"].append((intermediate_data[user_id]["time_temp"], unix))
                intermediate_data[user_id]["time_temp"] = None
        elif to_channel == voice_channel.id:
            intermediate_data[user_id]["time_temp"] = unix
    for user_id in intermediate_data:
        if intermediate_data[user_id]["time_temp"]:
            intermediate_data[user_id]["timestamps"].append((intermediate_data[user_id]["time_temp"], max_time))
        del intermediate_data[user_id]["time_temp"]
    data: VcLogGraphData = {"User": [], "Start": [], "Finish": []}
    sorted_usernames = sorted(intermediate_data)  # sort alphabetically so graph always uses the same order
    for user in sorted_usernames:
        for time_tuple in intermediate_data[user]["timestamps"]:
            data["User"].append(intermediate_data[user]["name"])
            data["Start"].append(time_tuple[0])
            data["Finish"].append(time_tuple[1])
    return data, sorted_usernames


class VCLogReader(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="getvcdata",
                          description="Get recent voice channel usage data.")
    @app_commands.describe(lower_bound="Get data from [period] minutes ago",
                           upper_bound="Get data up to [period] minutes ago",
                           msg_log_limit="How many logs should I use to make the graph (default: 5000)",
                           user_ids="Specific user ids to filter the graph for (separate with comma)")
    @app_commands.check(is_staff_check)
    @module_enabled_check(ModuleKeys.vc_log_reader)
    async def get_voice_channel_data(
            self, itx: discord.Interaction[Bot], requested_channel: str, lower_bound: str, upper_bound: str = None,
            msg_log_limit: int = 5000, user_ids: str | None = None
    ):
        if user_ids is None:
            user_ids = ""
        select_user_ids: list[str] = user_ids.replace(" ", "").split(",")
        # update typing (if channel mention)
        requested_channel: discord.app_commands.AppCommandChannel | str = requested_channel
        warning = ""
        if type(requested_channel) is discord.app_commands.AppCommandChannel:
            voice_channel = itx.client.get_channel(requested_channel.id)
        else:
            if not requested_channel.isdecimal():
                await itx.response.send_message("You need to give a numerical ID!", ephemeral=True)
                return
            voice_channel = itx.client.get_channel(int(requested_channel))

        if type(voice_channel) is not discord.VoiceChannel:
            # make custom vc if the voice channel we're trying to get logs does not exist anymore.
            voice_channel = CustomVoiceChannel(channel_id=int(requested_channel),
                                               name="Unknown Channel",
                                               members=[])
            warning = "Warning: This channel is not a voice channel, or has been deleted!\n\n"

        vc_activity_logs_channel = itx.client.get_guild_attribute(
            itx.guild_id, AttributeKeys.voice_channel_activity_logs_channel)

        if vc_activity_logs_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.vc_log_reader,
                AttributeKeys.voice_channel_activity_logs_channel)

        if upper_bound is None:
            upper_bound = 0  # 0 minutes from now
        try:
            lower_bound = float(lower_bound)
            upper_bound = float(upper_bound)
            if lower_bound <= 0:
                await itx.response.send_message("Your period (data in the past [x] minutes) has to be above 0!",
                                                ephemeral=True)
                return
            if upper_bound > lower_bound:
                await itx.response.send_message(
                    "Your upper bound can't be bigger (-> longer ago) than the lower bound!", ephemeral=True)
                return
        except ValueError:
            await itx.response.send_message(
                "Your bounding period has to be a number for the amount of minutes that have passed", ephemeral=True)
            return

        await itx.response.defer(ephemeral=True)

        lower_bound *= 60  # minutes to seconds
        upper_bound *= 60
        current_time: float = int(datetime.now().timestamp())
        # min_time = int((current_time-lower_bound)/accuracy)*accuracy
        # max_time = int((current_time-upper_bound)/accuracy)*accuracy
        min_time: float = current_time - lower_bound
        max_time: float = current_time - upper_bound

        events = await _get_vc_activity(vc_activity_logs_channel, min_time, max_time, msg_log_limit)

        if max_time == current_time:  # current_time - 0 == current_time
            # If looking until the current time/date, add fake "leave" event for every person that is currently
            #  still in the voice channel. This ensures that even [those that haven't joined or left during the
            #  given time frame] will still be plotted on the graph.
            for member in voice_channel.members:
                events.append((current_time, (member.id, member.name), (voice_channel.id, voice_channel.name), None))

        data, sorted_usernames = await _format_data_for_graph(
            events, max_time, min_time, select_user_ids, voice_channel)

        df = pd.DataFrame(data=data)
        await _make_bar_graph(df, lower_bound, sorted_usernames, upper_bound, voice_channel)
        await itx.followup.send(
            warning +
            f"VC activity from {voice_channel.mention} (`{voice_channel.id}`) from {lower_bound / 60} to "
            f"{upper_bound / 60} minutes ago ({(lower_bound - upper_bound) / 60} minutes)" +
            (
                "\nNote: If you're looking in the past, people that joined before and left after the "
                "given timeframes may not show up on the graph. To ensure you get a good representation, "
                "be sure to add a bit of margin around the edges!" if max_time != current_time else ""
            ) + (
                f"\nBasing data off of {len(events)} data points. (current limit: {msg_log_limit})"
                if len(events) * 2 >= msg_log_limit else ""
            ),
            file=discord.File('outputs/vcLogs.png'))
