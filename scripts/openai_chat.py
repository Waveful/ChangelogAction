#!/usr/bin/env python3

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def read_text(path):
    return Path(path).read_text(encoding="utf-8").strip()


def build_url(base_url):
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def extract_message_text(response_json):
    choices = response_json.get("choices") or []
    if choices:
        choice = choices[0] or {}
        message = choice.get("message") or {}
        content = message.get("content")

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            if parts:
                return "".join(parts)

        text = choice.get("text")
        if isinstance(text, str):
            return text

    output = response_json.get("output") or []
    if isinstance(output, list):
        parts = []
        for block in output:
            if not isinstance(block, dict):
                continue
            for item in block.get("content") or []:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return "".join(parts)

    raise ValueError("Unable to extract a text response from the provider payload.")


def main():
    parser = argparse.ArgumentParser(description="Call an OpenAI-compatible chat endpoint.")
    parser.add_argument("--system-prompt-file", required=True)
    parser.add_argument("--user-prompt-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()
    temperature = os.environ.get("OPENAI_TEMPERATURE", "0.2").strip()
    auth_header = os.environ.get("OPENAI_AUTH_HEADER", "Authorization").strip()
    auth_prefix = os.environ.get("OPENAI_AUTH_PREFIX", "Bearer ")

    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required.")

    if not model:
        raise SystemExit("OPENAI_MODEL is required.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": read_text(args.system_prompt_file)},
            {"role": "user", "content": read_text(args.user_prompt_file)},
        ],
        "temperature": float(temperature),
    }

    request = urllib.request.Request(
        build_url(base_url),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            auth_header: f"{auth_prefix}{api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_json = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(error_body, file=sys.stderr)
        raise SystemExit(f"LLM request failed with HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Unable to reach the configured LLM endpoint: {exc.reason}") from exc

    message = extract_message_text(response_json).strip()
    if not message:
        raise SystemExit("The configured LLM endpoint returned an empty response.")

    Path(args.output_file).write_text(message + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
