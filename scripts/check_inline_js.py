#!/usr/bin/env python3
"""Static checks for the single-file Sportscenter application."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile


class ScriptCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inline_scripts = []
        self._capture = False
        self._current = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self._capture = not any(name.lower() == "src" for name, _ in attrs)
            self._current = []

    def handle_data(self, data):
        if self._capture:
            self._current.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self._capture:
            self.inline_scripts.append("".join(self._current))
            self._capture = False
            self._current = []


def main():
    html_path = Path(__file__).resolve().parents[1] / "index.html"
    html = html_path.read_text(encoding="utf-8")

    required = {
        "Sportscenter page title": "<title>Sportscenter</title>",
        "Original Over 1.5–2.5 analysis tab": "Over 1,5–2,5 · forventede odds",
        "Fair expected odds for both goal lines": "Forventede odds · Over 1,5 og Over 2,5",
        "Supabase setup reference": "fodboldcenter_supabase_setup.sql",
    }
    missing = [label for label, needle in required.items() if needle not in html]
    if missing:
        raise SystemExit("Missing required app features: " + ", ".join(missing))

    parser = ScriptCollector()
    parser.feed(html)
    if not parser.inline_scripts:
        raise SystemExit("No inline application JavaScript found.")

    for index, source in enumerate(parser.inline_scripts, start=1):
        if not source.strip():
            continue
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", encoding="utf-8"
        ) as temp:
            temp.write(source)
            temp.flush()
            result = subprocess.run(
                ["node", "--check", temp.name],
                capture_output=True,
                text=True,
                check=False,
            )
        if result.returncode:
            raise SystemExit(
                f"Inline script {index} has a JavaScript syntax error:\n"
                + result.stderr
            )

    print(
        f"Static checks passed: {len(parser.inline_scripts)} inline script(s); "
        f"{len(required)} required feature markers."
    )


if __name__ == "__main__":
    main()
