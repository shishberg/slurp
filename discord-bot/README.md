# Discord Bot

This is a Discord bot that can answer questions about school communications.

## How it Works

The bot uses a large language model (Anthropic Claude on Amazon Bedrock) and an Amazon Knowledge Base to answer questions. It is designed to be aware of the user's children and their classes to provide personalized and relevant information.

The bot can be interacted with in the following ways:

*   **Direct Messages:** The bot will respond to DMs.
*   **Mentions:** Mentioning the bot in a channel will create a new thread for the conversation.
*   **Threads:** The bot will continue conversations within threads it has created.

## Setup

1.  Create a virtual environment: `python -m venv .venv`
2.  Activate it: `source .venv/bin/activate`
3.  Install dependencies: `pip install -r requirements.txt`
4.  Create a `.env` file with the necessary environment variables (see below).

## Usage

To start the bot, run:

```
python main.py
```

### Environment Variables

The following environment variables are required:

*   `DISCORD_TOKEN`: The token for your Discord bot.
*   `AWS_REGION`: The AWS region for the Bedrock and Knowledge Base services.
*   `AWS_ACCESS_KEY_ID`: Your AWS access key.
*   `AWS_SECRET_ACCESS_KEY`: Your AWS secret key.