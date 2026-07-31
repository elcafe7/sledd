"""Rich renderables for presentation and export modes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rich.align import Align
from rich.console import Group
from rich.text import Text

from .deck import Deck


@dataclass(frozen=True)
class Theme:
    accent: str
    muted: str


THEMES: dict[str, Theme] = {
    "ocean": Theme("bold cyan", "grey62"),
    "ember": Theme("bold orange1", "grey62"),
    "forest": Theme("bold spring_green3", "grey62"),
    "mono": Theme("bold white", "grey70"),
}


def strip_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"``", "", text)
    return text.strip()


def _vcenter(text: str, width: int, height: int) -> Text:
    lines = text.split("\n")
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
        else:
            while len(line) > max(width - 4, 10):
                wrapped.append(line[: width - 4])
                line = line[width - 4 :]
            wrapped.append(line)
    text_height = len(wrapped)
    top = max(0, (height - text_height) // 2)
    bottom = max(0, height - text_height - top)
    result = "\n" * top + "\n".join(wrapped) + "\n" * bottom
    return Text(result, justify="center")


def render_slide(
    deck: Deck,
    index: int,
    *,
    theme_name: str,
    show_notes: bool = False,
    navigation: bool = True,
    width: int | None = None,
    height: int | None = None,
) -> Text | Align:
    slide = deck.slides[index]
    text = strip_md(slide.markdown)
    if height and width:
        return Align.center(_vcenter(text, width, height), width=width)
    return Align.center(Text(text, justify="center"), width=width or 100)
