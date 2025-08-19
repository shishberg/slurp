import sys
import os

# Add the parent directory to the path so we can import from ingest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import extract_email_labels


class TestEmailLabelExtraction:
    """Test cases for email label extraction functionality."""

    def test_extract_single_label(self):
        """Test extraction of a single label."""
        assert extract_email_labels("user+summary@example.com") == ["summary"]

    def test_extract_multiple_labels(self):
        """Test extraction of multiple labels."""
        assert extract_email_labels("user+summary+forget@example.com") == [
            "summary",
            "forget",
        ]

    def test_extract_labels_with_mixed_case(self):
        """Test extraction handles case insensitivity."""
        assert extract_email_labels("user+Summary+FORGET@example.com") == [
            "summary",
            "forget",
        ]

    def test_extract_labels_with_spaces(self):
        """Test extraction handles spaces around labels."""
        assert extract_email_labels("user+ summary + forget @example.com") == [
            "summary",
            "forget",
        ]

    def test_no_labels(self):
        """Test extraction when no labels are present."""
        assert extract_email_labels("user@example.com") == []

    def test_empty_labels(self):
        """Test extraction with empty labels."""
        assert extract_email_labels("user++@example.com") == []

    def test_malformed_email(self):
        """Test extraction with malformed email addresses."""
        assert extract_email_labels("invalid-email") == []
        assert extract_email_labels("") == []
        assert extract_email_labels(None) == []

    def test_complex_labels(self):
        """Test extraction with complex label names."""
        assert extract_email_labels("user+test-label+another_label@example.com") == [
            "test-label",
            "another_label",
        ]

    def test_special_characters_in_labels(self):
        """Test extraction handles special characters in labels."""
        assert extract_email_labels("user+test123+label-with-dashes@example.com") == [
            "test123",
            "label-with-dashes",
        ]


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
