import discord
from discord import app_commands
from discord.ext import commands
from utils import checks, json_db, helpers
import json
import asyncio
import datetime

# Default activity to use when none exists
DEFAULT_ACTIVITY = discord.Activity(type=discord.ActivityType.playing, name="🏰 Taking showcase base orders")

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_status = discord.Status.online
        self._last_activity = DEFAULT_ACTIVITY
    
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

        self._last_status = status_map.get(status, discord.Status.online)
        
        # Use saved activity, not current bot activity
        activity = self.bot.activity or self._last_activity
        self._last_activity = activity
        
        await self.bot.change_presence(status=self._last_status, activity=activity)
        
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

        self._last_activity = discord.Activity(type=activity_map.get(activity_type, discord.ActivityType.playing), name=message)
        
        # Use saved status, not current bot status
        status = self.bot.status or self._last_status
        self._last_status = status
        
        await self.bot.change_presence(status=status, activity=self._last_activity)
        
        await interaction.response.send_message(f"✅ Status message changed to **{message}** ({activity_type}).", ephemeral=True)

    @app_commands.command(name="ticketlogset", description="Set the channel where ticket transcripts will be logged")
    @app_commands.describe(channel="The channel to log ticket transcripts to")
    async def ticketlogset(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not checks.is_mod_or_admin(interaction.user):
            await interaction.response.send_message("❌ Only moderators or administrators can use this command.", ephemeral=True)
            return

        guild_settings = json_db.load_guild_settings()
        guild_settings["ticketLogChannelId"] = channel.id
        json_db.save_guild_settings(guild_settings)

        await interaction.response.send_message(f"✅ Ticket transcripts will now be logged to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="ticketlog", description="Logs the current ticket transcript to the log channel")
    async def ticketlog(self, interaction: discord.Interaction):
        if not checks.is_builder_or_mod(interaction.user):
            await interaction.response.send_message("❌ Only base builders or moderators can use this command.", ephemeral=True)
            return

        # Load ticket log channel from settings
        guild_settings = json_db.load_guild_settings()
        ticket_log_channel_id = guild_settings.get("ticketLogChannelId")

        if not ticket_log_channel_id:
            await interaction.response.send_message("❌ No ticket log channel set. Use /ticketlogset to configure one.", ephemeral=True)
            return

        # Find the order for this channel
        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o.get("channelId") == interaction.channel.id), None)

        if not order:
            await interaction.response.send_message("❌ This command can only be used inside an order ticket.", ephemeral=True)
            return

        # Fetch messages from the channel
        ticket_channel = interaction.channel
        messages = []
        async for message in ticket_channel.history(limit=100):
            messages.append(message)

        # Sort by oldest first
        messages.reverse()

        # Build the transcript
        transcript_lines = [f"## Transcript for Order #{order['orderId']} - {order['username']}'s Showcase Base"]
        transcript_lines.append(f"**Status:** {order['status']}")
        transcript_lines.append(f"**Townhall Level:** {order['townhallLevel']}")
        transcript_lines.append(f"**Preferences:** {order.get('preferences', 'None')}")
        transcript_lines.append(f"**Notes:** {order.get('notes', 'None')}")
        transcript_lines.append(f"**Builder:** {order.get('builderUsername', 'Not assigned')}")
        transcript_lines.append("")
        transcript_lines.append("### Messages:")

        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
            author = msg.author.display_name
            content = msg.content or "[embed/attachment]"
            transcript_lines.append(f"**{timestamp}** - {author}: {content}")

        transcript = "\n".join(transcript_lines)

        # Send to log channel
        log_channel = interaction.guild.get_channel(ticket_log_channel_id)
        if log_channel:
            await helpers.safe_send_codeblock(log_channel, transcript)

            await interaction.response.send_message(f"✅ Transcript logged to {log_channel.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Could not find the ticket log channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))