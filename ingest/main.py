import send_email
import llm
import parse
import pdf
import kb
from common import logger

import urllib
import boto3
import os
import time
import json
from types import SimpleNamespace
import base64
import mailparser
import traceback
import dotenv

dotenv.load_dotenv()

log = logger(__name__)


class SQSListener:
    def __init__(self, queue_url, region_name):
        self.queue_url = queue_url
        self.region_name = region_name
        self.sqs = boto3.client("sqs", region_name=region_name)

    def process_message(self, payload):
        body = json.loads(payload["Body"], object_hook=lambda d: SimpleNamespace(**d))
        msg = json.loads(body.Message, object_hook=lambda d: SimpleNamespace(**d))
        content = base64.b64decode(msg.content)
        mail = mailparser.parse_from_bytes(content)
        parser = parse.EmailHTMLParser()
        for html in mail.text_html:
            parser.feed(html)
        contents = parser.markdown
        links = []
        for url in parser.urls:
            content = maybe_fetch_url(url)
            if content:
                contents.append(content)
                links.append(url)

        full_content = "\n---\n".join(contents)

        # Upload to S3
        kb.upload_to_s3(mail.subject, full_content)

        summary = llm.summarise(full_content)
        if links:
            summary += "\n---\n"
            summary += "\n\n".join(links)

        # Extract original message ID for reply threading
        original_message_id = None
        if hasattr(mail, "message_id") and mail.message_id:
            original_message_id = mail.message_id

        send_email.send_email(
            sender=os.getenv("EMAIL_SENDER"),
            recipient=os.getenv("EMAIL_RECIPIENT"),
            subject=f"Re: {mail.subject}",
            body=summary,
            original_message_id=original_message_id,
        )
        return True

    def listen(self):
        log.info(f"Listening on {self.queue_url}")
        while True:
            try:
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                    VisibilityTimeout=30,
                )
                messages = response.get("Messages", [])
                for message in messages:
                    if self.process_message(message):
                        self.sqs.delete_message(
                            QueueUrl=self.queue_url,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
                    else:
                        log.error("Failed to process message, not deleting")

            except Exception as e:
                log.error(f"Error receiving message: {e}")
                stacktrace = traceback.format_exc()
                log.error(stacktrace)
                time.sleep(5)


def maybe_fetch_url(url):
    if not should_fetch_url(url):
        return None
    log.info(f"Fetching URL: {url}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
        },
    )
    res = urllib.request.urlopen(req)
    if res.status != 200:
        raise Exception(f"Failed to fetch {url}: {res.status} {res.reason}")
    content = res.read()
    content_type = res.getheader("Content-Type", "not sent").split(";")[0].strip()
    if content_type == ("application/pdf"):
        return pdf.textract(content)
    log.info(f"Skipping URL {url} with content type {content_type}")


def should_fetch_url(url):
    url = url.lower()
    if not url.startswith("https://"):
        return False
    if url.endswith(".pdf"):
        return True
    if url.find("attachment") != -1:
        return True
    if url.find("download") != -1:
        return True
    log.info(f"Skipping URL: {url}")
    return False


if __name__ == "__main__":
    # Create listener instance
    listener = SQSListener(os.getenv("SQS_QUEUE_URL"), region_name="ap-southeast-2")

    # Start listening
    listener.listen()
