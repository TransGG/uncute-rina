import asyncio
# for sleep(0.1) to prevent blocking: allow discord and other processes
#  to send a heartbeat and function.
from datetime import datetime, timezone
from typing import Literal

import matplotlib.pyplot as plt
import pandas as pd  # for graphing member joins/leaves/verifications
from motor.core import AgnosticDatabase
import typing

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.abc import GuildInteraction
from resources.checks import not_in_dms_check
from resources.customs import Bot


type MemberDataType = typing.Literal[
    "joined",
    "left",
    "left unverified",
    "left verified",
    "verified"
]

# key = user id, val = list of unix times
# The key is a string because json (MongoDB) can't have integer keys.

type MemberEventType = dict[str, list[float]]

# This TypedDict has to be a function because the keys have spaces.
# noinspection PyTypeChecker
# ^ what do you mean "got unexpected 'TypeAliasType'"?
MemberDataEntry = typing.TypedDict(
    "MemberDataEntry",
    {
        "guild_id": typing.Required[int],
        "joined": MemberEventType,
        "left": MemberEventType,
        "left verified": MemberEventType,
        "left unverified": MemberEventType,
        "verified": MemberEventType,
    },
    total=False
)


async def _add_to_data(
        member: discord.Member,
        event_type: MemberDataType,
        async_rina_db: AgnosticDatabase
) -> None:
    collection = async_rina_db["data"]
    query = {"guild_id": member.guild.id}
    # noinspection PyTypeChecker
    data: MemberDataEntry | None = await collection.find_one(query)
    if data is None:
        await collection.insert_one(query)
        data = MemberDataEntry(**query)  # type: ignore[typeddict-item]

    if str(member.id) not in data[event_type]:
        data[event_type] = {
            str(member.id): [datetime.now().timestamp()]
        }
    else:
        data[event_type][str(member.id)].append(datetime.now().timestamp())

    await collection.update_one(
        query,
        {"$set": {
            f"{event_type}.{member.id}": data[event_type][str(member.id)]
        }},
        upsert=True
    )


class MemberData(commands.Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await _add_to_data(member, "joined", self.client.async_rina_db)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        role = discord.utils.find(lambda r: r.name == 'Verified',
                                  member.guild.roles)
        if role in member.roles:
            await _add_to_data(
                member,
                "left verified",
                self.client.async_rina_db
            )
        else:
            await _add_to_data(
                member,
                "left unverified",
                self.client.async_rina_db
            )

    @commands.Cog.listener()
    async def on_member_update(
            self,
            before: discord.Member,
            after: discord.Member
    ) -> None:
        role = discord.utils.find(lambda r: r.name == 'Verified',
                                  before.guild.roles)
        if role not in before.roles and role in after.roles:
            await _add_to_data(
                after,
                "verified",
                self.client.async_rina_db
            )

    @app_commands.command(
        name="getmemberdata",
        description="See joined, left, and recently verified users in x days"
    )
    @app_commands.describe(
        lower_bound_str="Get data from [period] days ago",
        upper_bound_str="Get data up to [period] days ago",
        doubles="If someone joined twice, are they counted double? "
                "(y/n or 1/0)",
        public="Send the output to everyone in the channel"
    )
    @app_commands.rename(lower_bound_str='lower_bound',
                         upper_bound_str='upper_bound')
    @not_in_dms_check
    async def get_member_data(
            self,
            itx: GuildInteraction[Bot],
            lower_bound_str: str,
            upper_bound_str: str | None = None,
            doubles: bool = False,
            public: bool = False
    ) -> None:
        # validate bounds
        try:
            lower_bound = float(lower_bound_str)
            upper_bound = float(upper_bound_str or 0)  # 0 days from now
        except ValueError:
            await itx.response.send_message(
                "Your period has to be a number for the amount of days "
                "that have passed",
                ephemeral=True
            )
            return
        valid = await self._validate_time_bounds(itx, lower_bound, upper_bound)
        if not valid:
            return

        # divide graph into 36 sections : 86400/36=2400
        accuracy = (lower_bound - upper_bound) * 2400
        lower_bound *= 86400  # days to seconds
        upper_bound *= 86400
        current_time = datetime.now(timezone.utc).timestamp()
        min_time = int((current_time - lower_bound) / accuracy) * accuracy
        max_time = int((current_time - upper_bound) / accuracy) * accuracy

        # fetch member data from mongodb
        collection = itx.client.async_rina_db["data"]
        query = {"guild_id": itx.guild_id}
        data: MemberDataEntry | None = await collection.find_one(query)
        if data is None:
            await itx.response.send_message(
                "Not enough data is configured to do this action! Please "
                "hope someone joins sometime soon lol",
                ephemeral=True)
            return
        await itx.response.defer(ephemeral=not public)

        results, max_time, min_time, totals, warning = await self._format_member_data(
            data,
            accuracy,
            min_time,
            max_time,
            doubles,
        )

        # widen type to allow None values (they will look better on the graph)
        results_nullable: dict[MemberDataType, dict[float, int | None]] = \
            typing.cast(dict[MemberDataType, dict[float, int | None]], results)

        await self._remove_zero_line(
            results_nullable,
            min_time,
            max_time,
            accuracy,
        )

        # PyCharm doesn't seem to notice that `results_nullable.keys()` returns (practically) Literals.
        # noinspection PyTypeChecker
        results_nullable = {
            key: {
                timestamp: value[timestamp]
                for timestamp in sorted(value.keys())
            }
            for key, value in results_nullable.items()
        }

        # allow heartbeat or recognizing other commands
        await asyncio.sleep(0.1)

        try:
            await self._make_member_data_graph(results_nullable, lower_bound, upper_bound, doubles)
        except ValueError:
            await itx.followup.send(
                "You encountered a ValueError! Mia has been sent an error "
                "report to hopefully be able to fix it :)",
                ephemeral=True)
            raise

        output = await self._format_event_stats(totals)

        await itx.followup.send(
            f"From {lower_bound / 86400} to {upper_bound / 86400} days ago, "
            f"{output} (with{'out' * (1 - doubles)} doubles)"
            + warning,
            file=discord.File('outputs/userJoins.png')
        )

    @staticmethod
    async def _validate_time_bounds(
            itx: GuildInteraction[Bot],
            lower_bound: float,
            upper_bound: float,
    ) -> bool:
        valid = True
        if lower_bound <= 0:
            await itx.response.send_message(
                "Your period (data in the past [x] days) has to be "
                "above 0!",
                ephemeral=True)
            valid = False
        # if period < 0.035:
        #     await itx.response.send_message(
        #         "Idk why but it seems to break when period is "
        #         "smaller than 0.0035, so better not use it.",
        #         ephemeral=True
        #     )
        #     valid = False
        # todo: figure out why you can't fill in less than 0.0035:
        #  ValueError: All arrays must be of the same length
        if lower_bound > 10958:
            await itx.response.send_message(
                "... I doubt you'll be needing to look 30 years into "
                "the past..",
                ephemeral=True
            )
            valid = False
        if upper_bound > lower_bound:
            await itx.response.send_message(
                "Your upper bound can't be bigger (-> more days ago) "
                "than the lower bound!",
                ephemeral=True
            )
            valid = False
        return valid

    # region get_member_data helpers

    @staticmethod
    async def _format_member_data(
            data: MemberDataEntry,
            accuracy: float,
            min_time: float,
            max_time: float,
            doubles: bool,
    ) -> tuple[
        dict[
            Literal["joined", "left", "left unverified", "left verified", "verified"],
            dict[float, int],
        ],
        float,
        float,
        dict[
            Literal["joined", "left", "left unverified", "left verified", "verified"],
            int,
        ],
        str
    ]:
        warning = ""
        # Map (rounded) unix timestamp with how often that
        #  (rounded) timestamp occurs.
        results: dict[MemberDataType, dict[float, int]] = {}
        # Get a list of people (in this server) that joined at certain
        #  times. Maybe round these to a certain factor (don't
        #  overstress the x-axis). These certain times are in a period
        #  of "now" and "[period] seconds ago".
        totals: dict[MemberDataType, int] = {}

        # gather timestamps in timeframe,
        #  as well as the lowest and highest timestamps

        for event_label, event_timestamps in data.items():
            event_label = typing.cast(MemberDataType, event_label)
            # ^ mypy sucks: https://github.com/python/mypy/issues/7178

            if not isinstance(event_timestamps, dict) or event_label == "guild_id":
                # event_label == "guild_id" is redundant, because guild_id has type int,
                #  so it's not a `dict` anyway.
                continue

            column = await MemberData._get_event_timestamps(
                event_timestamps,
                min_time,
                max_time,
                doubles,
            )
            totals[event_label] = len(column)

            # allow heartbeat or recognizing other commands
            await asyncio.sleep(0.1)

            results[event_label] = await MemberData._group_event_timestamps_by_accuracy(column, accuracy)

            # allow heartbeat or recognizing other commands
            await asyncio.sleep(0.1)

            if len(column) == 0:
                warning = (f"\nThere were no '{event_label}' users found for this "
                           f"time period.")
                results[event_label] = {}
            else:
                time_list = sorted(column)
                if min_time > time_list[0]:
                    min_time = time_list[0]
                if max_time < time_list[-1]:
                    max_time = time_list[-1]
        return results, max_time, min_time, totals, warning

    @staticmethod
    async def _get_event_timestamps(
            events: dict[
                str,
                list[float]
            ],
            min_time: float,
            max_time: float,
            doubles: bool,
    ) -> list[float]:
        # Make a list of timestamps where event 'y' happened.
        # We don't need to know what user 'triggered' this event,
        #  unless 'doubles' is True.
        column: list[float] = []
        for member in events:
            for time in events[member]:
                # If a user's join time is within the
                #  requested lower/upper bounds (note: see 'accuracy' variable),
                #  then append it.
                if min_time < time < max_time:
                    column.append(time)
                    if not doubles:
                        break
        return column

    @staticmethod
    async def _group_event_timestamps_by_accuracy(
            column: list[float],
            accuracy: float,
    ) -> dict[float, int]:
        events: dict[float, int] = {}
        # group timestamps into 'accuracy'-sized buckets.
        for time in column:
            time = int(time / accuracy) * accuracy
            if time in events:
                events[time] += 1
            else:
                events[time] = 1
        return events

    @staticmethod
    async def _remove_zero_line(
            results_nullable: dict[
                MemberDataType,
                dict[float, int | None]
            ],
            min_time: float,
            max_time: float,
            accuracy: float,
    ) -> None:
        # if the lowest timestamps are lower than the lowest timestamp,
        # then set all missing data to 0 (up until the graph has data)
        min_time_db = min_time
        for event_label, event_timestamps in results_nullable.items():
            min_time = min_time_db
            while min_time <= max_time:
                if min_time not in event_timestamps:
                    # remove the '0' line from before tracking
                    #  verifiedness of people after leaving
                    if (
                            (min_time > 1700225500 and event_label == "left")
                            # ^ backwards compatability
                            or (min_time < 1700225000
                                and event_label == "left verified")
                            or (min_time < 1700225000
                                and event_label == "left unverified")
                    ):
                        # todo: consider just migrating all 'left' to
                        #  left-verified.
                        event_timestamps[min_time] = None
                    else:
                        event_timestamps[min_time] = 0
                min_time += accuracy

    @staticmethod
    async def _make_member_data_graph(
            results_nullable: dict[
                MemberDataType,
                dict[float, int | None]
            ],
            lower_bound: float,
            upper_bound: float,
            doubles: bool,
    ) -> None:
        # make graph
        d: dict[
            typing.Literal["time"] | MemberDataType,
            list[float | int | None]
        ] = {
            "time": list(results_nullable["joined"])
        }
        for y in results_nullable:
            y: MemberDataType
            d[y] = [results_nullable[y][i] for i in results_nullable[y]]

        df = pd.DataFrame(data=d)  # can raise ValueError

        fig, (ax1) = plt.subplots()
        fig.suptitle(f"Member data from {lower_bound / 86400} to "
                     f"{upper_bound / 86400} days ago")
        fig.tight_layout(pad=1.0)
        color = {
            "joined": "g",
            "left": "r",  # backwards compatability
            "left verified": "r",
            "left unverified": "m",
            "verified": "b"
        }
        for graph in df:
            if str(graph) == "time":
                continue
            ax1.plot(df['time'], df[graph], color[str(graph)], label=graph)
        ax1.legend()
        if doubles:
            re_text = "inc"
        else:
            re_text = "exc"
        ax1.set_ylabel(f"# of members ({re_text}. rejoins/-leaves/etc)")

        tick_loc = list(df['time'][::3])
        if (lower_bound - upper_bound) / 86400 <= 1:
            tick_disp = [datetime
                         .fromtimestamp(i, timezone.utc)
                         .strftime('%H:%M')
                         for i in tick_loc]
        else:
            tick_disp = [datetime
                         .fromtimestamp(i, timezone.utc)
                         .strftime('%Y-%m-%dT%H:%M')
                         for i in tick_loc]

        # plt.xticks(tick_loc, tick_disp, rotation='vertical')
        # plt.setp(tick_disp, rotation=45, horizontalalignment='right')
        ax1.set_xticks(
            tick_loc,
            labels=tick_disp,
            horizontalalignment='right',
            minor=False,
            rotation=30
        )
        ax1.grid(visible=True, which='major', axis='both')
        fig.subplots_adjust(bottom=0.180, top=0.90, left=0.1, hspace=0.1)
        plt.savefig('outputs/userJoins.png', dpi=300)

    @staticmethod
    async def _format_event_stats(
            totals: dict[
                Literal["joined", "left", "left unverified", "left verified", "verified"],
                int
            ],
    ) -> str:
        string_map = {
            "joined": "members joined",
            "left": "members left",
            "left verified": "members left after being verified",
            "left unverified": "members left while unverified",
            "verified": "members were verified",
        }
        output = ""
        for label, count in totals.items():
            # "`10` members left after being verified, "
            output += f"`{count}` {string_map[label]}, "
        return output

    # endregion get_member_data helpers
