from common import logger

from dataclasses import dataclass
from html.parser import HTMLParser
import mailparser
from markdownify import markdownify
import urllib
import pdf

log = logger(__name__)


@dataclass
class Email:
    subject: str
    content: str
    original_message_id: str
    labels: list[str]
    links: list[str]


def parse_email(content: str) -> Email:
    mail = mailparser.parse_from_bytes(content)

    # Extract original message ID for reply threading
    original_message_id = get_original_message_id(mail)
    log.info(f"Original message ID: {original_message_id}")

    # Extract labels from recipient email address
    recipient_email = None
    for recipient in mail.to:
        _, email_address = recipient
        if email_address and "@" in email_address:
            recipient_email = email_address
            break

    labels = email_address_labels(recipient_email) if recipient_email else []
    log.info(f"Labels: {labels}")

    parser = parse_email.EmailHTMLParser()
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
    return Email(
        subject=mail.subject,
        content=full_content,
        original_message_id=original_message_id,
        labels=labels,
        links=links,
    )


def get_original_message_id(mail):
    # Case-insensitive lookup for x-forwarded-message-id header
    original_message_id = None
    for name, val in mail.headers.items():
        if name.lower() == "x-forwarded-message-id":
            return val

    if mail.message_id:
        return mail.message_id

    return None


def email_address_labels(email_address):
    """Extract labels from email address in format user+label1+label2@example.com"""
    local_part = email_address.split("@")[0]
    labels = local_part.split("+")[1:]  # Skip the username part
    return [label.strip().lower() for label in labels if label.strip()]


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


def parse_html(content):
    """Parse HTML content and convert it to markdown."""
    parser = EmailHTMLParser()
    parser.feed(content)
    return parser.markdown, parser.urls


class EmailHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.markdown = []
        self.urls = []

    def feed(self, content):
        self.markdown.append(markdownify(content))
        super().feed(content)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, val in attrs:
                if name == "href":
                    self.urls.append(val)
