import unittest
import sys
import os

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from parse import parse_html


class TestParseHtml(unittest.TestCase):
    """Test cases for the parse_html function."""

    def test_parse_simple_html(self):
        """Test parsing simple HTML content."""
        html_content = "<h1>Hello World</h1><p>This is a test.</p>"
        markdown, urls = parse_html(html_content)

        # Check that we get markdown content as a list
        self.assertIsInstance(markdown, list)
        self.assertEqual(len(markdown), 1)
        self.assertIn("Hello World", markdown[0])
        self.assertIn("This is a test", markdown[0])

        # Check that URLs list is empty for content without links
        self.assertEqual(urls, [])

    def test_parse_html_with_links(self):
        """Test parsing HTML with links."""
        html_content = (
            '<p>Visit <a href="https://example.com">our website</a> for more info.</p>'
        )
        markdown, urls = parse_html(html_content)

        # Check that we get the URL
        self.assertEqual(urls, ["https://example.com"])

        # Check that markdown contains the link text as a list
        self.assertIsInstance(markdown, list)
        self.assertEqual(len(markdown), 1)
        self.assertIn("our website", markdown[0])

    def test_parse_empty_html(self):
        """Test parsing empty HTML content."""
        html_content = ""
        markdown, urls = parse_html(html_content)

        # Check that we get empty results as a list
        self.assertIsInstance(markdown, list)
        self.assertEqual(markdown, [""])
        self.assertEqual(urls, [])

    def test_parse_complex_html(self):
        """Test parsing more complex HTML with multiple elements."""
        html_content = """
        <div>
            <h2>Section Title</h2>
            <p>Check out <a href="https://github.com">GitHub</a> and
            <a href="https://stackoverflow.com">Stack Overflow</a>.</p>
        </div>
        """
        markdown, urls = parse_html(html_content)

        # Check that we get both URLs
        self.assertEqual(len(urls), 2)
        self.assertIn("https://github.com", urls)
        self.assertIn("https://stackoverflow.com", urls)

        # Check that content is preserved as a list
        self.assertIsInstance(markdown, list)
        self.assertEqual(len(markdown), 1)
        self.assertIn("Section Title", markdown[0])
        self.assertIn("Check out", markdown[0])


if __name__ == "__main__":
    unittest.main()
