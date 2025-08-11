import os
import time
import boto3
import re
from datetime import datetime, timezone
from common import logger

log = logger(__name__)


def sanitize_filename(subject: str) -> str:
    """Sanitize the subject to create a valid filename."""
    sanitized = re.sub(r"[^\w\s-]", "", subject)
    sanitized = re.sub(r"[-\s]+", "_", sanitized)
    sanitized = sanitized.strip("_")
    if not sanitized:
        sanitized = "untitled"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    return f"{sanitized}_{timestamp}.md"


def upload_to_s3(subject: str, content: str) -> str:
    """Upload file content to S3 bucket."""
    filename = sanitize_filename(subject)
    try:
        s3 = boto3.client("s3")

        # Ensure content is bytes
        if isinstance(content, str):
            content = content.encode("utf-8")

        # Upload to S3
        bucket_name = os.getenv("KB_S3_BUCKET")
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=content,
            ContentType="text/markdown",
        )

        log.info(f"Successfully uploaded {filename} to s3://{bucket_name}")
        return filename

    except Exception as e:
        log.error(f"Failed to upload {filename} to S3: {e}")
        return False
