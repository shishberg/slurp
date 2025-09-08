from dataclasses import dataclass
from io import BytesIO
from common import logger

import os
from typing import Generator, List
from html.parser import HTMLParser
from markdownify import markdownify
from email.message import EmailMessage
from email.parser import Parser
from email.utils import parseaddr
from email import policy
import urllib
import pdf

log = logger(__name__)

email_parser = Parser(policy=policy.default)


class Email:
    parts: List[EmailMessage]

    def __init__(self):
        self.parts = []

    def original_message_id(self) -> str:
        for part in self.parts:
            message_id = part.get("x-forwarded-message-id")
            if message_id:
                return message_id
            message_id = part.get("message-id")
            if message_id:
                return message_id
        return None

    def subject(self) -> str:
        return self.get_first("subject")

    def from_(self) -> str:
        return self.get_first("from")

    def to(self) -> List[str]:
        return list(self.get_all("to"))

    def get_first(self, header: str) -> str:
        """Get the first occurrence of a header from the email parts."""
        for part in self.parts:
            value = part.get(header)
            if value:
                return value
        return None

    def get_all(self, header: str) -> Generator[str, None, None]:
        """Get all occurrences of a header from the email parts."""
        for part in self.parts:
            values = part.get_all(header, [])
            if values:
                yield from values

    def html_parts(self) -> Generator[str, None, None]:
        yield from (
            part.get_content()
            for part in self.parts
            if part.get_content_type().endswith("/html")
        )

    def content_type_parts(self, content_type: str) -> Generator[str, None, None]:
        yield from (
            part.get_content()
            for part in self.parts
            if part.get_content_type().lower() == content_type
        )

    def __repr__(self):
        s = f"Email(parts={len(self.parts)})\n"
        s += f"  Original Message ID: {self.original_message_id()}\n"
        s += f"  Subject: {self.subject()}\n"
        s += f"  From: {self.from_()}\n"
        s += f"  To: {', '.join(self.to())}\n"
        html_content = "\n---\n".join(self.html_parts())
        stripped_html = html_content.replace("\n", "")
        s += f"  HTML Content: {len(html_content)} {stripped_html[:100]}...\n"
        for part in self.parts:
            try:
                content_length = len(part.get_content())
            except:
                content_length = 0
            subject = part.get("subject", "No Subject")
            s += f"  - {subject} - {part.get_content_type()} ({content_length} bytes)\n"
        return s


def _walk_email(mail: EmailMessage) -> Generator[Email, None, None]:
    root_email = Email()
    root_email.parts.append(mail)

    for part in mail.iter_parts():
        if part.is_multipart():
            yield from _walk_email(part)
            continue

        root_email.parts.append(part)

    yield root_email


@dataclass
class EmailPart:
    subject: str
    content: str
    links: List[str]


class EmailContents:
    original_message_id: str
    parts: List[EmailPart]

    def __init__(self):
        self.parts = []


def parse(content: str) -> EmailContents:
    mail = email_parser.parsestr(content)

    result = EmailContents()

    # Extract original message ID for reply threading
    result.original_message_id = get_original_message_id(mail)
    log.info(f"Processing email with original message ID: {result.original_message_id}")

    for part in _walk_email(mail):
        if part.from_() == os.getenv("EMAIL_SENDER"):
            # Avoid infinite loop
            # TODO: better parsing of EMAIL_SENDER
            log.info("Skipping email from sender address")
            continue

        contents = []
        links = []

        headers = ""
        want_headers = {
            "from",
            "to",
            "cc",
            "bcc",
            "subject",
            "date",
            "message-id",
            "x-forwarded-message-id",
        }
        for key in want_headers:
            value = part.get_all(key)
            if value:
                for val in value:
                    headers += f"{key.title()}: {val}\n"
        contents.append(headers)

        for html_content in part.html_parts():
            html_content = html_content.strip()
            if len(html_content) == 0:
                continue
            markdown, urls = parse_html(html_content)
            if len(markdown) == 0:
                continue
            contents.append(markdown)
            links.extend(u for u in urls if should_fetch_url(u))

        # TODO: change this and fetch_url into handlers
        # mapped from content type
        for pdf_content in part.content_type_parts("application/pdf"):
            markdown = pdf.textract(pdf_content)
            contents.append(markdown)

        for url in links:
            content = fetch_url(url)
            if content:
                contents.append(content)

        if len(contents) == 1:  # headers only
            continue

        full_content = "\n---\n".join(contents)
        result.parts.append(EmailPart(part.subject(), full_content, links))

    return result


def get_original_message_id(mail: EmailMessage):
    return mail.get("x-forwarded-message-id") or mail.get("message-id")


def recipient_labels(recipients: List[str]):
    for recipient in recipients:
        # Assume recipient is of the form "Name <email@domain.com>"
        _, email_address = parseaddr(recipient)
        if not email_address:
            # Try again assuming recipient is of the form "email@domain.com"
            email_address = recipient
        local_part = email_address.split("@")[0]
        labels = local_part.split("+")[1:]  # Skip the username part
        yield from (label.strip().lower() for label in labels if label.strip())


def fetch_url(url):
    log.info(f"Fetching URL: {url}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0"
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


def parse_html(content) -> tuple[str, list[str]]:
    """Parse HTML content and convert it to markdown."""
    parser = LinkExtractor()
    parser.feed(content)
    return markdownify(content, heading_style="ATX"), parser.urls


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, val in attrs:
                if name == "href":
                    self.urls.append(val)


if __name__ == "__main__":
    with open("mail.example", "r") as f:
        mail = parse(f.read())

        log.info(f"Original message ID: {mail.original_message_id}")
        log.info(f"Labels: {list(mail.labels)}")
        for i, part in enumerate(mail.parts):
            log.info(f"Part {i}:\n{part}")
