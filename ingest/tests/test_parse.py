import sys
import os


from parse_email import recipient_labels


class TestEmailLabelExtraction:
    """Test cases for email label extraction functionality."""

    def test_extract_single_label(self):
        """Test extraction of a single label."""
        result = list(recipient_labels(["user+summary@example.com"]))
        assert result == ["summary"]

    def test_extract_multiple_labels(self):
        """Test extraction of multiple labels."""
        result = list(recipient_labels(["user+summary+forget@example.com"]))
        assert result == [
            "summary",
            "forget",
        ]

    def test_extract_labels_with_mixed_case(self):
        """Test extraction handles case insensitivity."""
        result = list(recipient_labels(["user+Summary+FORGET@example.com"]))
        assert result == [
            "summary",
            "forget",
        ]

    def test_extract_labels_with_spaces(self):
        """Test extraction handles spaces around labels."""
        result = list(recipient_labels(["user+ summary + forget @example.com"]))
        assert result == [
            "summary",
            "forget",
        ]

    def test_no_labels(self):
        """Test extraction when no labels are present."""
        result = list(recipient_labels(["user@example.com"]))
        assert result == []

    def test_empty_labels(self):
        """Test extraction with empty labels."""
        result = list(recipient_labels(["user++@example.com"]))
        assert result == []

    def test_malformed_email(self):
        """Test extraction with malformed email addresses."""
        result1 = list(recipient_labels(["invalid-email"]))
        result2 = list(recipient_labels([""]))
        # The function doesn't handle None values in the list, so we don't test that case
        assert result1 == []
        assert result2 == []

    def test_complex_labels(self):
        """Test extraction with complex label names."""
        result = list(recipient_labels(["user+test-label+another_label@example.com"]))
        assert result == [
            "test-label",
            "another_label",
        ]

    def test_special_characters_in_labels(self):
        """Test extraction handles special characters in labels."""
        result = list(recipient_labels(["user+test123+label-with-dashes@example.com"]))
        assert result == [
            "test123",
            "label-with-dashes",
        ]


import unittest
import sys
import os


from ingest.parse_email import parse_html


class TestParseHtml(unittest.TestCase):
    """Test cases for the parse_html function."""

    def test_parse_simple_html(self):
        """Test parsing simple HTML content."""
        html_content = "<h1>Hello World</h1><p>This is a test.</p>"
        markdown, urls = parse_html(html_content)

        # Check that we get markdown content as a string
        self.assertIsInstance(markdown, str)
        self.assertIn("Hello World", markdown)
        self.assertIn("This is a test", markdown)

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

        # Check that markdown contains the link text as a string
        self.assertIsInstance(markdown, str)
        self.assertIn("our website", markdown)

    def test_parse_empty_html(self):
        """Test parsing empty HTML content."""
        html_content = ""
        markdown, urls = parse_html(html_content)

        # Check that we get empty results as a string
        self.assertIsInstance(markdown, str)
        self.assertEqual(markdown, "")
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

        # Check that content is preserved as a string
        self.assertIsInstance(markdown, str)
        self.assertIn("Section Title", markdown)
        self.assertIn("Check out", markdown)


if __name__ == "__main__":
    unittest.main()
