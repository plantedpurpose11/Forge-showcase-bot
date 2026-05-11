import discord
import config

def is_builder_or_mod(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return bool(role_ids & {config.BASE_BUILDER_ROLE_ID, config.MODERATION_ROLE_ID})

def is_mod(member: discord.Member) -> bool:
    return config.MODERATION_ROLE_ID in {r.id for r in member.roles}
