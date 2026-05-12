import discord
import config

def is_builder_or_mod(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return bool(role_ids & {config.BASE_BUILDER_ROLE_ID, config.MODERATION_ROLE_ID})

def is_mod(member: discord.Member) -> bool:
    return config.MODERATION_ROLE_ID in {r.id for r in member.roles}

def is_admin(member: discord.Member) -> bool:
    return config.ADMIN_ROLE_ID in {r.id for r in member.roles}

def is_bot_owner(member: discord.Member) -> bool:
    return config.BOT_OWNER_ROLE_ID in {r.id for r in member.roles}

def is_bot_owner_by_id(member: discord.Member) -> bool:
    return member.id == config.BOT_OWNER_USER_ID

def is_bot_owner_check(member: discord.Member) -> bool:
    return is_bot_owner(member) or is_bot_owner_by_id(member)

def is_mod_or_admin(member: discord.Member) -> bool:
    return is_mod(member) or is_admin(member)
