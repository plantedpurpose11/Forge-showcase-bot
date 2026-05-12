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
        
        await target_channel.send(message)
        
        await interaction.response.send_message(f"✅ Message sent to {target_channel.mention}.", ephemeral=True)

    @app_commands.command(name="changestatus", description="Change the bot's status")
    @app_commands.describe(status="The status to set the bot to")
    @app_commands.choices(status=[
        app_commands.Choice(name="Online", value="online"),
        app_commands.Choice(name="Idle", value="idle"),
        app_commands.Choice(name="Do Not Disturb", value="dnd"),
        app_commands.Choice(name="Offline", value="invisible"),
    ])
    async def changestatus(self, interaction: discord.Interaction, status: str):
        if not checks.is_bot_owner(interaction.user):
            await interaction.response.send_message("❌ Only bot owners can use this command.", ephemeral=True)
            return

        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }

        new_status = status_map.get(status, discord.Status.online)
        
        # Get current activity to preserve it
        activity = self.bot.activity or discord.Activity(type=discord.ActivityType.playing, name="with my friends")
        
        await self.bot.change_presence(status=new_status, activity=activity)
        
        status_name = status.replace("invisible", "offline").replace("dnd", "Do Not Disturb")
        await interaction.response.send_message(f"✅ Bot status changed to **{status_name}**.", ephemeral=True)

    @app_commands.command(name="changestatusmessage", description="Change the bot's status message")
    @app_commands.describe(message="The status message to display", activity_type="The type of activity (playing, listening, watching, competing)")
    @app_commands.choices(activity_type=[
        app_commands.Choice(name="Playing", value="playing"),
        app_commands.Choice(name="Listening", value="listening"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Competing", value="competing"),
        app_commands.Choice(name="Streaming", value="streaming"),
    ])
    async def changestatusmessage(self, interaction: discord.Interaction, message: str, activity_type: str = "playing"):
        if not checks.is_bot_owner(interaction.user):
            await interaction.response.send_message("❌ Only bot owners can use this command.", ephemeral=True)
            return

        activity_map = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
            "streaming": discord.ActivityType.streaming,
        }

        activity = discord.Activity(type=activity_map.get(activity_type, discord.ActivityType.playing), name=message)
        
        # Get current status to preserve it
        status = self.bot.status or discord.Status.online
        
        await self.bot.change_presence(status=status, activity=activity)
        
        await interaction.response.send_message(f"✅ Status message changed to **{message}** ({activity_type}).", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))