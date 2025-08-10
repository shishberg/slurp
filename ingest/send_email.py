from common import logger

import boto3
import markdown
from botocore.exceptions import ClientError
import dotenv

dotenv.load_dotenv()

log = logger(__name__)

ses_client = boto3.client("ses")


def send_email(sender, recipient, subject, body):
    """Send an email with markdown body converted to HTML"""
    log.info(body)
    html_content = markdown.markdown(body)

    response = ses_client.send_email(
        Source=sender,
        Destination={"ToAddresses": [recipient]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Html": {"Data": html_content, "Charset": "UTF-8"}},
        },
    )
    log.info(f"Email sent! Message ID: {response['MessageId']}")
    return response
