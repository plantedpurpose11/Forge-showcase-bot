import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
from utils import json_db, embeds
import config

class ReviewModal(discord.ui.Modal, title='⭐ Leave a Review'):
    order_id = discord.ui.TextInput(
        label='Order ID',
        placeholder='Enter the order ID you want to review (check your DMs)',
        min_length=1,
        max_length=6,
        required=True
    )
    rating = discord.ui.TextInput(
        label='Star Rating (1 to 5)',
        placeholder='Enter a whole number: 1, 2, 3, 4 or 5',
        min_length=1,
        max_length=1,
        required=True
    )
    remarks = discord.ui.TextInput(
        label='Your Review',
        style=discord.TextStyle.paragraph,
        placeholder='Tell us what you thought about your showcase base! (optional)',
        required=False,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            oid = int(self.order_id.value)
            rating = int(self.rating.value)
            if not (1 <= rating <= 5): raise ValueError
        except ValueError:
            await interaction.response.send_message('❌ Invalid input. Please ensure order ID is a number and rating is 1-5.', ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o["orderId"] == oid), None)

        if not order or order["userId"] != str(interaction.user.id) or order["status"] != "completed" or order.get("reviewLeft"):
            await interaction.response.send_message('❌ That order ID is not valid, doesn\'t belong to you, or has already been reviewed.', ephemeral=True)
            return

        cooldowns = json_db.load("cooldowns.json", {})
        last_review = cooldowns.get(str(interaction.user.id), {}).get("lastReviewAt")
        if last_review:
            dt = datetime.datetime.fromisoformat(last_review)
            if (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() < 120:
                await interaction.response.send_message('❌ Please wait a moment before leaving another review.', ephemeral=True)
                return

        order["reviewLeft"] = True
        cooldowns[str(interaction.user.id)] = {"lastReviewAt": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        json_db.save("orders.json", orders)
        json_db.save("cooldowns.json", cooldowns)

        await asyncio.sleep(0.3)
        
        review_channel = interaction.guild.get_channel(config.REVIEW_CHANNEL_ID)
        review_msg = await review_channel.send(embed=embeds.review_embed(order, rating, self.remarks.value, interaction.user))
        await review_msg.add_reaction('❤️‍🔥')
        
        await interaction.response.send_message('✅ Thank you for your review! It means a lot to our builders. ⭐', ephemeral=True)

class ReviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="review", description="Leaves a review for a completed order")
    async def review(self, interaction: discord.Interaction):
        orders = json_db.load("orders.json", [])
        if not any(o for o in orders if o["userId"] == str(interaction.user.id) and o["status"] == "completed" and not o.get("reviewLeft")):
            await interaction.response.send_message("❌ You don't have any completed orders waiting for a review.", ephemeral=True)
            return
        
        await interaction.response.send_modal(ReviewModal())

async def setup(bot):
    await bot.add_cog(ReviewCog(bot))
