from pathlib import Path

import pytest
from rich.console import Console

from rich_slides.cli import deck_to_markdown, demo_deck_path, init_deck
from rich_slides.deck import load_deck, parse_deck
from rich_slides.render import render_slide


def test_parses_metadata_slides_and_notes() -> None:
    deck = parse_deck(
        """<!-- sledd
title: Demo
author: Ada
theme: ember
-->
# One
<!-- notes
Say hello.
-->
---
# Two
"""
    )

    assert deck.title == "Demo"
    assert deck.author == "Ada"
    assert deck.theme == "ember"
    assert len(deck) == 2
    assert deck.slides[0].notes == "Say hello."
    assert deck.slides[1].markdown == "# Two"


def test_rejects_empty_deck() -> None:
    with pytest.raises(ValueError, match="no slides"):
        parse_deck("\n---\n")


def test_init_does_not_overwrite_without_force(tmp_path: Path) -> None:
    path = tmp_path / "deck.md"
    init_deck(path, False)
    with pytest.raises(FileExistsError):
        init_deck(path, False)
    init_deck(path, True)


def test_slide_renders_with_rich() -> None:
    deck = parse_deck("# Hello\n\n- one\n- two")
    console = Console(record=True, width=80)
    console.print(render_slide(deck, 0, theme_name="ocean", width=80, height=20))

    rendered = console.export_text()
    assert "Hello" in rendered
    assert "\u256d" not in rendered


def test_slide_survives_a_zoomed_narrow_terminal() -> None:
    deck = parse_deck("# Still centered\n\nA short idea.")
    console = Console(record=True, width=24, height=8)
    console.print(render_slide(deck, 0, theme_name="mono", width=24, height=7))

    assert "Still" in console.export_text()


def test_demo_has_seven_slides_and_notes() -> None:
    deck = load_deck(demo_deck_path())

    assert len(deck) == 7
    assert deck.theme == "ember"
    assert all(slide.notes for slide in deck.slides)


def test_editor_serializes_one_line_per_slide() -> None:
    markdown = deck_to_markdown(["One idea", "", "Two ideas"], "My talk")
    deck = parse_deck(markdown)

    assert deck.title == "My talk"
    assert len(deck) == 2
    assert deck.slides[0].markdown == "# One idea"
    assert deck.slides[1].markdown == "# Two ideas"


def test_editor_empty_deck_writes_no_slides() -> None:
    markdown = deck_to_markdown(["", ""], "Empty")
    with pytest.raises(ValueError, match="no slides"):
        parse_deck(markdown)

