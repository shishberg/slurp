from common import logger

import boto3
import markdown
from botocore.exceptions import ClientError
import dotenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

dotenv.load_dotenv()

log = logger(__name__)

ses_client = boto3.client("ses")


def send_email(sender, recipient, subject, body, original_message_id=None):
    """Send an email with markdown body converted to HTML"""
    log.info(body)
    html_content = markdown.markdown(body)

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    # Add reply headers if original message ID is provided
    if original_message_id:
        msg["In-Reply-To"] = original_message_id
        msg["References"] = original_message_id

    # Add the HTML content
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    # Send the raw email
    response = ses_client.send_raw_email(
        Source=sender, Destinations=[recipient], RawMessage={"Data": msg.as_string()}
    )

    log.info(f"Email sent! Message ID: {response['MessageId']}")
    return response
