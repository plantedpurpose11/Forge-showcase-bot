import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
from utils import json_db, embeds, checks, helpers
import config

async def save_ticket_transcript(interaction: discord.Interaction, order: dict, channel=None):
    """Save ticket transcript to the log channel if configured.
    
    Args:
        channel: The ticket channel to read history from. Defaults to interaction.channel.
    
    Returns a status string: 'ok', 'no_log_channel', or an error message.
    """
    guild_settings = json_db.load_guild_settings()
    ticket_log_channel_id = guild_settings.get("ticketLogChannelId")
    
    if not ticket_log_channel_id:
        return "no_log_channel"
    
    ticket_channel = channel or interaction.channel
    
    try:
        # Fetch messages from the channel
        messages = []
        async for message in ticket_channel.history(limit=200):
            messages.append(message)
        
        # Sort by oldest first
        messages.reverse()
        
        # Build the transcript
        transcript_lines = [f"Transcript for Order #{order['orderId']} - {order['username']}'s Showcase Base"]
        transcript_lines.append(f"Status: {order['status']}")
        transcript_lines.append(f"Townhall Level: {order['townhallLevel']}")
        transcript_lines.append(f"Preferences: {order.get('preferences', 'None')}")
        transcript_lines.append(f"Notes: {order.get('notes', 'None')}")
        transcript_lines.append(f"Builder: {order.get('builderUsername', 'Not assigned')}")
        if order.get("baseLink"):
            transcript_lines.append(f"Base Link: {order['baseLink']}")
        transcript_lines.append("")
        transcript_lines.append("--- Messages ---")
        
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
            author = msg.author.display_name
            
            # Build content from message text, embeds, and attachments
            parts = []
            if msg.content:
                parts.append(msg.content)
            for embed in msg.embeds:
                if embed.title:
                    parts.append(f"[Embed: {embed.title}]")
                elif embed.description:
                    desc_preview = embed.description[:100]
                    parts.append(f"[Embed: {desc_preview}]")
            for att in msg.attachments:
                parts.append(f"[Attachment: {att.filename}]")
            
            content = " ".join(parts) if parts else "[empty message]"
            transcript_lines.append(f"[{timestamp}] {author}: {content}")
        
        transcript = "\n".join(transcript_lines)
        
        # Send to log channel
        log_channel = interaction.guild.get_channel(ticket_log_channel_id)
        if not log_channel:
            return "log_channel_not_found"
        
        await helpers.safe_send_codeblock(log_channel, transcript)
        return "ok"
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return f"error: {e}"


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
            await ticket_channel.send(
                content=f"<@{order['userId']}> your showcase base is on its way — check your DMs! 🏰",
                embed=embeds.completed_ticket_embed(order)
            )
            # Save transcript before completing
            await save_ticket_transcript(interaction, order, channel=ticket_channel)
        
        await asyncio.sleep(3)
        
        await completed_channel.send(
            embed=embeds.completed_public_embed(order),
            allowed_mentions=discord.AllowedMentions.none()
        )
        
        await asyncio.sleep(0.5)
        
        user = interaction.guild.get_member(int(order["userId"]))
        if user:
            try:
                await user.send(
                    content=f"<@{order['userId']}>",
                    embed=embeds.completed_dm_embed(order)
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

        # Save transcript before closing
        order["status"] = "closed"
        result = await save_ticket_transcript(interaction, order)

        transcript_note = ""
        if result == "no_log_channel":
            transcript_note = "\n⚠️ No ticket log channel set — use `/ticketlogset` to enable transcripts."
        elif result == "log_channel_not_found":
            transcript_note = "\n⚠️ Ticket log channel not found — use `/ticketlogset` to reconfigure."
        elif result and result.startswith("error:"):
            transcript_note = f"\n⚠️ Failed to save transcript: {result}"
        elif result == "ok":
            transcript_note = "\n📋 Transcript saved."

        await interaction.response.send_message(
            f"✅ Closing ticket for order #{order['orderId']} in 5 seconds.\nReason: {reason}{transcript_note}"
        )
        
        user = interaction.guild.get_member(int(order["userId"]))
        if user:
            try:
                await user.send(f"Hey there <@{order['userId']}>, your ticket for a showcase base has been closed.\nReason: {reason}")
            except discord.Forbidden:
                pass
        
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

    @app_commands.command(name="addtoticket", description="Add a user to the current order ticket")
    @app_commands.describe(user="The user to add to the ticket")
    async def addtoticket(self, interaction: discord.Interaction, user: discord.Member):
        if not (checks.is_builder_or_mod(interaction.user) or checks.is_admin(interaction.user)):
            await interaction.response.send_message("❌ Only builders, moderators, or admins can use this command.", ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o.get("channelId") == interaction.channel.id), None)

        if not order:
            await interaction.response.send_message("❌ This command can only be used inside an order ticket.", ephemeral=True)
            return

        # Update permissions to allow the user to see the channel
        overwrites = interaction.channel.overwrites
        overwrites[user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        await interaction.channel.edit(name=interaction.channel.name, overwrites=overwrites)

        await interaction.response.send_message(f"✅ {user.mention} has been added to this ticket.", ephemeral=True)
        await interaction.channel.send(f"📥 {user.mention} has been added to this ticket by {interaction.user.mention}.")

    @app_commands.command(name="removefromticket", description="Remove a user from the current order ticket")
    @app_commands.describe(user="The user to remove from the ticket")
    async def removefromticket(self, interaction: discord.Interaction, user: discord.Member):
        if not (checks.is_builder_or_mod(interaction.user) or checks.is_admin(interaction.user)):
            await interaction.response.send_message("❌ Only builders, moderators, or admins can use this command.", ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o.get("channelId") == interaction.channel.id), None)

        if not order:
            await interaction.response.send_message("❌ This command can only be used inside an order ticket.", ephemeral=True)
            return

        # Don't allow removing the order owner
        if user.id == int(order["userId"]):
            await interaction.response.send_message("❌ You cannot remove the order owner from their ticket.", ephemeral=True)
            return

        # Update permissions to remove access
        overwrites = interaction.channel.overwrites
        if user in overwrites:
            del overwrites[user]
        await interaction.channel.edit(name=interaction.channel.name, overwrites=overwrites)

        await interaction.response.send_message(f"✅ {user.mention} has been removed from this ticket.", ephemeral=True)
        await interaction.channel.send(f"📤 {user.mention} has been removed from this ticket by {interaction.user.mention}.")

    @app_commands.command(name="forceclose", description="Force closes a ticket by order ID (for when user left)")
    @app_commands.describe(order_id="The Order ID to force close", reason="Reason for closing")
    async def forceclose(self, interaction: discord.Interaction, order_id: int, reason: str = "Force closed by staff"):
        if not checks.is_builder_or_mod(interaction.user):
            await interaction.response.send_message("❌ Only base builders can use this command.", ephemeral=True)
            return

        orders = json_db.load("orders.json", [])
        order = next((o for o in orders if o["orderId"] == order_id), None)

        if not order:
            await interaction.response.send_message(f"❌ Order #{order_id} not found.", ephemeral=True)
            return

        if order["status"] in ["completed", "removed", "closed"]:
            await interaction.response.send_message(f"❌ Order #{order_id} is already completed, removed, or closed.", ephemeral=True)
            return

        channel_id = order.get("channelId")
        if not channel_id:
            # No channel exists, just close the order
            order["status"] = "closed"
            json_db.save("orders.json", orders)
            await interaction.response.send_message(f"✅ Order #{order_id} marked as closed (no ticket channel existed).", ephemeral=True)
            return

        # Get the ticket channel if it still exists
        ticket_channel = interaction.guild.get_channel(channel_id)

        if ticket_channel:
            # Save transcript before closing
            await save_ticket_transcript(interaction, order, channel=ticket_channel)

            # Try to DM the user (will fail silently if user left)
            user = interaction.guild.get_member(int(order["userId"]))
            if user:
                try:
                    await user.send(f"Hey there <@{order['userId']}>, your ticket for a showcase base has been closed.\nReason: {reason}")
                except discord.Forbidden:
                    pass
            else:
                # User has left the server - mention in the close that they left
                await ticket_channel.send(f"⚠️ User {order['userId']} has left the server. Ticket force closed by {interaction.user.mention}.")

            order["status"] = "closed"
            json_db.save("orders.json", orders)

            await interaction.response.send_message(
                f"✅ Force closing ticket for order #{order_id}.\nReason: {reason}",
                ephemeral=True
            )

            await asyncio.sleep(1)

            await ticket_channel.delete(reason=f"Order #{order_id} force closed by {interaction.user}: {reason}")
        else:
            # Channel doesn't exist anymore, just close the order
            order["status"] = "closed"
            json_db.save("orders.json", orders)
            await interaction.response.send_message(f"✅ Order #{order_id} marked as closed (ticket channel no longer exists).", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BuilderCog(bot))
