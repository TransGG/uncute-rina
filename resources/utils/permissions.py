import discord

def is_verified(itx: discord.Interaction) -> bool:
    """
    Check if someone is verified

    ### Parameters:
    itx: :class:`discord.Interaction`
        interaction with itx.guild.roles and itx.user.roles
    
    ### Returns
    `bool` is_verified
    """
    if itx.guild is None:
        return False
    roles = [discord.utils.find(lambda r: r.name.lower() == 'verified', itx.guild.roles)]
    user_role_ids = [role.id for role in itx.user.roles]
    role_ids = [959748411844874240,  # Transplace: Verified
                1109907941454258257] # Transonance: Verified
    return len(set(roles).intersection(itx.user.roles)) > 0 or is_staff(itx) or len(set(role_ids).intersection(user_role_ids)) > 0

# def isVerifier(itx: discord.Interaction):
#     roles = [discord.utils.find(lambda r: r.name == 'Verifier', itx.guild.roles)]
#     return len(set(roles).intersection(itx.user.roles)) > 0 or is_admin(itx)

def is_staff(itx: discord.Interaction) -> bool:
    """
    Check if someone is staff

    ### Parameters:
    itx: :class:`discord.Interaction`
        interaction with itx.guild.roles and itx.user.roles
    
    ### Returns
    `bool` is_staff
    """
    if itx.guild is None:
        return False
    # case sensitive lol
    roles = [discord.utils.find(lambda r: 'staff'     in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'moderator' in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'trial mod' in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'sr. mod'   in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'chat mod'  in r.name.lower(), itx.guild.roles)]
    user_role_ids = [role.id for role in itx.user.roles]
    role_ids = [1069398630944997486,981735650971775077, #TransPlace: trial ; moderator
                1108771208931049544] # Transonance: Staff
    return len(set(roles).intersection(itx.user.roles)) > 0 or is_admin(itx) or len(set(role_ids).intersection(user_role_ids)) > 0

def is_admin(itx: discord.Interaction) -> bool:
    """
    Check if someone is an admin

    ### Parameters:
    itx: :class:`discord.Interaction`
        interaction with itx.guild.roles and itx.user
    
    ### Returns
    `bool` is_admin
    """
    if itx.guild is None:
        return False
    roles = [discord.utils.find(lambda r: r.name.lower() == 'full admin', itx.guild.roles),
             discord.utils.find(lambda r: 'head staff' in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: r.name.lower() == 'admins'    , itx.guild.roles),
             discord.utils.find(lambda r: r.name.lower() == 'admin'     , itx.guild.roles),
             discord.utils.find(lambda r: r.name.lower() == 'owner'     , itx.guild.roles)] 
    user_role_ids = [role.id for role in itx.user.roles]
    role_ids = [981735525784358962]  # TransPlace: Admin
    has_admin = itx.permissions.administrator
    return has_admin or len(set(roles).intersection(itx.user.roles)) > 0 or itx.user.id == 262913789375021056 or len(set(role_ids).intersection(user_role_ids)) > 0
