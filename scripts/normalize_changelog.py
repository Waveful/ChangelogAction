#!/usr/bin/env python3
"""Normalize markdown formatting in changelog text.

Ensures bullet lines (•) render on separate lines in markdown previews
and that ## headings are properly separated from surrounding content.
"""

import argparse
import re
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser(description="Normalize changelog markdown in-place.")
    parser.add_argument("file", help="Markdown file to normalize")
    args = parser.parse_args()

    path = Path(args.file)
    content = path.read_text(encoding="utf-8")
    normalized = normalize(content.strip()) + "\n"
    path.write_text(normalized, encoding="utf-8")


if __name__ == "__main__":
    main()
