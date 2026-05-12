import discord
from discord import app_commands
from discord.ext import commands
from utils import checks

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Makes the bot repeat what you type")
    @app_commands.describe(message="The message for the bot to say", channel="The channel to send the message in (defaults to current channel)")
    async def say(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
        if not checks.is_mod_or_admin(interaction.user):
            await interaction.response.send_message("❌ Only moderators or administrators can use this command.", ephemeral=True)
            return

        target_channel = channel or interaction.channel
        
        await target_channel.send(f"💬 **{interaction.user.display_name} said:**\n{message}")
        
        await interaction.response.send_message(f"✅ Message sent to {target_channel.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))