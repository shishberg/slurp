import chat
from common import logger, log_formatter

import discord
import dotenv
import os
import re

from langchain_core.messages import HumanMessage, AIMessage


log = logger(__name__)

dotenv.load_dotenv()  # take environment variables

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Constant for number of messages to use as context
CONTEXT_MESSAGE_COUNT = 10


@client.event
async def on_ready():
    log.info(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Handle DMs directly
    if isinstance(message.channel, discord.DMChannel):
        # Don't include any recent messages as context for DMs
        response = await chat.invoke([message.clean_content])
        await message.channel.send(response.answer)
        return

    # Handle messages in threads created by the bot
    if isinstance(message.channel, discord.Thread):
        # Check if this thread was created by our bot
        if message.channel.owner == client.user:
            # Get recent messages for context (excluding the current message)
            messages = []
            async for msg in message.channel.history(limit=CONTEXT_MESSAGE_COUNT + 1):
                if msg.type in (
                    discord.MessageType.default,
                    discord.MessageType.reply,
                ):
                    content = msg.clean_content
                elif msg.type == discord.MessageType.thread_starter_message:
                    content = message.channel.starter_message.clean_content
                else:
                    continue

                line = f"{msg.author.name}: {content}"
                if msg.author.id == client.user.id:
                    messages.append(AIMessage(line))
                else:
                    messages.append(HumanMessage(line))

            messages.reverse()  # Most recent last

            response = await chat.invoke(messages)
            await message.channel.send(response.answer)
            return

    # Handle mentions in channels
    if client.user in message.mentions:
        # Create a new thread and respond there
        # Create thread with temporary title
        thread = await message.create_thread(
            name="Slurp is thinking...",
            auto_archive_duration=60,
        )

        # Send placeholder message
        placeholder = await thread.send("Thinking...")
        response = await chat.invoke([message.clean_content])

        # Update thread title and message content
        await thread.edit(name=response.title)
        await placeholder.edit(content=response.answer)
        return


if __name__ == "__main__":
    client.run(os.getenv("DISCORD_TOKEN"), log_formatter=log_formatter)
