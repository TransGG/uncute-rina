import re
# ^ to remove pronouns from user-/nicknames and split names at
#  capital letters.

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.nameusage.views.pageview import GetTopPageView
from resources.checks import not_in_dms_check
from resources.customs import Bot


class NameUsage(
        commands.GroupCog,
        name="nameusage",
        description="Get data about which names are used in which server"
):
    def __init__(self):
        pass

    @app_commands.command(
        name="gettop",
        description="See how often different names occur in this server"
    )
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Search most-used usernames',
                                    value=1),
        discord.app_commands.Choice(name='Search most-used nicknames',
                                    value=2),
        discord.app_commands.Choice(name='Search nicks and usernames',
                                    value=3),
    ])
    @app_commands.check(not_in_dms_check)
    async def nameusage_gettop(
            self,
            itx: discord.Interaction[Bot],
            mode: int
    ):
        # todo: split this function into multiple smaller functions
        await itx.response.defer(ephemeral=True)
        sections = {}
        for member in itx.guild.members:
            member_sections = []
            if mode == 1:  # most-used usernames
                names = [member.name]
            elif mode == 2 and member.nick is not None:  # most-used nicknames
                names = [member.nick]
            elif mode == 3:  # most-used nicks and usernames
                names = [member.name]
                if member.nick is not None:
                    names.append(member.nick)
            else:
                continue

            _pronouns = [
                "she", "her",
                "he", "him",
                "they", "them",
                "it", "its",
            ]
            pronouns = []
            for pronounx in _pronouns:
                for pronouny in _pronouns:
                    pronouns.append(pronounx + " " + pronouny)

            for index in range(len(names)):
                new_name = ""
                for char in names[index]:
                    if char.lower() in "abcdefghijklmnopqrstuvwxyz":
                        new_name += char
                    else:
                        new_name += " "

                for pronoun in pronouns:
                    _name_backup = new_name + " "
                    while new_name != _name_backup:
                        _name_backup = new_name
                        new_name = re.sub(
                            pronoun,
                            "",
                            new_name,
                            flags=re.IGNORECASE
                        )

                names[index] = new_name

            def add(member_name_part):
                if member_name_part not in member_sections:
                    member_sections.append(member_name_part)

            for name in names:
                for section in name.split():
                    if section in member_sections:
                        pass
                    else:
                        parts = []
                        match = 1
                        while match:
                            match = re.search(
                                "[A-Z][a-z]*[A-Z]",
                                section,
                                re.MULTILINE
                            )
                            if match:
                                caps = match.span()[1] - 1
                                parts.append(section[:caps])
                                section = section[caps:]
                        if len(parts) != 0:
                            for part in parts:
                                add(part)
                            add(section)
                        else:
                            add(section)

            for section in member_sections:
                section = section.lower()
                if section in ["the", "any", "not"]:
                    continue
                if len(section) < 3:
                    continue
                if section in sections:
                    sections[section] += 1
                else:
                    sections[section] = 1

        sections = sorted(sections.items(), key=lambda x: x[1], reverse=True)
        pages = []
        for i in range(int(len(sections) / 20 + 0.999) + 1):
            result_page = ""
            for section in sections[0 + 20 * i:20 + 20 * i]:
                result_page += f"{section[1]} {section[0]}\n"
            if result_page == "":
                result_page = "_"
            pages.append(result_page)

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
    @app_commands.check(not_in_dms_check)
    async def nameusage_name(
            self,
            itx: discord.Interaction[Bot],
            name: str,
            search_type: int,
            public: bool = False
    ):
        await itx.response.defer(ephemeral=not public)
        count = 0
        type_string = ""
        if search_type == 1:  # usernames
            for member in itx.guild.members:
                if name.lower() in member.name.lower():
                    count += 1
            type_string = "username"
        elif search_type == 2:  # nicknames
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower():
                        count += 1
            type_string = "nickname"
        elif search_type == 3:  # usernames and nicknames
            for member in itx.guild.members:
                if member.nick is not None:
                    if (name.lower() in member.nick.lower()
                            or name.lower() in member.name.lower()):
                        count += 1
                elif name.lower() in member.name.lower():
                    count += 1
            type_string = "username or nickname"
        await itx.followup.send(
            f"I found {count} {'person' if count == 1 else 'people'} "
            f"with '{name.lower()}' in their {type_string}",
            ephemeral=not public,
        )
