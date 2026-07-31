"""Parse the intentionally small sledd Markdown format."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


SEPARATOR = re.compile(r"^---\s*$", re.MULTILINE)
NOTES = re.compile(r"\n?<!--\s*notes\s*\n(.*?)\n\s*-->\s*", re.DOTALL | re.IGNORECASE)
CONFIG = re.compile(r"\A\s*<!--\s*sledd\s*\n(.*?)\n\s*-->\s*", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class Slide:
    markdown: str
    notes: str = ""


@dataclass(frozen=True)
class Deck:
    slides: tuple[Slide, ...]
    title: str
    author: str = ""
    theme: str = "ocean"

    def __len__(self) -> int:
        return len(self.slides)


def _config(text: str) -> tuple[dict[str, str], str]:
    match = CONFIG.match(text)
    if not match:
        return {}, text
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip():
            values[key.strip().lower()] = value.strip()
    return values, text[match.end() :]


def parse_deck(text: str, fallback_title: str = "Untitled deck") -> Deck:
    metadata, body = _config(text.replace("\r\n", "\n"))
    slides: list[Slide] = []
    for part in SEPARATOR.split(body):
        part = part.strip()
        if not part:
            continue
        note_match = NOTES.search(part)
        notes = note_match.group(1).strip() if note_match else ""
        markdown = NOTES.sub("", part).strip()
        if markdown:
            slides.append(Slide(markdown=markdown, notes=notes))
    if not slides:
        raise ValueError("deck contains no slides")
    return Deck(
        slides=tuple(slides),
        title=metadata.get("title", fallback_title),
        author=metadata.get("author", ""),
        theme=metadata.get("theme", "ocean"),
    )


def load_deck(path: Path) -> Deck:
    if not path.is_file():
        raise FileNotFoundError(f"deck not found: {path}")
    return parse_deck(path.read_text(encoding="utf-8"), fallback_title=path.stem)

