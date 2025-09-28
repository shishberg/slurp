import os
import boto3
import re
from datetime import datetime, timezone
from common import logger
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import (
    MarkdownTextSplitter,
    ExperimentalMarkdownSyntaxTextSplitter,
)

log = logger(__name__)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "slurp")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))


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

        log.info(f"Uploaded {filename} to s3://{bucket_name}")
        return filename

    except Exception as e:
        log.error(f"Failed to upload {filename} to S3: {e}")
        return False


def upload_to_pinecone(
    filename: str,
    md: str,
    embedding_model,
    chunking_function,
    metadata: dict[str, str] = None,
):
    """Upload markdown content to Pinecone index."""
    if metadata is None:
        metadata = {}

    docs = chunking_function.create_documents([md], metadatas=[metadata])

    vectorstore = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX"),
        embedding=embedding_model,
        namespace=PINECONE_NAMESPACE,
    )
    vectorstore.add_documents(docs)
    log.info(f"Uploaded {len(docs)} documents to Pinecone index")


if __name__ == "__main__":
    content = open(
        "experiments/Fwd_SPPS_School_newsletter_20250814_131209.md", "r"
    ).read()
    upload_to_pinecone("filename", content, metadata={"source": "test_email"})
