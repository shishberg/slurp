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

    def fetch_textract():
        """Compute the textract result on cache miss."""
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
        return document.to_markdown().encode("utf-8")

    # Get cached result or compute and cache new result
    result = _cache.get(content, fetch_textract)
    return result.decode("utf-8")
