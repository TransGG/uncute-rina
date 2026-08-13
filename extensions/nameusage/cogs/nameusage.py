import re  # to remove pronouns from user-/nicknames and split names at capital letters.
import typing
from enum import Enum

import discord
from discord import app_commands
from discord.ext import commands

from extensions.nameusage.views.pageview import GetTopPageView
from resources.abc import GuildInteraction
from resources.checks import not_in_dms_check
from resources.customs import Bot

name_blacklist = {
    "she", "he", "they", "it",
    "her", "him", "them", "its",
}


class NameUsageSearchMode(Enum):
    usernames = 1
    nicknames = 2
    nicknames_and_usernames = 3


def _get_member_name(member: discord.Member, mode: NameUsageSearchMode) -> set[str] | None:
    # get list of names
    match mode:
        case NameUsageSearchMode.usernames:
            name_sections = _split_name(member.name)
        case NameUsageSearchMode.nicknames:
            if member.nick is None:
                return None
            name_sections = _split_name(member.nick)
        case NameUsageSearchMode.nicknames_and_usernames:
            name_sections = _split_name(member.name)
            if member.nick is not None:
                name_sections.union(_split_name(member.nick))
    return name_sections


def _split_name(name: str) -> set[str]:
    new_name = ""
    # remove special characters
    for char in name:
        if char.lower() in "abcdefghijklmnopqrstuvwxyz":
            new_name += char
        else:
            new_name += " "

    return set(new_name.split())


def _split_name_capitals(name_sections: set[str]) -> set[str]:
    member_sections: set[str] = set()
    for section in name_sections:
        if section in member_sections:
            continue

        parts: set[str] = set()
        match = 1
        cropped_section = section
        while match:
            match = re.search(
                r"[A-Z][a-z]*[A-Z]",
                cropped_section,
                re.MULTILINE
            )
            if match:
                caps = match.span()[1] - 1
                parts.add(cropped_section[:caps])
                cropped_section = cropped_section[caps:]
        if len(parts) != 0:
            member_sections.union(parts)
            member_sections.add(cropped_section)
        else:
            member_sections.add(cropped_section)

    return member_sections


def _get_name_usage_sections(
        members: typing.Sequence[discord.Member],
        mode: NameUsageSearchMode,
) -> dict[str, int]:
    section_counts: dict[str, int] = {}
    for member in members:
        name_sections = _get_member_name(member, mode)
        if name_sections is None:
            continue

        member_sections: set[str] = _split_name_capitals(name_sections)
        for section in member_sections:
            section_lower = section.lower()
            if section_lower in name_blacklist:
                continue
            if len(section_lower) < 3:
                continue
            if section_lower in section_counts:
                section_counts[section_lower] += 1
            else:
                section_counts[section_lower] = 1
    return section_counts


def _get_gettop_embed_pages(sections: dict[str, int]) -> list[typing.Any]:
    section_tuples = sorted(
        sections.items(), key=lambda x: x[1], reverse=True)
    pages = []
    for i in range(int(len(section_tuples) / 20 + 0.999) + 1):
        result_page = ""
        for section in section_tuples[0 + 20 * i:20 + 20 * i]:
            result_page += f"{section[1]} {section[0]}\n"
        if result_page == "":
            result_page = "_"
        pages.append(result_page)
    return pages


class NameUsage(
        commands.GroupCog,
        name="nameusage",
        description="Get data about which names are used in which server"
):
    def __init__(self) -> None:
        pass

    @app_commands.command(
        name="gettop",
        description="See how often different names occur in this server"
    )
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Search most-used usernames',
                                    value=NameUsageSearchMode.usernames.value),
        discord.app_commands.Choice(name='Search most-used nicknames',
                                    value=NameUsageSearchMode.nicknames.value),
        discord.app_commands.Choice(name='Search nicks and usernames',
                                    value=NameUsageSearchMode.nicknames_and_usernames.value),
    ])
    @not_in_dms_check
    async def nameusage_gettop(
            self,
            itx: GuildInteraction[Bot],
            mode: int
    ) -> None:
        # todo: split this function into multiple smaller functions
        await itx.response.defer(ephemeral=True)
        section_counts = _get_name_usage_sections(itx.guild.members, NameUsageSearchMode(mode))
        pages = _get_gettop_embed_pages(section_counts)

        mode_text = ("usernames" if mode == 1
                     else "nicknames" if mode == 2
                     else "usernames and nicknames")
        embed_title = f'Most-used {mode_text} leaderboard!'

        view = GetTopPageView(pages, embed_title, timeout=60)
        embed = view.make_page()
        await itx.followup.send("", embed=embed, view=view, ephemeral=True)

        await view.wait()
        await itx.edit_original_response(view=None)

    @app_commands.command(
        name="name",
        description="See how often different names occur in this server"
    )
    @app_commands.describe(name="What specific name are you looking for?")
    @app_commands.choices(search_type=[
        discord.app_commands.Choice(name='usernames', value=1),
        discord.app_commands.Choice(name='nicknames', value=2),
        discord.app_commands.Choice(name='Search both nicknames and usernames',
                                    value=3),
    ])
    @not_in_dms_check
    async def nameusage_name(
            self,
            itx: GuildInteraction[Bot],
            name: str,
            search_type: int,
            public: bool = False,
    ) -> None:
        await itx.response.defer(ephemeral=not public)
        count = 0
        type_string = ""
        match NameUsageSearchMode(search_type):
            case NameUsageSearchMode.usernames:
                type_string = "username"
                for member in itx.guild.members:
                    if name.lower() in member.name.lower():
                        count += 1
            case NameUsageSearchMode.nicknames:
                type_string = "nickname"
                for member in itx.guild.members:
                    if (member.nick is not None
                            and name.lower() in member.nick.lower()):
                        count += 1
            case NameUsageSearchMode.nicknames_and_usernames:
                type_string = "username or nickname"
                for member in itx.guild.members:
                    if member.nick is not None:
                        if (name.lower() in member.nick.lower()
                                or name.lower() in member.name.lower()):
                            count += 1
                    elif name.lower() in member.name.lower():
                        count += 1

        await itx.followup.send(
            f"I found {count} {'person' if count == 1 else 'people'} "
            f"with '{name.lower()}' in their {type_string}",
            ephemeral=not public,
        )
