from typing import Callable

import discord

from resources.customs.bot import Bot
from resources.customs.utils import EnabledServers
from resources.utils.utils import get_mod_ticket_channel_id  # for ticket channel id in Report tag
from resources.utils.utils import log_to_guild
# ^ for logging when people send tags anonymously (in case someone abuses the anonymity)

from extensions.tags.views import SendPubliclyTagView


class Tags:
    no_politics_channel_id = 1126163144134361238
    no_venting_channel_id = 1126163020620513340

    @staticmethod
    async def tag_message(
            tag_name: str, itx: discord.Interaction, client: Bot, public: bool, anonymous: bool,
            embed: discord.Embed, public_footer: bool = False
    ):
        """
        Send a tag message (un)publicly or (un)anonymously, given an embed.

        Parameters
        -----------
        tag_name: :class:`str`
            The tag's custom ID used in the code, and in logs.
        itx: :class:`discord.Interaction`
            The interaction to reply to.
        client: :class:`UncuteRina.Bot`
            The Bot client, for logs.
        public: :class:`bool`
            Whether to send the tag publicly or not.
        anonymous: :class:`bool`
            Whether to make public tags show the executor's username or not (auomatically adds a log msg).
        embed: :class:`discord.Embed`
            The embed to send, with information about the selected tag.
        public_footer: :class:`bool`, optional
            Whether to add the pre-made 'misused command' footer to the embed if sent anonymously. Default: False.
        """

        embed.colour = colours[tag_name]
        cmd_mention = client.get_command_mention("tag")
        log_msg = f"{itx.user.name} (`{itx.user.id}`) used {cmd_mention} `tag:{tag_name}` anonymously"
        if public:
            if anonymous:
                if public_footer:
                    embed.set_footer(text=f"Note: If you believe that this command was misused or abused, "
                                          f"please do not argue in this channel. Instead, open a mod ticket "
                                          f"and explain the situation there. Thank you.")
                await itx.response.send_message("sending...", ephemeral=True)
                try:
                    # try sending the message without replying to the previous ephemeral
                    msg = await itx.channel.send(embed=embed)
                except discord.Forbidden:
                    msg = await itx.followup.send(embed=embed, ephemeral=False, wait=True)
                log_msg += f", in {itx.channel.mention} (`{itx.channel.id}`)\n[Jump to the tag message]({msg.jump_url})"
                await log_to_guild(client, itx.guild, log_msg)
                staff_message_reports_channel = client.get_channel(client.custom_ids["staff_reports_channel"])
                await staff_message_reports_channel.send(log_msg)
            else:
                await itx.response.send_message(embed=embed)
        else:
            if anonymous:
                view = SendPubliclyTagView(client, embed, timeout=60, public_footer=public_footer, log_msg=log_msg,
                                           tag_name=tag_name)
            else:
                view = SendPubliclyTagView(client, embed, timeout=60, tag_name=tag_name)
            await itx.response.send_message(f"", embed=embed, view=view, ephemeral=True)

    # region Tags
    @staticmethod
    async def send_report_info(
            tag_name: str,
            context: discord.Interaction | discord.TextChannel,
            client: Bot,
            additional_info: None | list[str | int] = None,
            public=False,
            anonymous=True
    ):
        # additional_info = [message.author.name, message.author.id]
        mod_ticket_channel_id = get_mod_ticket_channel_id(client, context.guild.id)
        embed = discord.Embed(
            title='Reporting a message or scenario',
            description="Hi there! If anyone is making you uncomfortable, or you want to "
                        "report or prevent a rule-breaking situation, you can `Right Click "
                        "Message > Apps > Report Message` to notify our staff confidentially. "
                        f"You can also create a mod ticket in <#{mod_ticket_channel_id}> or DM a staff "
            # mod_ticked_channel_id = #contact-staff
                        "member.")
        embed.set_image(url="https://i.imgur.com/jxEcGvl.gif")
        if isinstance(context, discord.Interaction):
            await Tags.tag_message(tag_name, context, client, public, anonymous, embed, public_footer=True)
        else:
            if additional_info is not None:
                embed.set_footer(text=f"Triggered by {additional_info[0]} ({additional_info[1]})")
            await context.send(embed=embed)

    @staticmethod
    async def send_customvc_info(tag_name: str, itx: discord.Interaction, client: Bot, public, anonymous):
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
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_triggerwarning_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
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
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)

    @staticmethod
    async def send_toneindicator_info(tag_name: str, itx: discord.Interaction, client: Bot, public, anonymous):
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
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_trustedrole_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="The trusted role (and selfies)",
            description="The trusted role is the role we use to add an extra layer of protection to some "
                        "aspects of our community. Currently, this involves the selfies channel, but may be "
                        "expanded to other channels in future.\n"
                        "\n"
                        "You can obtain the trusted role by reaching level 6 by sending messages or talking in "
                        "voice channels. If you rejoin the server you can always "
                        "ask for the role back too!"
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_imagebanrole_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
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
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_selfies_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Selfies and the #selfies channel",
            description="For your own and other's safety, the selfies channel is hidden behind the "
                        "trusted role. This role is granted automatically when you've been active in "
                        "the server for long enough. We grant the role at level six which can be "
                        "obtained by sending messages or chatting in VC or a combination of both.\n"
                        "\n"
                        "The selfies channel automatically deletes all messages after 7 days to ensure "
                        "the privacy and safety of our members."
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_minimodding_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Correcting staff or minimodding",
            description="If you have any input on how members of staff operate, please open a ticket to "
                        "properly discuss."
                        "\n"
                        "Please do not interfere with moderator actions, as it can make situations worse. "
                        "It can be seen as harassment, and you could be warned."
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)

    @staticmethod
    async def send_avoidpolitics_info(tag_name: str, itx: discord.Interaction, client: Bot, public, anonymous):
        cmd_mention = client.get_command_mention("remove-role")
        embed = discord.Embed(
            title="Please avoid political discussions!",
            description="A member has requested that we avoid political discussions in this chat. We kindly "
                        "ask that you refrain from discussing politics to maintain a positive and "
                        "uplifting environment for all members.\n"
                        "Our community focuses on highlighting the positive aspects of the trans "
                        "community. Political discussions often detract from this goal and create "
                        "negative air and conflict among members.\n"
                        f"Check out <#{Tags.no_politics_channel_id}>. If you can't see this, use "
                        f"{cmd_mention} `role:NPA`\n"
                        "If you continue discussing politics, a moderator may need to take action and mute "
                        "you. Thank you for your cooperation."
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)

    @staticmethod
    async def send_avoidventing_info(tag_name: str, itx: discord.Interaction, client: Bot, public, anonymous):
        cmd_mention = client.get_command_mention("remove-role")
        embed = discord.Embed(
            title="Please avoid venting / doomposting!",
            description="A member has requested that we avoid venting / doomposting in this chat. We kindly "
                        "ask that you refrain from venting to maintain a positive, uplifting and "
                        "safe environment for all members.\n"
                        "Venting often means sharing negative thoughts or feeling to gain support. This can "
                        "become a burden to others to be an emotional support buddy. Be mindful of people "
                        "around you or see if you can get support from family, friends, or a therapist.\n"
                        f"Check out <#{Tags.no_venting_channel_id}>. If you can't see this, use "
                        f"{cmd_mention} `role:NVA`\n"
                        f"If you continue venting or doomposting, a moderator may need to take action and mute "
                        f"you. Thank you for your cooperation."
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)


    @staticmethod
    async def send_chat_topic_change_request(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Please change chat topic",
            description="A community member has requested a change of topic as the current one is making them "
                        "uncomfortable. Please refrain from continuing the current line of discussion and find "
                        "a new topic."
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed, public_footer=True)

    @staticmethod
    async def send_conversing_effectively_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
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
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_pluralkit_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="PluralKit and users with the [APP] tag",
            description="PluralKit is a Discord bot that allows users to proxy their messages via Discord webhooks. "
                        "This allows for one discord account to have multiple pseudo accounts, without the need to "
                        "have alts in the server.\n"
                        "\n"
                        "These messages are sent via the bot and get a [APP] tag, but the user behind them is **not** "
                        "a bot.\n"
                        "\n"
                        "PluralKit can have multiple uses in other communities. However, in ours it should only be "
                        "used for plurality, self-identity purposes, or as a mental health aid.\n"
                        "- Learn more? Check out <https://quiltmc.org/en/community/pluralkit/>\n"
                        "\n"
                        "***We do not allow users to make use of PluralKit for role-playing.***"
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_maturerole_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
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
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_syscourse_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Please avoid system discourse",
            description="A member has requested that we avoid discussions of system origins, including but "
                        "not limited to: __Tuplas__; __Tuplagenic, Endogenic, and non-Traumagenic systems__; __system "
                        "hopping__; and __intentional splits__.\n\n"
                        "We kindly ask that you **refrain from discussing system origins** to maintain a positive "
                        "and uplifting environment for all members and to **avoid controversial topics** such as "
                        "the \"Endogenic vs. Traumagenic\" debate and other system discourse.\n\n"
                        "This is a **trans-focused server** and **not system-focused**, so we cannot take a strong "
                        "stance on controversial topics within systems communities, and not all moderators are "
                        "educated on systems and system discourse. "
                        "If you continue discussing system origins or other disallowed topics, a moderator may "
                        "need to take action and mute you. Thank you for your cooperation."
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_pksettag_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        embed = discord.Embed(
            title="Please set a PluralKit server tag",
            description="Please set a server tag via PluralKit. You can do that by doing `pk;system servertag [tag]`"
                        " in the bot commands channel.\n\n"
                        "A tag is an emoji or word that represents your system to make it easier "
                        "for moderators and users to identify what system you are a part of without "
                        "needing to use commands or ask you.\n\n"
                        "Example: Apocalypse System uses ☣️ as a system tag, but \"[Mod]\" as a server "
                        "tag to be easily identifiable as a moderator."
        )
        await Tags.tag_message(tag_name, itx, client, public, anonymous, embed)

    @staticmethod
    async def send_enabling_embeds_info(tag_name: str, itx: discord.Interaction, client, public, anonymous):
        txt = ("**Enabling Embeds**\n"
               "Embeds are a neat feature in discord that let you preview websites and show certain messages "
               "in a nicer format. Many bots make use of embeds to lay out information, as do I.\n"
               "Users can enable and disable this setting manually. Simply go to `Discord > App Settings > Chat > "
               "Embeds and Link Previews > Show embeds and previews website links pasted into chat` and toggle "
               "that setting.")
        if anonymous:
            if public:
                await itx.response.send_message("sending...", ephemeral=True)
                try:
                    msg = await itx.channel.send(txt)
                    cmd_mention = client.get_command_mention("tag")
                    log_msg = (f"{itx.user.name} ({itx.user.id}) used {cmd_mention} `tag:{tag_name}` anonymously, "
                               f"in {itx.channel.mention} (`{itx.channel.id}`)\n"
                               f"[Jump to the tag message]({msg.jump_url})")
                    await log_to_guild(client, itx.guild, log_msg)
                    staff_message_reports_channel = client.get_channel(client.custom_ids["staff_reports_channel"])
                    await staff_message_reports_channel.send(log_msg)
                except discord.Forbidden:
                    await itx.followup.send(txt, ephemeral=False)
            else:
                await itx.response.send_message(txt, ephemeral=True)
        else:
            await itx.response.send_message(txt, ephemeral=not public)
    # endregion Tags


t: type[Tags] = Tags
tag_info_dict: dict[str, tuple[tuple[int, int, int], Callable, int]] = {
    # (sorted ABC and by hue; change hue) (Hue Sat Value (HSV), tag function, servers they're active in)
    "avoiding politics": ([0, 40, 100], t.send_avoidpolitics_info, EnabledServers.all_server_ids()),
    "avoiding venting": ([20, 40, 100], t.send_avoidventing_info, EnabledServers.all_server_ids()),
    "conversing effectively": ([40, 40, 100], t.send_conversing_effectively_info, EnabledServers.all_server_ids()),
    "customvcs": ([60, 40, 100], t.send_customvc_info, EnabledServers.all_server_ids()),
    "enabling embeds": ([80, 40, 100], t.send_enabling_embeds_info, EnabledServers.all_server_ids()),
    "image ban role / temporary embed ban": ([100, 40, 100],
                                             t.send_imagebanrole_info, EnabledServers.transplace_etc_ids()),
    "mature role and mature chat": ([120, 40, 100], t.send_maturerole_info, EnabledServers.transplace_etc_ids()),
    "minimodding or correcting staff": ([140, 40, 100], t.send_minimodding_info, EnabledServers.all_server_ids()),
    "please change topic": ([160, 40, 100], t.send_chat_topic_change_request, EnabledServers.all_server_ids()),
    "plural kit": ([180, 40, 100], t.send_pluralkit_info, EnabledServers.all_server_ids()),
    "report": ([0, 100, 100], t.send_report_info, EnabledServers.all_server_ids()),
    "selfies": ([200, 40, 100], t.send_selfies_info, EnabledServers.transplace_etc_ids()),
    "tone indicators": ([220, 40, 100], t.send_toneindicator_info, EnabledServers.all_server_ids()),
    "trigger warnings": ([240, 40, 100], t.send_triggerwarning_info, EnabledServers.all_server_ids()),
    "trusted role": ([260, 40, 100], t.send_trustedrole_info, EnabledServers.transplace_etc_ids()),
    "set pk server tag": ([280, 40, 100], t.send_pksettag_info, EnabledServers.all_server_ids()),
    "system discourse": ([300, 40, 100], t.send_syscourse_info, EnabledServers.all_server_ids()),
}
colours = {k: discord.Colour.from_hsv(v[0][0] / 360, v[0][1] / 100, v[0][2] / 100) for k, v in tag_info_dict.items()}
