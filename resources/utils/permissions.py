import discord


def is_verified(guild: discord.Guild, member: discord.Member | discord.User) -> bool:
    """
    Check if someone is verified.

    Parameters
    -----------
    guild: :class:`discord.Guild`
        A guild with roles to cycle through.
    member: :class:`discord.Member` | :class:`discord.User`
        A discord user with or without roles attribute.

    Returns
    --------
    :class:`bool`
        Whether the user is verified.
    """
    if guild is None:
        return False
    if type(member) == discord.User or not hasattr(member, "roles"):
        return False
    roles = [discord.utils.find(lambda r: r.name.lower() == 'verified', guild.roles)]
    user_role_ids = [role.id for role in member.roles]
    role_ids = [959748411844874240,   # Transplace: Verified
                1109907941454258257]  # Transonance: Verified
    # TODO: add role ids for enbyplace as backup as well
    return (len(set(roles).intersection(member.roles)) > 0 or
            is_staff(guild, member) or
            len(set(role_ids).intersection(user_role_ids)) > 0)

# def isVerifier(itx: discord.Interaction):
#     roles = [discord.utils.find(lambda r: r.name == 'Verifier', itx.guild.roles)]
#     return len(set(roles).intersection(itx.user.roles)) > 0 or is_admin(itx.guild, itx.user)


def is_staff(guild: discord.Guild, member: discord.Member | discord.User) -> bool:
    """
    Check if someone is staff.

    Parameters
    -----------
    guild: :class:`discord.Guild`
        A guild with roles to cycle through.
    member: :class:`discord.Member` | :class:`discord.User`
        A discord user with or without roles attribute.

    Returns
    --------
    :class:`bool`
        Whether the user has a staff role.
    """
    if guild is None:
        return False
    if isinstance(member, discord.User) or not hasattr(member, "roles"):
        return False
    roles = []
    for role_name_comparison in ["staff", "moderator", "trial mod", "sr. mod", "chat mod"]:
        for role in guild.roles:
            # case sensitive lol
            if role_name_comparison in role.name.lower():
                roles.append(role)
    # roles = [discord.utils.find(lambda r: 'staff'     in r.name.lower(), guild.roles),
    #          discord.utils.find(lambda r: 'moderator' in r.name.lower(), guild.roles),
    #          discord.utils.find(lambda r: 'trial mod' in r.name.lower(), guild.roles),
    #          discord.utils.find(lambda r: 'sr. mod'   in r.name.lower(), guild.roles),
    #          discord.utils.find(lambda r: 'chat mod'  in r.name.lower(), guild.roles)]
    user_role_ids = [role.id for role in member.roles]
    role_ids = [1069398630944997486, 981735650971775077,  #TransPlace: trial ; moderator
                1108771208931049544]  # Transonance: Staff
    return (len(set(roles).intersection(member.roles)) > 0 or
            is_admin(guild, member)
            or len(set(role_ids).intersection(user_role_ids)) > 0)


def is_admin(guild: discord.Guild, member: discord.Member | discord.User) -> bool:
    """
    Check if someone is an admin.

    Parameters
    -----------
    guild: :class:`discord.Guild`
        A guild with roles to cycle through.
    member: :class:`discord.Member` | :class:`discord.User`
        A discord user with or without roles attribute.

    Returns
    --------
    `bool`
        Whether the user has an admin role.
    """
    if guild is None:
        return False
    if isinstance(member, discord.User) or not hasattr(member, "roles"):
        return False
    roles = [discord.utils.find(lambda r: r.name.lower() == 'full admin', guild.roles),
             discord.utils.find(lambda r: 'head staff' in r.name.lower(), guild.roles),
             discord.utils.find(lambda r: 'admin' in r.name.lower(), guild.roles),
             # discord.utils.find(lambda r: r.name.lower() == 'admins', guild.roles),
             discord.utils.find(lambda r: r.name.lower() in 'owner', guild.roles)]
    user_role_ids = [role.id for role in member.roles]
    role_ids = [981735525784358962]  # TransPlace: Admin
    has_admin = any([role.permissions.administrator for role in member.roles])
    return (has_admin or
            len(set(roles).intersection(member.roles)) > 0
            or member.id == 262913789375021056
            or len(set(role_ids).intersection(user_role_ids)) > 0)
