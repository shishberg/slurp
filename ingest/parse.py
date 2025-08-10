from html.parser import HTMLParser
from markdownify import markdownify


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
