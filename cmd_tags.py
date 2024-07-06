from import_modules import *

report_message_reminder_unix = 0 #int(mktime(datetime.now().timetuple()))

class SendPublicly_TagView(discord.ui.View):
    def __init__(self, client: Bot, embed: discord.Embed, timeout=None, public_footer=None, logmsg=None, tag_name=None):
        super().__init__()
        if embed.footer.text is None:
            self.footer = ""
        else:
            self.footer = embed.footer.text + "\n"

        self.value = None
        self.client = client
        self.timeout = timeout
        self.public_footer = public_footer
        self.embed = embed
        self.logmsg = logmsg
        self.tag_name = tag_name

    @discord.ui.button(label='Send publicly', style=discord.ButtonStyle.primary)
    async def send_publicly(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = 1
        if self.public_footer is None:
            self.public_footer = f"Triggered by {itx.user.name} ({itx.user.id})"
        else:
            self.public_footer = f"Note: If you believe that this command was misused or abused, " + \
                                 f"please do not argue in this channel. Instead, open a mod ticket " + \
                                 f"and explain the situation there. Thank you."
            self.value = 2
        self.embed.set_footer(text=self.footer + self.public_footer)
        await itx.response.edit_message(content="Sent successfully!", embed=None, view=None)
        msg = await itx.followup.send("", embed=self.embed, ephemeral=False, allowed_mentions=discord.AllowedMentions.none(), wait=True)
        if self.value == 2 and self.logmsg is not None:
            await log_to_guild(self.client, itx.guild, self.logmsg)
            cmd_mention = self.client.get_command_mention("tag")
            if itx.guild_id not in EnabledServers.dev_server_ids():
                staff_message_reports_channel = self.client.get_channel(self.client.custom_ids["staff_reports_channel"])
                await staff_message_reports_channel.send(f"{itx.user.name} (`{itx.user.id}`) used {cmd_mention} `tag:{self.tag_name}` anonymously, in {itx.channel.mention} (`{itx.channel.id}`)\n"
                                                         f"[Jump to the tag message]({msg.jump_url})")
        self.stop()

    async def on_timeout(self):
        self.send_publicly.disabled = True
        self.send_publicly.style = discord.ButtonStyle.gray

class Tags:
    def __init__(self):
        self.no_politics_channel_id = 1126163144134361238
        self.no_venting_channel_id = 1126163020620513340

    async def tag_message(self, tag_name: str, itx: discord.Interaction, client: Bot, public: bool, anonymous: bool, 
                          embed: discord.Embed, public_footer: bool = False):
        """
        Send a tag message (un)publicly or (un)anonymously, given an embed.
        
        ### Parameters
        tag_name: :class:`str`
            The tag's custom ID used in the code, and in logs
        itx: :class:`discord.Interaction`
            The interaction to reply to
        client: :class:`UncuteRina.Bot`
            The Bot client, for logs
        public: :class:`bool`
            Whether to send the tag publicly or not
        anonymous: :class:`bool`
            Whether to make public tags show the executor's username or not (auomatically adds a log msg)
        embed: :class:`discord.Embed`
            The embed to send, with information about the selected tag
        public_footer: :class:`bool`
            Whether to add the pre-made 'misused command' footer to the embed if sent anonymously
        """

        embed.color = colours[tag_name]
        cmd_mention = client.get_command_mention("tag")
        logmsg = f"{itx.user.name} ({itx.user.id}) used {cmd_mention} `tag:{tag_name}` anonymously"
        if public:
            if anonymous:
                if public_footer:
                    embed.set_footer(text = f"Note: If you believe that this command was misused or abused, " 
                                            f"please do not argue in this channel. Instead, open a mod ticket " 
                                            f"and explain the situation there. Thank you.")
                await itx.response.send_message("sending...", ephemeral=True)
                msg = await itx.followup.send(embed=embed, ephemeral=False, wait=True)
                await log_to_guild(client, itx.guild, logmsg)
                if itx.guild_id not in EnabledServers.dev_server_ids():
                    staff_message_reports_channel = client.get_channel(client.custom_ids["staff_reports_channel"])
                    await staff_message_reports_channel.send(f"{itx.user.name} (`{itx.user.id}`) used {cmd_mention} `tag:{tag_name}` anonymously, in {itx.channel.mention} (`{itx.channel.id}`)\n"
                                                             f"[Jump to the tag message]({msg.jump_url})")
            else:
                await itx.response.send_message(embed=embed)
        else:
            if anonymous:
                view = SendPublicly_TagView(client, embed, timeout=60, public_footer=public_footer, logmsg=logmsg, tag_name=tag_name)
            else:
                view = SendPublicly_TagView(client, embed, timeout=60, tag_name=tag_name)
            await itx.response.send_message(f"", embed=embed, view=view, ephemeral=True)
            if await view.wait():
                await itx.edit_original_response(view=view)

    # region Tags
    async def send_report_info(self, tag_name: str, context: discord.Interaction | discord.TextChannel, client: Bot, additional_info: None | list[str, int]=None, public=False, anonymous=True):
        # additional_info = [message.author.name, message.author.id]
        mod_ticket_channel_id = get_mod_ticket_channel_id(client, context.guild.id)
        embed = discord.Embed(
            title='Reporting a message or scenario',
            description="Hi there! If anyone is making you uncomfortable, or you want to "
                        "report or prevent a rule-breaking situation, you can `Right Click "
                        "Message > Apps > Report Message` to notify our staff confidentially. "
                       f"You can also create a mod ticket in <#{mod_ticket_channel_id}> or DM a staff " # channel-id = #contact-staff
                        "member.")
        embed.set_image(url="https://i.imgur.com/jxEcGvl.gif")
        if isinstance(context, discord.Interaction):
            await self.tag_message(tag_name, context, client, public, anonymous, embed, public_footer=True)
        else:
            if additional_info is not None:
                embed.set_footer(text=f"Triggered by {additional_info[0]} ({additional_info[1]})")
            await context.send(embed=embed)

    async def send_customvc_info(self, tag_name: str, itx: discord.Interaction, client: Bot, public, anonymous):
        vc_hub = await client.get_guild_info(itx.guild, "vcHub")

        cmd_mention = client.get_command_mention('editvc')
        cmd_mention2 = client.get_command_mention('vctable about')
        embed = discord.Embed(
            title="TransPlace's custom voice channels (vc)",
            description=f"In our server, you can join <#{vc_hub}> to create a custom vc. You "
                        f"are then moved to this channel automatically. You can change the name and user "
                        f"limit of this channel with the {cmd_mention} command. When everyone leaves the "
                        f"channel, the channel is deleted automatically."
                        f"You can use {cmd_mention2} for additional features.")
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)

    async def send_triggerwarning_info(self, tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Using trigger warnings correctly",
            description="Content or trigger warnings (CW and TW for short) are notices placed before a "
                        "(section of) text to warn the reader of potential traumatic triggers in it. Often, "
                        "people might want to avoid reading these, so a warning will help them be aware of "
                        "it.\n"
                        "You can warn the reader in the beginning or the middle of the text, and spoiler the "
                        "triggering section like so: \"TW: ||guns||: ||The gun was fired.||\".\n"
                        "\n"
                        r"You can spoiler messages with a double upright slash \|\|text\|\|." "\n"
                        "Some potential triggers include (TW: triggers): abuse, bugs/spiders, death, "
                        "dieting/weight loss, injections, self-harm, transmed/truscum points of view or "
                        "transphobic content.")
        await self.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)

    async def send_toneindicator_info(self, tag_name: str, itx: discord.Interaction, client: Bot, public, anonymous):
        embed = discord.Embed(
            title="When to use tone indicators?",
            description="Tone indicators are a useful tool to clarify the meaning of a message.\n"
                        "Occasionally, people reading your comment may not be certain about the tone of "
                        "a message. Is it meant as positive feedback, a joke, or sarcasm?\n"
                        "\n"
                        "For example, you may playfully tease a friend. Without tone indicators, the "
                        "message may come across as rude or mean, but adding “/lh” (meaning light-"
                        "hearted) helps clarify that it was meant in good fun.\n"
                        "\n"
                        "Some tone indicators have multiple definitions depending on the context. For "
                        "example: \"/m\" can mean 'mad' or 'metaphor'. You can look up tone indicators by "
                        f"their tag or definition using {client.get_command_mention('toneindicator')}."
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)

    async def send_trustedrole_info(self, tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="The trusted role (and selfies)",
            description="The trusted role is the role we use to add an extra layer of protection to some "
                        "aspects of our community. Currently, this involves the selfies channel, but may be "
                        "expanded to other channels in future.\n"
                        "\n"
                        "You can obtain the trusted role by sending 500 messages or after gaining the "
                        "equivalent XP from voice channel usage. If you rejoin the server you can always "
                        "ask for the role back too!"
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)

    async def send_imagebanrole_info(self, tag_name: str, itx: discord.Interaction, client, public, anonymous):
        mod_ticket_channel_id = get_mod_ticket_channel_id(client, itx.guild.id)
        embed = discord.Embed(
            title="TEB role (Image Ban)",
            description="**Why can't I send images in the server? Why are my .GIFs only sending links and not "
                        "the actual meme I was hoping for?**\n"
                        "\n"
                        "You have the TEB role (Temporary Embed Ban, or Image Ban for short). There may be a "
                        "number of reasons for it, but the most common one is that most new verifications "
                        "have it. Don't worry - you're not in trouble if this is the case. It's simply a "
                        "method we use to prevent trolls and other bad actors from spamming our server.\n"
                        "\n"
                        "If you've been active on the server for a bit and need this role removed, please "
                       f"don't hesitate to make a ticket in <#{mod_ticket_channel_id}>.\n"
                        "Do note that mods will *only* remove the role if you have been active enough in the "
                        "server and weren't given the role from a warning."
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)

    async def send_selfies_info(self, tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Selfies and the #selfies channel",
            description="For your own and other's safety, the selfies channel is hidden behind the "
                        "trusted role. This role is granted automatically when you've been active in "
                        "the server for long enough. We grant the role after 500 messages or 9 hours "
                        "in VC or a combination of both.\n"
                        "\n"
                        "The selfies channel automatically deletes all messages after 7 days to ensure "
                        "the privacy and safety of our members."
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)

    async def send_minimodding_info(self, tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Correcting staff or minimodding",
            description="If you have any input on how members of staff operate, please open a ticket to "
                        "properly discuss."
                        "\n"
                        "Please do not interfere with moderator actions, as it can make situations worse. It can be seen as "
                        "harassment, and you could be warned."
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)
        
    async def send_avoidpolitics_info(self, tag_name: str, itx: discord.Interaction, client: Bot, public, anonymous):
        cmd_mention = client.get_command_mention("remove-role")
        embed = discord.Embed(
            title="Please avoid political discussions!",
            description="A member has requested that we avoid political discussions in this chat, we kindly "
                        "ask that you refrain from discussing politics in this chat to maintain a positive and "
                        "uplifting environment for all members.\n"
                        "Our community focuses on highlighting the positive aspects of the trans "
                        "community. Political discussions often detract from this goal and create "
                        "negative air and conflict among members.\n"
                        f"Check out <#{self.no_politics_channel_id}>. If you can't see this, use {cmd_mention} `role:NPA`"
                        "\n"
                        "If you continue discussing politics, a moderator may need to take action and mute "
                        "you. Thank you for your cooperation."
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)

    async def send_chat_topic_change_request(self, tag_name: str, itx:discord.Interaction,  client,public, anonymous):
        embed = discord.Embed(
            title="Please change chat topic",
            description="A community member has requested a change of topic as the current one is making them "
                        "uncomfortable. Please refrain from continuing the current line of discussion and find "
                        "a new topic."
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)

    async def send_conversing_effectively_info(self, tag_name: str, itx:discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Conversing effectively",
            description="When you have a question and hope to find the answer quickly, don't start with just "
                        "\"hi\", but instead also immediately ask the question. That way, you don't have to wait "
                        "for a response twice.\n"
                        "\n"
                        "Your first question shouldn't be \"Can I ask something?\" or \"Are there any [subject] "
                        "experts around?\", but rather something like: \"How do I do [problem] with [subject] and "
                        "[other relevant info]?\""
        )
        embed.set_footer(text="More info: https://www.nohello.net/, https://dontasktoask.com/")
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)
 
    async def send_pluralkit_info(self, tag_name: str, itx:discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="PluralKit and users with the [BOT] tag",
            description="PluralKit is a Discord bot that allows users to proxy their messages via Discord webhooks. This allows for "
                        "one discord account to have multiple psudo accounts, without the need to have alts in the server.\n"
                        "\n"
                        "These messages are sent via the bot and get a [BOT] tag, but the user behind them is **not** a bot.\n"
                        "\n"
                        "PluralKit can have multiple uses in other communities. However, in ours it should only be used for plurality, "
                        "self-identity purposes, or as a mental health aid.\n"
                        "- Learn more? Check out <https://quiltmc.org/en/community/pluralkit/>\n"
                        "\n"
                        "***We do not allow users to make use of PluralKit for role-playing.***"
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)

    async def send_maturerole_info(self, tag_name: str, itx:discord.Interaction, client, public, anonymous):
        mod_ticket_channel_id = get_mod_ticket_channel_id(client, itx)
        embed = discord.Embed(
            title="Mature role and \\#mature\\-chat",
            description="Our server is accessible to people of all ages. Because of that, you may often "
                        "come across young people figuring things out regarding their identity. If you "
                        "feel more like talking about finance or working, these chats may not offer the "
                        "right conversation partners. In such cases, the \\# mature-chat may be something for you!\n"
                        "\n"
                        "The channel is 18+, with the intention of keeping the chat more mature. You must still follow "
                        "all server rules.\n"
                        f"Access the channel by making a ticket in <#{mod_ticket_channel_id}>!"
        )
        await self.tag_message(tag_name, itx, client, public, anonymous, embed)    
    #endregion Tags

class TagFunctions(commands.Cog):
    def __init__(self, client):
        self.client: Bot = client

    @commands.Cog.listener()
    async def on_message(self, message):
        global report_message_reminder_unix
        if message.author.bot:
            return

        for staff_role_mention in ["<@&981735650971775077>",  # transplace moderator
                                   "<@&1012954384142966807>", # transplace sr. mod
                                   "<@&981735525784358962>",  # transplace admin
                                #    "<@&1109905190372524132>", # transonance admin
                                #    "<@&1108771208931049544>", # transonance staff
                                #    "<@&1087014898418061363>", # enbyplace moderator
                                #    "<@&1087014898418061365>", # enbyplace sr. mod
                                #    "<@&1087014898418061367>", # enbyplace admin
                                   ]:
            if staff_role_mention in message.content:
                time_now = int(mktime(datetime.now().timetuple())) # get time in unix
                if time_now - report_message_reminder_unix > 900: # 15 minutes
                    await Tags().send_report_info("report", message.channel, self.client, additional_info=[message.author.name, message.author.id])
                    report_message_reminder_unix = time_now
                    break

    async def tag_autocomplete(self, itx: discord.Interaction, current: str):
        if current == "":
            return [app_commands.Choice(name="Show list of tags", value="help")]
        
        options = [i.lower() for i in tag_info_dict if itx.guild_id in tag_info_dict[i][2]]
        return [
            app_commands.Choice(name=term, value=term)
            for term in options if current.lower() in term
        ][:15]

    @app_commands.command(name="tag", description="Look up something through a tag")
    @app_commands.describe(tag="What tag do you want more information about?")
    @app_commands.describe(public="Show everyone in chat? (default: yes)")
    @app_commands.describe(anonymous="Hide your name when sending the message publicly? (default: yes)")
    @app_commands.autocomplete(tag=tag_autocomplete)
    async def tag(self, itx: discord.Interaction, tag: str, public: bool = True, anonymous: bool = True):
        options = [i for i in tag_info_dict if itx.guild_id in tag_info_dict[i][2]]
        tag = tag.lower()
        if tag in options:
            await tag_info_dict[tag][1](tag, itx, self.client, public=public, anonymous=anonymous)
        elif tag in tag_info_dict:
            ticket_channel = get_mod_ticket_channel_id(self.client, itx)
            await itx.response.send_message(f"This tag is not enabled in this server! If you think this is a mistake, make a staff ticket (<#{ticket_channel}>).", ephemeral=True)
        elif tag == "help":
            await itx.response.send_message("List of tags currently available to send:\n" +
                                            '\n'.join(["- " + i for i in tag_info_dict]), ephemeral=True)
        else:
            await itx.response.send_message("No tag found with this name!", ephemeral=True)

    async def role_autocomplete(self, itx: discord.Interaction, current: str):
        role_options = {
            1126160553145020460: ("Hide Politics channel role",  "NPA"), #NPA
            1126160612620243044: ("Hide Venting channel role", "NVA") # NVA
        }
        options = []
        for role in itx.user.roles:
            if role.id in role_options:
                if current.lower() in role_options[role.id][0].lower() or current.lower() in role_options[role.id][1].lower():
                    options.append(role.id)
        if options:
            return [
                app_commands.Choice(name=role_options[role_id][0], value=role_options[role_id][1])
                for role_id in options
            ][:15]
        else:
            return[app_commands.Choice(name="You don't have any roles to remove!", value="none")]

    @app_commands.command(name="remove-role", description="Remove one of your agreement roles")
    @app_commands.describe(role_name="The name of the role to remove")
    @app_commands.autocomplete(role_name=role_autocomplete)
    async def remove_role(self, itx: discord.Interaction, role_name: str):
        role_options = {
            "npa":["NPA", 1126160553145020460],
            "nva":["NVA", 1126160612620243044],
        }
        if role_name.lower() not in role_options:
            await itx.response.send_message("You can't remove that role!", ephemeral=True)
            return

        role_id = role_options[role_name.lower()][1]
        try:
            for role in itx.user.roles:
                if role.id == role_id:
                    await itx.user.remove_roles(role, reason="Removed by user using /remove-role")
                    await itx.response.send_message("Successfully removed role!", ephemeral=True)
                    return
        except discord.Forbidden:
            await itx.response.send_message("I couldn't remove this role! (Forbidden)", ephemeral=True)
            return

t: Tags = Tags()
tag_info_dict: dict[str, tuple[tuple[int,int,int], typing.Callable, int]] = \
{ # (sorted ABC and by hue; change hue)   (Hue  Sat  value (HSV) , tag function,              servers they're active in)
    "avoiding politics"               : ([  0,  40, 100], t.send_avoidpolitics_info,          EnabledServers.all_server_ids()),
    "conversing effectively"          : ([ 20,  40, 100], t.send_conversing_effectively_info, EnabledServers.all_server_ids()),
    "customvcs"                       : ([ 40,  40, 100], t.send_customvc_info,               EnabledServers.all_server_ids()),
    "image ban role"                  : ([ 60,  40, 100], t.send_imagebanrole_info,           EnabledServers.transplace_etc_ids()),
    "mature role and mature chat"     : ([ 80,  40, 100], t.send_maturerole_info,             EnabledServers.transplace_etc_ids()),
    "minimodding or correcting staff" : ([100,  40, 100], t.send_minimodding_info,            EnabledServers.all_server_ids()),
    "please change topic"             : ([120,  40, 100], t.send_chat_topic_change_request,   EnabledServers.all_server_ids()),
    "plural kit"                      : ([140,  40, 100], t.send_pluralkit_info,              EnabledServers.all_server_ids()),
    "report"                          : ([  0, 100, 100], t.send_report_info,                 EnabledServers.all_server_ids()),
    "selfies"                         : ([160,  40, 100], t.send_selfies_info,                EnabledServers.transplace_etc_ids()),
    "tone indicators"                 : ([180,  40, 100], t.send_toneindicator_info,          EnabledServers.all_server_ids()),
    "trigger warnings"                : ([200,  40, 100], t.send_triggerwarning_info,         EnabledServers.all_server_ids()),
    "trusted role"                    : ([220,  40, 100], t.send_trustedrole_info,            EnabledServers.transplace_etc_ids()),
}
colours = {k: discord.Colour.from_hsv(v[0][0]/360, v[0][1]/100, v[0][2]/100) for k, v in tag_info_dict.items()}

async def setup(client):
    await client.add_cog(TagFunctions(client))
