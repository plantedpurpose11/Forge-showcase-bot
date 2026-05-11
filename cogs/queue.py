import discord
from discord import app_commands
from discord.ext import commands
from utils import json_db, embeds
import config

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="queue", description="Shows the current showcase base order queue")
    async def queue(self, interaction: discord.Interaction):
        orders = json_db.load("orders.json", [])
        active_orders = sorted(
            [o for o in orders if o["status"] in ["pending", "started"]],
            key=lambda x: x["createdAt"]
        )

        if not active_orders:
            embed = discord.Embed(
                title="📋 Showcase Base Queue",
                color=0x5865F2,
                description="✅ The queue is currently empty! Click the order button to be first in line."
            )
            await interaction.response.send_message(embed=embed)
            return

        for i in range(0, len(active_orders), 15):
            chunk = active_orders[i:i+15]
            await interaction.response.send_message(embed=embeds.queue_embed(chunk))

    @app_commands.command(name="myorders", description="Shows your order history")
    async def myorders(self, interaction: discord.Interaction):
        orders = json_db.load("orders.json", [])
        user_orders = sorted(
            [o for o in orders if o["userId"] == str(interaction.user.id)],
            key=lambda x: x["createdAt"],
            reverse=True
        )

        if not user_orders:
            await interaction.response.send_message("You haven't placed any orders yet.", ephemeral=True)
            return

        await interaction.response.send_message(embed=embeds.myorders_embed(user_orders, interaction.user), ephemeral=True)

async def setup(bot):
    await bot.add_cog(QueueCog(bot))
