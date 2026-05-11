import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
from utils import json_db, embeds, checks
import config

class BuilderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Starts working on an order")
    @app_commands.describe(order_id="The Order ID to start")
    async def start(self, interaction: discord.Interaction, order_id: int):
        if not checks.is_builder_or_mod(interaction.user):
            await interaction.response.send_message("❌ Only base builders can use this command.", ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o["orderId"] == order_id), None)

        if not order:
            await interaction.response.send_message(f"❌ Order #{order_id} not found.", ephemeral=True)
            return
        
        if order["status"] in ["completed", "removed"]:
            await interaction.response.send_message(f"❌ Order #{order_id} is already completed or removed.", ephemeral=True)
            return
            
        if order["status"] == "started":
            await interaction.response.send_message(f"⚠️ Order #{order_id} has already been claimed by {order['builderUsername']}. Use /complete [id] to finish it.", ephemeral=True)
            return
            
        order.update({
            "status": "started",
            "builderId": str(interaction.user.id),
            "builderUsername": interaction.user.display_name,
            "startedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        json_db.save("orders.json", orders)

        await asyncio.sleep(0.3)
        
        user = interaction.guild.get_member(int(order["userId"]))
        if user:
            try:
                await user.send(
                    content=f"<@{order['userId']}> your showcase base has been started!",
                    embed=embeds.order_started_embed(order, interaction.user)
                )
            except discord.Forbidden:
                await interaction.channel.send(f"⚠️ <@{order['userId']}> — I couldn't send you a DM! Please enable DMs from server members.")
        
        await interaction.response.send_message(
            f"✅ You've claimed order #{order_id} (TH{order['townhallLevel']} for {order['username']}). Use /complete [id] link:[url] (optional image attachment) when done.", 
            ephemeral=True
        )

    @app_commands.command(name="complete", description="Marks an order as complete")
    @app_commands.describe(order_id="Order ID", attachment="Image attachment", link="Showcase base link")
    async def complete(self, interaction: discord.Interaction, order_id: int, link: str, attachment: discord.Attachment = None):
        if not checks.is_builder_or_mod(interaction.user):
            await interaction.response.send_message("❌ Only base builders can use this command.", ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o["orderId"] == order_id), None)

        if not order:
            await interaction.response.send_message(f"❌ Order #{order_id} not found.", ephemeral=True)
            return
        
        if order["status"] in ["completed", "removed"]:
            await interaction.response.send_message(f"❌ Order #{order_id} is already completed or removed.", ephemeral=True)
            return
            
        if order["status"] == "pending":
            order["startedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            order["builderId"] = str(interaction.user.id)
            order["builderUsername"] = interaction.user.display_name
            
        order.update({
            "status": "completed",
            "completedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "baseLink": link,
            "imageUrl": attachment.url if attachment else None
        })
        
        counts = json_db.load("user_order_counts.json", {})
        counts[order["userId"]] = max(0, counts.get(order["userId"], 1) - 1)
        if counts[order["userId"]] == 0: del counts[order["userId"]]
        
        json_db.save("orders.json", orders)
        json_db.save("user_order_counts.json", counts)
        
        await interaction.response.send_message(f"✅ Order #{order_id} marked as complete!", ephemeral=True)
        
        customer_role = interaction.guild.get_role(config.CUSTOMER_ROLE_ID)
        user = interaction.guild.get_member(int(order["userId"]))
        if customer_role and user and customer_role not in user.roles:
            try:
                await user.add_roles(customer_role)
            except Exception as e:
                print(f"Failed to add role: {e}")
        
        ticket_channel = interaction.guild.get_channel(order["channelId"]) if order.get("channelId") else None
        completed_channel = interaction.guild.get_channel(config.COMPLETED_ORDERS_CHANNEL_ID)
        
        if ticket_channel:
            ticket_file = await attachment.to_file() if attachment else None
            await ticket_channel.send(
                content=f"<@{order['userId']}> your showcase base is on its way — check your DMs! 🏰",
                embed=embeds.completed_ticket_embed(order),
                file=ticket_file
            )
        
        await asyncio.sleep(3)
        
        await completed_channel.send(
            embed=embeds.completed_public_embed(order),
            allowed_mentions=discord.AllowedMentions.none()
        )
        
        await asyncio.sleep(0.5)
        
        user = interaction.guild.get_member(int(order["userId"]))
        if user:
            try:
                dm_file = await attachment.to_file() if attachment else None
                await user.send(
                    content=f"<@{order['userId']}>",
                    embed=embeds.completed_dm_embed(order),
                    file=dm_file
                )
                await user.send(f"🌟 Loved your base? We'd appreciate a review!\nType **/review** in <#{config.BOT_COMMANDS_CHANNEL_ID}> and use Order ID **#{order['orderId']}**")
            except discord.Forbidden:
                await completed_channel.send(f"⚠️ <@{order['userId']}> — I couldn't send you a DM! Please enable DMs from server members.")

    @app_commands.command(name="closeticket", description="Closes the current order ticket")
    @app_commands.describe(reason="Reason for closing the ticket")
    async def closeticket(self, interaction: discord.Interaction, reason: str = "Closed by staff"):
        if not checks.is_builder_or_mod(interaction.user):
            await interaction.response.send_message("❌ Only base builders can use this command.", ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o.get("channelId") == interaction.channel.id), None)

        if not order:
            await interaction.response.send_message("❌ This command can only be used inside an order ticket.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"✅ Closing ticket for order #{order['orderId']} in 5 seconds.\nReason: {reason}"
        )
        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Order #{order['orderId']} closed by {interaction.user}: {reason}")

    @app_commands.command(name="removeorder", description="Removes an order")
    @app_commands.describe(order_id="Order ID", reason="Reason for removal")
    async def removeorder(self, interaction: discord.Interaction, order_id: int, reason: str):
        if not checks.is_builder_or_mod(interaction.user):
            await interaction.response.send_message("❌ Only base builders can use this command.", ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o["orderId"] == order_id), None)

        if not order:
            await interaction.response.send_message(f"❌ Order #{order_id} not found.", ephemeral=True)
            return
        
        if order["status"] in ["completed", "removed"]:
            await interaction.response.send_message(f"❌ Order #{order_id} is already completed or removed.", ephemeral=True)
            return
            
        order["status"] = "removed"
        
        counts = json_db.load("user_order_counts.json", {})
        counts[order["userId"]] = max(0, counts.get(order["userId"], 1) - 1)
        if counts[order["userId"]] == 0: del counts[order["userId"]]
        
        json_db.save("orders.json", orders)
        json_db.save("user_order_counts.json", counts)
        
        await asyncio.sleep(0.3)
        
        user = interaction.guild.get_member(int(order["userId"]))
        if user:
            try:
                await user.send(
                    content=f"<@{order['userId']}>",
                    embed=embeds.removed_order_embed(order, reason, interaction.user)
                )
            except discord.Forbidden:
                pass
                
        await interaction.response.send_message(f"✅ Order #{order_id} removed.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BuilderCog(bot))
