import discord
import logging
from discord.ext import commands, tasks
import asyncio
import datetime
from utils import json_db, embeds
import config

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.start_time = None  # Track bot uptime

@tasks.loop(hours=1)
async def stale_order_check():
    try:
        orders = json_db.load("orders.json", [])
        now = datetime.datetime.now(datetime.timezone.utc)
        channel = bot.get_channel(config.BUILDER_NOTIFICATION_CHANNEL_ID)
        if not channel: return

        for order in orders:
            if order["status"] == "pending":
                created_at = datetime.datetime.fromisoformat(order["createdAt"])
                if (now - created_at).total_seconds() > 86400:
                    last_alert = order.get("alertedAt")
                    if not last_alert or (now - datetime.datetime.fromisoformat(last_alert)).total_seconds() > 82800:
                        await channel.send(
                            content=f"<@&{config.BASE_BUILDER_ROLE_ID}>",
                            embed=embeds.stale_order_embed(order)
                        )
                        order["alertedAt"] = now.isoformat()
                        json_db.save("orders.json", orders)
    except Exception as e:
        logging.error(f"Error in stale_order_check: {e}")

@bot.event
async def on_ready():
    bot.start_time = datetime.datetime.now(datetime.timezone.utc)
    print(f"✅ Bot logged in as {bot.user} ({bot.user.id})")

    from cogs.panel import OrderPanelView
    bot.add_view(OrderPanelView())

    if config.GUILD_ID:
        guild = discord.Object(id=config.GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"✅ Synced commands to guild {config.GUILD_ID}")
    else:
        await bot.tree.sync()
        print("✅ Synced commands globally")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🏰 Taking showcase base orders"
        )
    )
    
    if not stale_order_check.is_running():
        stale_order_check.start()

async def load_extensions():
    try:
        await bot.load_extension("cogs.panel")
    except Exception as e:
        logging.error(f"Failed to load cogs.panel: {e}")
    try:
        await bot.load_extension("cogs.queue")
    except Exception as e:
        logging.error(f"Failed to load cogs.queue: {e}")
    try:
        await bot.load_extension("cogs.builder")
    except Exception as e:
        logging.error(f"Failed to load cogs.builder: {e}")
    try:
        await bot.load_extension("cogs.review")
    except Exception as e:
        logging.error(f"Failed to load cogs.review: {e}")
    try:
        await bot.load_extension("cogs.utilities")
    except Exception as e:
        logging.error(f"Failed to load cogs.utilities: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(config.TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
