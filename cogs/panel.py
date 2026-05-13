import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
from utils import json_db, embeds, checks
import config

class OrderModal(discord.ui.Modal, title='📋 Order a Base at Jack\'s Showbase Forge'):
    th_level = discord.ui.TextInput(
        label='Townhall Level',
        placeholder='Enter your TH level — must be 14, 15, 16, 17, or 18',
        min_length=2,
        max_length=2,
        required=True
    )
    preferences = discord.ui.TextInput(
        label='Do you have anything in mind?',
        style=discord.TextStyle.paragraph,
        placeholder='Add a crown, good font, etc.',
        required=False,
        max_length=300
    )
    notes = discord.ui.TextInput(
        label='Additional notes',
        style=discord.TextStyle.paragraph,
        placeholder='Anything else you want us to know',
        required=False,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        th = self.th_level.value
        try:
            th_int = int(th)
            if th_int not in config.SUPPORTED_TH_LEVELS:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                '❌ Invalid Townhall level. Please enter a number: 14, 15, 16, 17, or 18.', ephemeral=True
            )
            return

        orders = json_db.load("orders.json", [])
        order_id = max([o["orderId"] for o in orders], default=0) + 1
        
        counts = json_db.load("user_order_counts.json", {})
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        order = {
            "orderId": order_id,
            "userId": str(interaction.user.id),
            "username": interaction.user.display_name,
            "townhallLevel": th_int,
            "preferences": self.preferences.value,
            "notes": self.notes.value,
            "status": "pending",
            "builderId": None,
            "builderUsername": None,
            "queuePosition": len([o for o in orders if o["status"] in ["pending", "started"]]) + 1,
            "createdAt": now.isoformat(),
            "startedAt": None,
            "completedAt": None,
            "baseLink": None,
            "imageUrl": None,
            "reviewLeft": False,
            "confirmationMessageId": None,
            "channelId": None
        }
        
        orders.append(order)
        json_db.save("orders.json", orders)
        
        counts[str(interaction.user.id)] = counts.get(str(interaction.user.id), 0) + 1
        json_db.save("user_order_counts.json", counts)
        
        await interaction.response.defer(ephemeral=True)
        
        # Verify the category exists
        try:
            category = await interaction.guild.fetch_channel(config.ORDER_TICKET_CATEGORY_ID)
            if category.type != discord.ChannelType.category:
                await interaction.followup.send("❌ ORDER_TICKET_CATEGORY_ID is not a valid category channel.", ephemeral=True)
                return
        except discord.NotFound:
            await interaction.followup.send("❌ Order ticket category not found. Please check ORDER_TICKET_CATEGORY_ID in config.", ephemeral=True)
            return
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.get_role(config.BASE_BUILDER_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.get_role(config.MODERATION_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            name=f"order-{order_id}",
            category=config.ORDER_TICKET_CATEGORY_ID,
            overwrites=overwrites,
            topic=f"Order #{order_id} for {interaction.user.display_name}"
        )
        
        order["channelId"] = channel.id
        json_db.save("orders.json", orders)
        
        await channel.send(
            content=f"<@{interaction.user.id}> <@&{config.BASE_BUILDER_ROLE_ID}>",
            embed=embeds.builder_notification_embed(order)
        )
        
        await interaction.followup.send(
            f"✅ Order #{order_id} placed! Discuss it in <#{channel.id}>.", 
            ephemeral=True
        )

class OrderPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='📋 Order a Showcase Base', style=discord.ButtonStyle.green, custom_id='order_showcase_base_btn')
    async def order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        orders = json_db.load("orders.json", [])
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        daily_count = len([o for o in orders if datetime.datetime.fromisoformat(o["createdAt"]).strftime("%Y-%m-%d") == today])
        if daily_count >= config.DAILY_ORDER_LIMIT:
            await interaction.response.send_message('❌ We\'ve reached our daily limit of 10 orders today. Please come back tomorrow!', ephemeral=True)
            return

        counts = json_db.load("user_order_counts.json", {})
        if counts.get(str(interaction.user.id), 0) >= config.MAX_ACTIVE_ORDERS_PER_USER:
            await interaction.response.send_message(f'❌ You already have {config.MAX_ACTIVE_ORDERS_PER_USER} active orders in progress. Please wait for one to be completed before ordering again.', ephemeral=True)
            return

        await interaction.response.send_modal(OrderModal())

class PanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="Posts the order panel")
    @app_commands.checks.has_role(config.MODERATION_ROLE_ID)
    async def panel(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=embeds.panel_embed(), view=OrderPanelView())

async def setup(bot):
    await bot.add_cog(PanelCog(bot))
