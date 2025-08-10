# Ingest Service

This service is responsible for ingesting and processing emails.

## How it Works

The service listens to an Amazon SQS queue for notifications of new emails. When a message is received, it:

1.  Parses the email content.
2.  If the email contains links to PDFs, it fetches and extracts the text from them using Amazon Textract.
3.  The combined text is then sent to a large language model (Anthropic Claude on Amazon Bedrock) to be summarized.
4.  The summary is then sent as an email to a pre-configured recipient.

## Setup

1.  Create a virtual environment: `python -m venv .venv`
2.  Activate it: `source .venv/bin/activate`
3.  Install dependencies: `pip install -r requirements.txt`
4.  Create a `.env` file with the necessary environment variables (see below).

## Usage

To start the service, run:

```
python main.py
```

### Environment Variables

The following environment variables are required:

*   `SQS_QUEUE_URL`: The URL of the SQS queue to listen to.
*   `EMAIL_SENDER`: The email address to send summaries from.
*   `EMAIL_RECIPIENT`: The email address to send summaries to.
*   `AWS_DEFAULT_REGION`: The AWS region for SQS and Bedrock.
*   `AWS_ACCESS_KEY_ID`: Your AWS access key.
*   `AWS_SECRET_ACCESS_KEY`: Your AWS secret key.
*   `TEXTRACT_S3_BUCKET`: An S3 bucket for Textract to use for temporary storage.