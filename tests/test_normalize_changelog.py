import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "normalize_changelog.py"


def load_module():
    spec = importlib.util.spec_from_file_location("normalize_changelog", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


normalize_mod = load_module()


class NormalizeChangelogTests(unittest.TestCase):
    def test_adds_blank_line_after_heading(self):
        text = "## v1.0\n• First bullet\n• Second bullet"
        result = normalize_mod.normalize(text)
        self.assertIn("## v1.0\n\n", result)

    def test_adds_blank_line_before_heading(self):
        text = "• Last bullet\n## v2.0\n• New bullet"
        result = normalize_mod.normalize(text)
        self.assertIn("\n\n## v2.0", result)

    def test_adds_trailing_spaces_to_bullet_lines(self):
        text = "## v1.0\n\n• First bullet\n• Second bullet"
        result = normalize_mod.normalize(text)
        for line in result.split("\n"):
            if line.startswith("•"):
                self.assertTrue(
                    line.endswith("  "), f"Missing trailing spaces: {line!r}"
                )

    def test_replaces_existing_trailing_whitespace_with_two_spaces(self):
        text = "## v1.0\n\n• Bullet with tabs\t\t"
        result = normalize_mod.normalize(text)
        bullet = [l for l in result.split("\n") if l.startswith("•")][0]
        self.assertTrue(bullet.endswith("  "))
        self.assertNotIn("\t", bullet)

    def test_does_not_double_existing_blank_lines(self):
        text = "## v1.0\n\n• First  \n• Second  \n\n## v2.0\n\n• Third  "
        result = normalize_mod.normalize(text)
        self.assertNotIn("\n\n\n", result)

    def test_collapses_triple_newlines(self):
        text = "## v1.0\n\n\n\n• First bullet"
        result = normalize_mod.normalize(text)
        self.assertNotIn("\n\n\n", result)
        self.assertIn("## v1.0\n\n• First bullet", result)

    def test_preserves_heading_text(self):
        text = "## deployed-2026-03-24T1317Z\n• Some change"
        result = normalize_mod.normalize(text)
        self.assertIn("## deployed-2026-03-24T1317Z", result)

    def test_filter_removes_noop_dependency_bullet(self):
        text = "## v1.0\n\n• Added login\n• Update some dependencies (none)\n• Fixed logout"
        result = normalize_mod.filter_changelog(text)
        self.assertIn("• Added login", result)
        self.assertIn("• Fixed logout", result)
        self.assertNotIn("• Added login\n\n• Fixed logout", result)
        self.assertNotIn("Update some dependencies (none)", result)

    def test_filter_preserves_named_dependency_bullet(self):
        text = "## v1.0\n\n• Update some dependencies (firebase, sentry)"
        result = normalize_mod.filter_changelog(text)
        self.assertIn("• Update some dependencies (firebase, sentry)", result)

    def test_normalize_does_not_filter_changelog_content(self):
        text = "## v1.0\n\n• Update some dependencies (none)"
        result = normalize_mod.normalize(text)
        self.assertIn("• Update some dependencies (none)  ", result)

    def test_idempotent(self):
        text = "## v1.0\n\n• First  \n• Second  \n\n## v2.0\n\n• Third  "
        first = normalize_mod.normalize(text)
        second = normalize_mod.normalize(first)
        self.assertEqual(first, second)

    def test_full_changelog_with_header(self):
        text = (
            "# Changelog\n\n"
            "## v2.0\n• New feature\n• Bug fix\n\n"
            "## v1.0\n• Initial release"
        )
        result = normalize_mod.normalize(text)
        self.assertIn("## v2.0\n\n• New feature  \n• Bug fix  ", result)
        self.assertIn("\n\n## v1.0\n\n• Initial release  ", result)
        self.assertNotIn("\n\n\n", result)

    def test_blank_line_before_heading_when_prev_bullet_has_trailing_spaces(self):
        text = "• Last bullet  \n## v2.0\n• New bullet"
        result = normalize_mod.normalize(text)
        self.assertIn("\n\n## v2.0", result)

    def test_main_normalizes_file_in_place(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.md"
            path.write_text("## v1.0\n• First\n• Second\n", encoding="utf-8")

            with mock.patch.object(sys, "argv", ["prog", str(path)]):
                normalize_mod.main()

            result = path.read_text(encoding="utf-8")
            self.assertIn("## v1.0\n\n", result)
            self.assertTrue(result.endswith("\n"))
            for line in result.split("\n"):
                if line.startswith("•"):
                    self.assertTrue(line.endswith("  "))

    def test_main_filters_before_normalizing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.md"
            path.write_text(
                "## v1.0\n"
                "• Added login\n"
                "• Update some dependencies (none)\n"
                "• Fixed logout\n",
                encoding="utf-8",
            )

            with mock.patch.object(sys, "argv", ["prog", str(path)]):
                normalize_mod.main()

            result = path.read_text(encoding="utf-8")
            self.assertIn("• Added login  ", result)
            self.assertIn("• Fixed logout  ", result)
            self.assertNotIn("Update some dependencies (none)", result)


if __name__ == "__main__":
    unittest.main()
