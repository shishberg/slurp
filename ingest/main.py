import send_email
import llm
import parse_email
import kb
from common import logger

import boto3
import os
import time
import json
from types import SimpleNamespace
import base64
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
        raw_email = base64.b64decode(msg.content)
        mail = parse_email.parse_email(raw_email)

        # Conditional S3 upload based on 'forget' label
        if "forget" not in mail.labels:
            kb.upload_to_s3(mail.subject, mail.content)
            kb.upload_to_pinecone(mail.subject, mail.content)

        # Conditional summary creation and email reply based on 'summary' label
        if "summary" in mail.labels:
            summary = llm.summarise(mail.content)
            if mail.links:
                summary += "\n---\n"
                summary += "\n\n".join(mail.links)

            send_email.send_email(
                sender=os.getenv("EMAIL_SENDER"),
                recipient=os.getenv("EMAIL_RECIPIENT"),
                subject=f"Re: {mail.subject}",
                body=summary,
                original_message_id=mail.original_message_id,
            )
            log.info("Sent summary email")

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


if __name__ == "__main__":
    # Create listener instance
    listener = SQSListener(os.getenv("SQS_QUEUE_URL"), region_name="ap-southeast-2")

    # Start listening
    try:
        listener.listen()
    except KeyboardInterrupt:
        log.info("Shutting down listener")
