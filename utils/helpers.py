import discord

DISCORD_MAX_LENGTH = 2000


async def safe_send(channel: discord.abc.Messageable, content: str, **kwargs):
    """Send a message, automatically splitting into chunks if it exceeds Discord's 2000 char limit.

    Args:
        channel: Any Discord messageable (TextChannel, DMChannel, etc.)
        content: The message content to send.
        **kwargs: Extra keyword arguments passed to channel.send() (e.g. allowed_mentions).

    Returns:
        The last discord.Message sent.
    """
    if len(content) <= DISCORD_MAX_LENGTH:
        return await channel.send(content, **kwargs)

    chunks = [content[i:i + DISCORD_MAX_LENGTH] for i in range(0, len(content), DISCORD_MAX_LENGTH)]
    last = None
    for chunk in chunks:
        last = await channel.send(chunk, **kwargs)
    return last


async def safe_send_codeblock(channel: discord.abc.Messageable, text: str, **kwargs):
    """Send text wrapped in a code block, splitting into safe chunks if needed.

    Each chunk is wrapped in triple backticks. The chunk size accounts for
    the 8-character overhead of the ```\\n...\\n``` wrapper.

    Args:
        channel: Any Discord messageable.
        text: The raw text to wrap in code blocks.
        **kwargs: Extra keyword arguments passed to channel.send().

    Returns:
        The last discord.Message sent.
    """
    max_text = DISCORD_MAX_LENGTH - 8  # account for ```\n...\n```
    if len(text) <= max_text:
        return await channel.send(f"```\n{text}\n```", **kwargs)

    chunks = [text[i:i + max_text] for i in range(0, len(text), max_text)]
    last = None
    for chunk in chunks:
        last = await channel.send(f"```\n{chunk}\n```", **kwargs)
    return last
