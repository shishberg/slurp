from textractor.entities.document import Document
from textractor.entities.layout import (
    LAYOUT_TITLE,
    LAYOUT_SECTION_HEADER,
    LAYOUT_LIST,
    LAYOUT_TEXT,
)
from dataclasses import dataclass, field
from typing import List, Generator
import uuid
import re


def _to_html(tag: str, content: str, attributes: dict = {}, indent: int = 0) -> str:
    """Generates an HTML element."""
    attrs = " ".join(f'{key}="{value}"' for key, value in attributes.items())
    if attrs:
        attrs = " " + attrs
    indent_str = "  " * indent

    if not tag in ("h1", "h2", "p"):
        # Indent each line of the content
        content = "\n".join(f"  {line}" for line in content.splitlines())
        content = f"\n{content}\n{indent_str}"
    else:
        content = content.strip()

    return f"{indent_str}<{tag}{attrs}>{content}</{tag}>"


@dataclass
class ContentElement:
    """Represents a piece of content in the document."""

    element_id: str
    text: str
    type: str  # e.g., 'p', 'li'

    def to_html(self) -> str:
        if self.type == "ul":
            items = "\n".join(
                _to_html("li", item.strip())
                for item in self.text.split("\n")
                if item.strip()
            )
            return _to_html("ul", items)
        return _to_html(self.type, self.text)

    def size(self) -> int:
        return len(self.text)


@dataclass
class Section:
    """Represents a section of the document, starting with a header."""

    section_id: str
    title: str
    level: int
    content: List[ContentElement] = field(default_factory=list)
    children: List["Section"] = field(default_factory=list)
    _size: int = 0

    def to_html(self) -> str:
        """Converts the section to an HTML string."""
        heading = _to_html(f"h{self.level}", self.title)
        content_html = "\n".join(elem.to_html() for elem in self.content)
        children_html = "\n".join(child.to_html() for child in self.children)
        inner_html = "\n".join(filter(None, [heading, content_html, children_html]))
        return _to_html("div", inner_html, {"id": self.section_id})

    def size(self) -> int:
        if self._size == 0:
            self._size = (
                len(self.title)
                + sum(elem.size() for elem in self.content)
                + sum(child.size() for child in self.children)
            )
        return self._size


def build_document_tree(document: Document) -> Section:
    """Builds a hierarchical tree of sections from a Textractor Document."""
    root = Section(section_id="fooid", title="Document", level=0)
    section_stack = [root]

    for layout_element in document.layouts:
        if layout_element.layout_type == LAYOUT_TITLE:
            new_section = Section(
                section_id=layout_element.id, title=layout_element.text, level=1
            )
            root.children.append(new_section)
            section_stack = [root, new_section]

        elif layout_element.layout_type == LAYOUT_SECTION_HEADER:
            level = 2  # Default level for section headers
            new_section = Section(
                section_id=layout_element.id, title=layout_element.text, level=level
            )
            # Adjust level based on hierarchy
            while len(section_stack) > 1 and level <= section_stack[-1].level:
                section_stack.pop()

            section_stack[-1].children.append(new_section)
            section_stack.append(new_section)

        elif layout_element.layout_type in [LAYOUT_TEXT, LAYOUT_LIST]:
            content_type = "p"
            if layout_element.layout_type == LAYOUT_LIST:
                content_type = "ul"

            section_stack[-1].content.append(
                ContentElement(
                    element_id=layout_element.id,
                    text=layout_element.text,
                    type=content_type,
                )
            )
    return root


def _chunk_section(section: Section, size_hint: int) -> Generator[Section, None, None]:
    """Recursively chunks a section."""
    if section.size() <= size_hint:
        yield section
        return

    current_chunk_content = []
    current_chunk_children = []
    current_chunk_size = len(section.title)

    def _yield_chunk():
        nonlocal current_chunk_content, current_chunk_children, current_chunk_size
        if current_chunk_content or current_chunk_children:
            yield Section(
                section.section_id,
                section.title,
                section.level,
                current_chunk_content,
                current_chunk_children,
            )
        current_chunk_content = []
        current_chunk_children = []
        current_chunk_size = len(section.title)

    for content_element in section.content:
        if current_chunk_size + content_element.size() > size_hint:
            yield from _yield_chunk()
        current_chunk_content.append(content_element)
        current_chunk_size += content_element.size()

    for child_section in section.children:
        if current_chunk_size + child_section.size() > size_hint:
            yield from _yield_chunk()

        if child_section.size() > size_hint:
            yield from _yield_chunk()
            yield from _chunk_section(child_section, size_hint)
        else:
            current_chunk_children.append(child_section)
            current_chunk_size += child_section.size()

    yield from _yield_chunk()


def to_markdown_chunks(
    document: Document, size_hint: int = 10000
) -> Generator[str, None, None]:
    """
    Generates structured markdown chunks from a Textractor Document.

    Args:
        document: The Textractor Document object.
        size_hint: The desired approximate size of each chunk in characters.

    Yields:
        str: HTML-formatted chunks of the document.
    """
    document_tree = build_document_tree(document)
    for section in document_tree.children:
        for chunk in _chunk_section(section, size_hint):
            yield chunk.to_html()


if __name__ == "__main__":
    import sys
    from textractor.data.constants import TextractFeatures
    from textractor.entities.document import Document

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <filename>", file=sys.stderr)
        sys.exit(1)

    document = Document.open(sys.argv[1])

    for chunk in to_markdown_chunks(document):
        print(chunk)
        print("=========================")
