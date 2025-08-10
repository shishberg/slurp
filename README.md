# Slurp

Slurp is a project designed to help parents stay on top of school communications. It automatically ingests and summarizes emails, and provides a chatbot for asking questions.

## Components

*   **[ingest](./ingest/README.md)**: A service that listens for emails, processes their content (including PDF attachments), and sends a summarized version.
*   **[discord-bot](./discord-bot/README.md)**: A Discord bot that answers questions about the school information, with personalized answers based on the user's children.

## Architecture

The `ingest` service listens to an SQS queue for new email notifications. When an email arrives, it's parsed, and its content (along with any linked PDFs) is sent to a large language model for summarization. The summary is then sent to a specified email address.

The `discord-bot` uses a knowledge base to answer questions. This knowledge base is presumably populated by the `ingest` service.