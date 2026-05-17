import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils import json_db, checks

class StickyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._locks = {}

    def _get_lock(self, channel_id: int) -> asyncio.Lock:
        if channel_id not in self._locks:
            self._locks[channel_id] = asyncio.Lock()
        return self._locks[channel_id]

    @app_commands.command(name="stickymessage", description="Pin a message to the bottom of a channel (admin only)")
    @app_commands.describe(message="The message to keep pinned at the bottom of this channel")
    async def stickymessage(self, interaction: discord.Interaction, message: str):
        if not checks.is_admin(interaction.user) and not checks.is_bot_owner(interaction.user):
            await interaction.response.send_message("❌ You need admin permissions to use this command.", ephemeral=True)
            return

        stickies = json_db.load("stickies.json", {})
        channel_id = str(interaction.channel_id)

        # Delete old sticky message if one exists
        old = stickies.get(channel_id)
        if old:
            try:
                old_msg = await interaction.channel.fetch_message(old["messageId"])
                await old_msg.delete()
            except (discord.NotFound, discord.HTTPException):
                pass

        # Send the new sticky
        embed = discord.Embed(
            description=message,
            color=0xffa201
        )
        embed.set_footer(text="📌 Sticky Message")
        sticky_msg = await interaction.channel.send(embed=embed)

        stickies[channel_id] = {
            "messageId": sticky_msg.id,
            "content": message
        }
        json_db.save("stickies.json", stickies)

        await interaction.response.send_message("📌 Sticky message set! It will stay at the bottom of this channel.", ephemeral=True)

    @app_commands.command(name="removesticky", description="Remove the sticky message from this channel (admin only)")
    async def removesticky(self, interaction: discord.Interaction):
        if not checks.is_admin(interaction.user) and not checks.is_bot_owner(interaction.user):
            await interaction.response.send_message("❌ You need admin permissions to use this command.", ephemeral=True)
            return

        stickies = json_db.load("stickies.json", {})
        channel_id = str(interaction.channel_id)

        old = stickies.get(channel_id)
        if not old:
            await interaction.response.send_message("❌ There is no sticky message in this channel.", ephemeral=True)
            return

        try:
            old_msg = await interaction.channel.fetch_message(old["messageId"])
            await old_msg.delete()
        except (discord.NotFound, discord.HTTPException):
            pass

        del stickies[channel_id]
        json_db.save("stickies.json", stickies)

        await interaction.response.send_message("✅ Sticky message removed.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        stickies = json_db.load("stickies.json", {})
        channel_id = str(message.channel.id)

        if channel_id not in stickies:
            return

        lock = self._get_lock(message.channel.id)
        async with lock:
            sticky = stickies.get(channel_id)
            if not sticky:
                return

            # Delete the old sticky message
            try:
                old_msg = await message.channel.fetch_message(sticky["messageId"])
                await old_msg.delete()
            except (discord.NotFound, discord.HTTPException):
                pass

            # Re-send it so it's at the bottom
            embed = discord.Embed(
                description=sticky["content"],
                color=0xffa201
            )
            embed.set_footer(text="📌 Sticky Message")
            new_msg = await message.channel.send(embed=embed)

            # Update stored message ID
            sticky["messageId"] = new_msg.id
            json_db.save("stickies.json", stickies)


async def setup(bot):
    await bot.add_cog(StickyCog(bot))
