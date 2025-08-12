# Project State

## High-Level Architecture

### Ingestion Pipeline
- Emails are received by AWS SES, routed to an SNS topic, then to an SQS queue.
- A Python service (`ingest/`) listens to the SQS queue, reads emails, and follows links to PDFs.
- Amazon Textract is used to convert PDFs to text.
- An LLM via Amazon Bedrock generates summaries and email replies.
- Raw email content and extracted text are stored in an S3 bucket.

### Knowledge Base
- Currently, a Bedrock Knowledge Base is backed by PostgreSQL with a vector extension.
- The intent is to automate syncing from the S3 bucket to this knowledge base (manual currently).
- Future plan to migrate the vector store to a dedicated service like Pinecone.

### User Interaction (Discord Bot)
- A Discord bot (`discord-bot/`) listens for user questions.
- It uses Retrieval Augmented Generation (RAG) with the knowledge base to provide answers.
- The bot's prompt is customized with the user's children's names and classes.

## Current Status
- The core ingestion and processing pipeline for single emails is functional.
- The Discord bot can answer questions using the knowledge base.
- The system is currently designed for a single user.

## What's Not Yet Implemented
- Automated synchronization from S3 to the Bedrock Knowledge Base.
- Multi-user support (authentication, authorization, per-user settings).
- Robust event reminder system.
- Comprehensive evaluation framework for LLM pipelines.
- Advanced infrastructure practices (IaC, CI/CD, observability).
- Support for interaction surfaces beyond email and Discord.