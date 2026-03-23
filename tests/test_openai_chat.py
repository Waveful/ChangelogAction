import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "openai_chat.py"


def load_module():
    spec = importlib.util.spec_from_file_location("openai_chat", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


openai_chat = load_module()


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OpenAIChatTests(unittest.TestCase):
    def test_build_url_appends_chat_completions(self):
        self.assertEqual(
            openai_chat.build_url("https://example.com/v1"),
            "https://example.com/v1/chat/completions",
        )

    def test_build_url_keeps_existing_chat_completions_endpoint(self):
        self.assertEqual(
            openai_chat.build_url("https://example.com/v1/chat/completions"),
            "https://example.com/v1/chat/completions",
        )

    def test_extract_message_text_supports_multiple_response_shapes(self):
        self.assertEqual(
            openai_chat.extract_message_text(
                {"choices": [{"message": {"content": "first response"}}]}
            ),
            "first response",
        )

        self.assertEqual(
            openai_chat.extract_message_text(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {"type": "output_text", "text": "hello "},
                                    {"type": "output_text", "text": "world"},
                                ]
                            }
                        }
                    ]
                }
            ),
            "hello world",
        )

        self.assertEqual(
            openai_chat.extract_message_text(
                {
                    "output": [
                        {
                            "content": [
                                {"type": "output_text", "text": "fallback "},
                                {"type": "output_text", "text": "format"},
                            ]
                        }
                    ]
                }
            ),
            "fallback format",
        )

    def test_main_posts_request_and_writes_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            system_prompt = temp_path / "system.txt"
            user_prompt = temp_path / "user.txt"
            output_file = temp_path / "output.txt"

            system_prompt.write_text("system prompt\n", encoding="utf-8")
            user_prompt.write_text("user prompt\n", encoding="utf-8")

            captured = {}

            def fake_urlopen(request):
                captured["url"] = request.full_url
                captured["headers"] = {
                    key.lower(): value for key, value in request.header_items()
                }
                captured["payload"] = json.loads(request.data.decode("utf-8"))
                return FakeResponse(
                    {"choices": [{"message": {"content": "## v1.2.3\n\u2022 Added support"}}]}
                )

            argv = [
                "openai_chat.py",
                "--system-prompt-file",
                str(system_prompt),
                "--user-prompt-file",
                str(user_prompt),
                "--output-file",
                str(output_file),
            ]

            env = {
                "OPENAI_BASE_URL": "https://provider.example/v1",
                "OPENAI_API_KEY": "secret-key",
                "OPENAI_MODEL": "test-model",
                "OPENAI_TEMPERATURE": "0.7",
                "OPENAI_AUTH_HEADER": "api-key",
                "OPENAI_AUTH_PREFIX": "",
            }

            with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(
                sys, "argv", argv
            ), mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
                openai_chat.main()

            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                "## v1.2.3\n\u2022 Added support\n",
            )
            self.assertEqual(
                captured["url"],
                "https://provider.example/v1/chat/completions",
            )
            self.assertEqual(captured["headers"]["api-key"], "secret-key")
            self.assertEqual(captured["payload"]["model"], "test-model")
            self.assertEqual(captured["payload"]["temperature"], 0.7)
            self.assertEqual(
                captured["payload"]["messages"],
                [
                    {"role": "system", "content": "system prompt"},
                    {"role": "user", "content": "user prompt"},
                ],
            )

    def test_main_requires_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            system_prompt = temp_path / "system.txt"
            user_prompt = temp_path / "user.txt"
            output_file = temp_path / "output.txt"

            system_prompt.write_text("system prompt", encoding="utf-8")
            user_prompt.write_text("user prompt", encoding="utf-8")

            argv = [
                "openai_chat.py",
                "--system-prompt-file",
                str(system_prompt),
                "--user-prompt-file",
                str(user_prompt),
                "--output-file",
                str(output_file),
            ]

            with mock.patch.dict(os.environ, {"OPENAI_MODEL": "test-model"}, clear=True), mock.patch.object(
                sys, "argv", argv
            ):
                with self.assertRaises(SystemExit) as error:
                    openai_chat.main()

            self.assertEqual(str(error.exception), "OPENAI_API_KEY is required.")


if __name__ == "__main__":
    unittest.main()
