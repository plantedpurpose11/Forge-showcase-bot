import discord
from discord import app_commands
from discord.ext import commands
import datetime
import zoneinfo

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="uptime", description="Shows how long the bot has been online since its last restart")
    async def uptime(self, interaction: discord.Interaction):
        if not self.bot.start_time:
            await interaction.response.send_message("❌ Uptime data not available yet.", ephemeral=True)
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        duration = now - self.bot.start_time

        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days} day{'' if days == 1 else 's'}")
        if hours > 0:
            parts.append(f"{hours} hour{'' if hours == 1 else 's'}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'' if minutes == 1 else 's'}")
        parts.append(f"{seconds} second{'' if seconds == 1 else 's'}")

        uptime_str = ", ".join(parts)
        est = zoneinfo.ZoneInfo("America/New_York")
        start_time_est = self.bot.start_time.astimezone(est)
        timestamp = start_time_est.strftime("%Y-%m-%d %I:%M:%S %p ET")

        embed = discord.Embed(
            title="⏱️ Bot Uptime",
            color=0x5865F2
        )
        embed.add_field(name="Online Since", value=f"`{timestamp}`", inline=False)
        embed.add_field(name="Duration", value=uptime_str, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Checks the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        # Measure time to send initial response
        start_time = datetime.datetime.now(datetime.timezone.utc)
        
        # WebSocket latency: time it takes for messages to reach Discord
        ws_latency = self.bot.latency * 1000
        
        end_time = datetime.datetime.now(datetime.timezone.utc)
        response_time = (end_time - start_time).total_seconds() * 1000

        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x2ECC71
        )
        embed.add_field(name="WebSocket Latency", value=f"`{ws_latency:.2f} ms`", inline=True)
        embed.add_field(name="Response Time", value=f"`{response_time:.2f} ms`", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Lists all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📚 Command List",
            description="Here are all available slash commands:",
            color=0x5865F2
        )
        
        # List known commands from this bot
        commands = [
            ("uptime", "Shows how long the bot has been online since its last restart"),
            ("ping", "Checks the bot's latency"),
            ("help", "Lists all available commands"),
            ("queue", "Shows the current showcase base order queue"),
            ("myorders", "Shows your order history"),
            ("review", "Leaves a review for a completed order"),
            ("panel", "Posts the order panel"),
            ("start", "Starts working on an order"),
            ("complete", "Marks an order as complete"),
            ("closeticket", "Closes the current order ticket"),
            ("removeorder", "Removes an order"),
            ("say", "Makes the bot repeat what you type (mod/admin only)"),
            ("changestatus", "Change the bot's status (bot owner only)"),
            ("changestatusmessage", "Change the bot's status message (bot owner only)"),
        ]
        
        for cmd_name, cmd_desc in commands:
            embed.add_field(
                name=f"/{cmd_name}",
                value=cmd_desc,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))