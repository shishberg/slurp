import chat
from common import logger, log_formatter

import discord
import dotenv
import os

from langchain_core.messages import HumanMessage, AIMessage


log = logger(__name__)

dotenv.load_dotenv()  # take environment variables

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Constant for number of messages to use as context
CONTEXT_MESSAGE_COUNT = 20


@client.event
async def on_ready():
    log.info(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    thread = None

    # Handle DMs and mentions
    if (
        isinstance(message.channel, discord.DMChannel)
        or client.user in message.mentions
    ):
        # Don't include any recent messages as context for DMs
        messages = [HumanMessage(message.clean_content)]
        # Create a new thread and respond there
        # Create thread with temporary title
        thread = await message.create_thread(
            name="Slurp is thinking...",
            auto_archive_duration=60,
        )

    # Handle messages in threads created by the bot
    elif isinstance(message.channel, discord.Thread):
        # Check if this thread was created by our bot
        if message.channel.owner != client.user:
            return

        thread = message.channel

        # Get recent messages for context (excluding the current message)
        messages = []
        async for msg in thread.history(limit=CONTEXT_MESSAGE_COUNT + 1):
            if msg.type in (
                discord.MessageType.default,
                discord.MessageType.reply,
            ):
                pass
            elif msg.type == discord.MessageType.thread_starter_message:
                log.info(f"starter message: {msg}")
                msg = thread.starter_message
                if msg is None:
                    msg = await thread.parent.fetch_message(thread.id)
            else:
                continue

            line = f"{msg.author.name}: {msg.clean_content}"
            if msg.author.id == client.user.id:
                messages.append(AIMessage(line))
            else:
                messages.append(HumanMessage(line))

        messages.reverse()  # Most recent last

    else:
        log.info(f"Ignoring message: {message}")
        return

    async for response in chat.invoke(messages):
        if response.title:
            await thread.edit(name=response.title)
        if response.answer:
            await thread.send(response.answer)


if __name__ == "__main__":
    client.run(os.getenv("DISCORD_TOKEN"), log_formatter=log_formatter)
