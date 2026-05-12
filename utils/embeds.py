import discord
import config
from datetime import datetime

def _get_unix(iso_str: str) -> int:
    """Helper to convert ISO string to Unix timestamp."""
    if not iso_str: return 0
    return int(datetime.fromisoformat(iso_str).timestamp())

def panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏰 Cheap Showcase Bases",
        color=0x5516a5,
        description=(
            "Welcome! We build custom Clash of Clans **showcase bases** for you — $4 a base.\n\n"
            "📋 **How it works:**\n"
            "1️⃣ Click the button below to place your order\n"
            "2️⃣ Fill in your Townhall level and any preferences\n"
            "3️⃣ Our builders will get to work on your showcase base\n"
            "4️⃣ You'll receive your base link via DM when it's done!\n\n"
            "⚠️ **Please read before ordering:**\n"
            "• We only accept **10 orders per day**\n"
            "• You can have a maximum of **5 active orders** at once\n"
            "• Supported Townhall levels: **TH14, TH15, TH16, TH17, TH18**\n"
            "• This is a **showcase base** service only"
        )
    )
    embed.set_footer(text="The Showbase Forge")
    return embed

def order_received_embed(order: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"✅ Showcase Base Order Received! — #{order['orderId']}",
        color=0x00ff88,
        description=f"Your order has been received! Our builders have been notified."
    )
    embed.add_field(name="Order ID", value=f"#{order['orderId']}", inline=True)
    embed.add_field(name="Townhall Level", value=f"TH{order['townhallLevel']}", inline=True)
    embed.add_field(name="Queue Position", value=f"#{order['queuePosition']}", inline=True)
    embed.add_field(name="Status", value="⏳ Pending", inline=True)
    embed.add_field(name="Preferences", value=order['preferences'] or "None", inline=False)
    embed.add_field(name="Notes", value=order['notes'] or "None", inline=False)
    embed.set_footer(text="The Showbase Forge")
    return embed

def builder_notification_embed(order: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"📋 New Showcase Base Order — #{order['orderId']}",
        color=0x5865F2,
    )
    embed.add_field(name="Customer", value=f"<@{order['userId']}>", inline=True)
    embed.add_field(name="Townhall Level", value=f"TH{order['townhallLevel']}", inline=True)
    embed.add_field(name="Order ID", value=f"#{order['orderId']}", inline=True)
    embed.add_field(name="Queue Position", value=f"#{order['queuePosition']}", inline=True)
    embed.add_field(name="Preferences", value=order['preferences'] or "None", inline=False)
    embed.add_field(name="Notes", value=order['notes'] or "None", inline=False)
    embed.add_field(name="Ordered at", value=f"<t:{_get_unix(order['createdAt'])}:F>", inline=False)
    embed.set_footer(text="The Showbase Forge")
    return embed

def order_started_embed(order: dict, builder: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=f"🔨 Order #{order['orderId']} Has Been Started!",
        color=0xff9900,
        description="Your showcase base is now being worked on! You'll receive it via DM as soon as it's complete."
    )
    embed.add_field(name="Customer", value=f"<@{order['userId']}>", inline=True)
    embed.add_field(name="Builder", value=builder.mention, inline=True)
    embed.add_field(name="Townhall Level", value=f"TH{order['townhallLevel']}", inline=True)
    embed.add_field(name="Order ID", value=f"#{order['orderId']}", inline=True)
    embed.add_field(name="Started at", value=f"<t:{_get_unix(order['startedAt'])}:F>", inline=False)
    embed.set_footer(text="The Showbase Forge")
    return embed

def completed_ticket_embed(order: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"✅ Showcase Base Completed — Order #{order['orderId']}",
        color=0x5516a5,
        description="Your showcase base has been completed and sent via DM!"
    )
    embed.add_field(name="For", value=f"<@{order['userId']}>", inline=True)
    embed.add_field(name="Order ID", value=f"#{order['orderId']}", inline=True)
    embed.add_field(name="Townhall Level", value=f"TH{order['townhallLevel']}", inline=True)
    embed.add_field(name="Built by", value=order['builderUsername'], inline=True)
    embed.add_field(name="Completed", value=f"<t:{_get_unix(order['completedAt'])}:F>", inline=False)
    if order.get('imageUrl'):
        embed.set_image(url=order['imageUrl'])
    embed.set_footer(text="The Showbase Forge")
    return embed

def completed_public_embed(order: dict) -> discord.Embed:
    embed = discord.Embed(
        title="✅ Showcase Base Completed",
        color=0x5516a5
    )
    embed.add_field(name="Base for:", value=order["username"], inline=True)
    embed.add_field(name="Base by:", value=order["builderUsername"], inline=True)
    if order.get('imageUrl'):
        embed.set_image(url=order['imageUrl'])
    embed.set_footer(text="The Showbase Forge")
    return embed

def completed_dm_embed(order: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🏰 Your Showcase Base Is Ready!",
        color=0x5516a5,
        description="Thank you for your patience! Your showcase base has been completed."
    )
    embed.add_field(name="Order ID", value=f"#{order['orderId']}", inline=True)
    embed.add_field(name="Townhall Level", value=f"TH{order['townhallLevel']}", inline=True)
    embed.add_field(name="Built by", value=order['builderUsername'], inline=True)
    embed.add_field(name="Base Link", value=order.get('baseLink', 'N/A'), inline=False)
    if order.get('imageUrl'):
        embed.set_image(url=order['imageUrl'])
    embed.set_footer(text="The Showbase Forge")
    return embed

def removed_order_embed(order: dict, reason: str, removed_by: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=f"❌ Order Removed — #{order['orderId']}",
        color=0xfc0303,
        description="Unfortunately your order has been removed."
    )
    embed.add_field(name="Order ID", value=f"#{order['orderId']}", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Removed by", value=removed_by.mention, inline=True)
    embed.set_footer(text="The Showbase Forge")
    return embed

def queue_embed(active_orders: list) -> discord.Embed:
    embed = discord.Embed(
        title=f"📋 Showcase Base Queue — {len(active_orders)} order(s) waiting",
        color=0x5865F2,
        description="Here's the current order queue. Orders are worked on from top to bottom."
    )
    for i, order in enumerate(active_orders, 1):
        status = "⏳ Pending"
        if order['status'] == 'started':
            status = f"🔨 In Progress — builder: {order['builderUsername']}"
        
        embed.add_field(
            name=f"#{i} — Order #{order['orderId']} — TH{order['townhallLevel']}",
            value=(
                f"👤 Customer: <@{order['userId']}>\n"
                f"📌 Status: {status}\n"
                f"🕐 Waiting since: <t:{_get_unix(order['createdAt'])}:R>"
            ),
            inline=False
        )
    embed.set_footer(text="The Showbase Forge")
    return embed

def myorders_embed(user_orders: list, user: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=f"📋 Your Order History — {user.display_name}",
        color=0x5865F2,
        description="All orders you've ever placed with us."
    )
    for order in user_orders[:20]:
        status_emoji = {"pending": "⏳", "started": "🔨", "completed": "✅", "removed": "❌"}[order['status']]
        
        embed.add_field(
            name=f"Order #{order['orderId']} — TH{order['townhallLevel']} {status_emoji}",
            value=f"📌 Status: {order['status'].capitalize()}",
            inline=False
        )
    embed.set_footer(text="Jack's Showbase Forge")
    return embed

def review_embed(order: dict, rating: int, remarks: str, reviewer: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=f"⭐ Review from {reviewer.display_name}",
        color=0x5516a5
    )
    embed.set_thumbnail(url=reviewer.avatar.url if reviewer.avatar else None)
    embed.add_field(name="Rating", value="⭐" * rating, inline=True)
    embed.add_field(name="Order", value=f"#{order['orderId']} — TH{order['townhallLevel']}", inline=True)
    embed.add_field(name="Built by", value=order['builderUsername'], inline=True)
    embed.add_field(name="Review", value=remarks or "No review provided.", inline=False)
    embed.set_footer(text="The Showbase Forge")
    return embed

def stale_order_embed(order: dict) -> discord.Embed:
    embed = discord.Embed(
        title="⚠️ Stale Order Alert",
        color=0xff6600,
        description="The following order has been waiting for 24+ hours without being claimed:"
    )
    embed.add_field(name="Order ID", value=f"#{order['orderId']}", inline=True)
    embed.add_field(name="Customer", value=f"<@{order['userId']}>", inline=True)
    embed.add_field(name="Townhall Level", value=f"TH{order['townhallLevel']}", inline=True)
    embed.add_field(name="Waiting since", value=f"<t:{_get_unix(order['createdAt'])}:R>", inline=False)
    embed.set_footer(text="The Showbase Forge")
    return embed
