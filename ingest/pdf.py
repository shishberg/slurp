from common import logger
from cache import DiskCache

from textractor import Textractor
from textractor.data.constants import TextractFeatures
import os
import dotenv

dotenv.load_dotenv()

log = logger(__name__)

_cache = DiskCache(cache_dir=".cache/pdf_textract")


def textract(content: bytes) -> str:
    """Extract PDF content and convert to markdown using Amazon Textract."""
    # Check cache first
    cached_result = _cache.get(content)
    if cached_result is not None:
        return cached_result.decode("utf-8")

    # AWS credentials will be loaded from environment variables
    extractor = Textractor()

    log.info("calling Textract API")
    document = extractor.start_document_analysis(
        file_source=content,
        s3_upload_path=f"s3://{os.getenv('TEXTRACT_S3_BUCKET')}/",
        save_image=False,
        features=[
            # TextractFeatures.TABLES,
            TextractFeatures.LAYOUT,
        ],
    )
    result = document.to_markdown()

    # Cache the result
    _cache.set(content, result.encode("utf-8"))

    return result
