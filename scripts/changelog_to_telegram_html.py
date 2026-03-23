#!/usr/bin/env python3

import argparse
import html
import re
from pathlib import Path


def format_inline(text):
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", escaped)
    escaped = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", escaped)
    return escaped


def main():
    parser = argparse.ArgumentParser(description="Convert changelog markdown to Telegram HTML.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rendered_lines = []
    for raw_line in Path(args.input).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            rendered_lines.append("")
            continue

        if line.startswith("## "):
            rendered_lines.append(f"<b>{format_inline(line[3:].strip())}</b>")
            continue

        if line.startswith("# "):
            rendered_lines.append(f"<b>{format_inline(line[2:].strip())}</b>")
            continue

        if line.startswith("\u2022 "):
            rendered_lines.append(f"&#8226; {format_inline(line[2:].strip())}")
            continue

        if re.match(r"^[*-]\s+", line):
            rendered_lines.append(f"&#8226; {format_inline(re.sub(r'^[*-]\s+', '', line))}")
            continue

        rendered_lines.append(format_inline(line))

    message = "\n".join(rendered_lines).strip()
    Path(args.output).write_text(message + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
