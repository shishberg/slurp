from common import logger

import json
from textractor import Textractor
from textractor.data.constants import TextractFeatures

log = logger(__name__)


def textract(content):
    """Extract PDF content and convert to markdown using Amazon Textract."""
    # AWS credentials will be loaded from environment variables
    extractor = Textractor()

    log.info("calling Textract API")
    document = extractor.start_document_analysis(
        file_source=content,
        s3_upload_path="s3://mcleish-slurp-textract-tmp/",
        save_image=False,
        features=[
            TextractFeatures.TABLES,
            TextractFeatures.FORMS,
            TextractFeatures.LAYOUT,
        ],
    )
    return document.to_markdown()
