import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "changelog_to_telegram_html.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "changelog_to_telegram_html", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


telegram_html = load_module()


class TelegramHtmlTests(unittest.TestCase):
    def test_format_inline_escapes_html_and_formats_markdown(self):
        self.assertEqual(
            telegram_html.format_inline("Use **bold** <tag> and *italic* plus _notes_"),
            "Use <b>bold</b> &lt;tag&gt; and <i>italic</i> plus <i>notes</i>",
        )

    def test_main_converts_markdown_to_telegram_safe_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            input_file = temp_path / "input.md"
            output_file = temp_path / "output.html"

            input_file.write_text(
                "## v1.2.3\n"
                "\n"
                "\u2022 Added **support**\n"
                "- Fixed <bug>\n"
                "Plain _text_\n",
                encoding="utf-8",
            )

            argv = [
                "changelog_to_telegram_html.py",
                "--input",
                str(input_file),
                "--output",
                str(output_file),
            ]

            with mock.patch.object(sys, "argv", argv):
                telegram_html.main()

            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                "<b>v1.2.3</b>\n"
                "\n"
                "&#8226; Added <b>support</b>\n"
                "&#8226; Fixed &lt;bug&gt;\n"
                "Plain <i>text</i>\n",
            )


if __name__ == "__main__":
    unittest.main()
