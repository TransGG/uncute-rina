import discord, discord.ext.commands as commands, discord.app_commands as app_commands
import re # to remove pronouns from user-/nicknames and split names at capital letters
from resources.customs.bot import Bot
from resources.views.nameusage import PageView_NameUsage_GetTop


class NameUsage(commands.GroupCog, name="nameusage",description="Get data about which names are used in which server"):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="gettop", description="See how often different names occur in this server")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Search most-used usernames', value=1),
        discord.app_commands.Choice(name='Search most-used nicknames', value=2),
        discord.app_commands.Choice(name='Search nicks and usernames', value=3),
    ])
    async def nameusage_gettop(self, itx: discord.Interaction, mode: int):
        await itx.response.defer(ephemeral=True)
        sections = {}
        for member in itx.guild.members:
            member_sections = []
            if mode == 1: # most-used usernames
                names = [member.name]
            elif mode == 2 and member.nick is not None: # most-used nicknames
                names = [member.nick]
            elif mode == 3: # most-used nicks and usernames
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
                        new_name = re.sub(pronoun, "", new_name, flags=re.IGNORECASE)

                names[index] = new_name

            def add(part):
                if part not in member_sections:
                    member_sections.append(part)

            for name in names:
                for section in name.split():
                    if section in member_sections:
                        pass
                    else:
                        parts = []
                        match = 1
                        while match:
                            match = re.search("[A-Z][a-z]*[A-Z]", section, re.MULTILINE)
                            if match:
                                caps = match.span()[1]-1
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

        sections = sorted(sections.items(), key=lambda x:x[1], reverse=True)
        pages = []
        for i in range(int(len(sections)/20+0.999)+1):
            result_page = ""
            for section in sections[0+20*i:20+20*i]:
                result_page += f"{section[1]} {section[0]}\n"
            if result_page == "":
                result_page = "_"
            pages.append(result_page)
        page = 0
        
        result_page = pages[page]
        result_page2 = pages[page+1]
        embed_title = f'Most-used {"user" if mode==1 else "nick" if mode==2 else "usernames and nick"}names leaderboard!'
        embed = discord.Embed(color=8481900, title=embed_title)
        embed.add_field(name="Column 1",value=result_page)
        embed.add_field(name="Column 2",value=result_page2)
        embed.set_footer(text="page: "+str(page+1)+" / "+str(int(len(pages)/2)))
        view = PageView_NameUsage_GetTop(pages, embed_title, timeout=60)
        await itx.followup.send(f"",embed=embed, view=view,ephemeral=True)
        await view.wait()
        if view.value is None:
            await itx.edit_original_response(view=None)

    @app_commands.command(name="name", description="See how often different names occur in this server")
    @app_commands.describe(name="What specific name are you looking for?")
    @app_commands.choices(type=[
        discord.app_commands.Choice(name='usernames', value=1),
        discord.app_commands.Choice(name='nicknames', value=2),
        discord.app_commands.Choice(name='Search both nicknames and usernames', value=3),
    ])
    async def nameusage_name(self, itx: discord.Interaction, name: str, type: int, public: bool = False):
        await itx.response.defer(ephemeral=not public)
        count = 0
        type_string = ""
        if type == 1: # usernames
            for member in itx.guild.members:
                if name.lower() in member.name.lower():
                    count += 1
            type_string = "username"
        elif type == 2: # nicknames
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower():
                        count += 1
            type_string = "nickname"
        elif type == 3: # usernames and nicknames
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower() or name.lower() in member.name.lower():
                        count += 1
                elif name.lower() in member.name.lower():
                    count += 1
            type_string = "username or nickname"
        await itx.followup.send(f"I found {count} {"person" if count == 1 else "people"} with '{name.lower()}' in their {type_string}",ephemeral=not public)


async def setup(client):
    await client.add_cog(NameUsage(client))