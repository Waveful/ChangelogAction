#!/usr/bin/env python3
"""Normalize markdown formatting in changelog text.

Ensures bullet lines (•) render on separate lines in markdown previews
and that ## headings are properly separated from surrounding content.
"""

import argparse
import re
from pathlib import Path


NOOP_DEPENDENCY_BULLET_RE = re.compile(
    r"^[ \t]*(?:[•*-]|\d+[.)])[ \t]+"
    r"(?:update(?:d|s)?|bump(?:ed|s)?|upgrade(?:d|s)?)\s+"
    r"(?:some\s+)?dependenc(?:y|ies)\s*"
    r"\(\s*(?:none|n/?a|not applicable|no dependencies?)\s*\)"
    r"[.!?]?[ \t]*$",
    flags=re.IGNORECASE | re.MULTILINE,
)


def normalize(text):
    # Ensure blank line before ## headings (when not already preceded by one)
    text = re.sub(r"(?<!\n)\n(## )", r"\n\n\1", text)
    # Ensure blank line after ## headings
    text = re.sub(r"^(## .+)$\n(?!\n)", r"\1\n\n", text, flags=re.MULTILINE)
    # Append two trailing spaces to every • line (markdown hard line break)
    text = re.sub(r"^(•.+?)[ \t]*$", r"\1  ", text, flags=re.MULTILINE)
    # Collapse triple+ newlines into one blank line
    text = re.sub(r"\n{3,}", r"\n\n", text)
    return text


def remove_noop_dependency_bullets(text):
    return "\n".join(
        line for line in text.splitlines() if not NOOP_DEPENDENCY_BULLET_RE.match(line)
    )


CHANGELOG_FILTERS = (
    remove_noop_dependency_bullets,
)


def filter_changelog(text):
    for changelog_filter in CHANGELOG_FILTERS:
        text = changelog_filter(text)
    return text


def main():
    parser = argparse.ArgumentParser(description="Normalize changelog markdown in-place.")
    parser.add_argument("file", help="Markdown file to normalize")
    args = parser.parse_args()

    path = Path(args.file)
    content = path.read_text(encoding="utf-8")
    filtered = filter_changelog(content.strip())
    normalized = normalize(filtered) + "\n"
    path.write_text(normalized, encoding="utf-8")


if __name__ == "__main__":
    main()
