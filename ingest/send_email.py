from common import logger

import boto3
import markdown
from botocore.exceptions import ClientError
import dotenv

dotenv.load_dotenv()

log = logger(__name__)

ses_client = boto3.client("ses")


def send_email(sender, recipient, subject, body, original_message_id=None):
    """Send an email with markdown body converted to HTML"""
    log.info(body)
    html_content = markdown.markdown(body)

    message = {
        "Subject": {"Data": subject, "Charset": "UTF-8"},
        "Body": {"Html": {"Data": html_content, "Charset": "UTF-8"}},
    }

    # Add reply headers if original message ID is provided
    if original_message_id:
        message["Headers"] = [
            {"Name": "In-Reply-To", "Value": original_message_id},
            {"Name": "References", "Value": original_message_id},
        ]

    response = ses_client.send_email(
        Source=sender,
        Destination={"ToAddresses": [recipient]},
        Message=message,
    )
    log.info(f"Email sent! Message ID: {response['MessageId']}")
    return response
