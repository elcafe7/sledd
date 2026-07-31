# sledd

PowerPoint-style presentations that run entirely in your terminal. Decks are plain Markdown, rendering is handled by [Rich](https://github.com/Textualize/rich), and the only runtime dependency is `rich`.

## Quick start

```sh
git clone https://github.com/elcafe7/sledd.git
cd sledd
uv sync
uv run sledd
uv run sledd --init demo.md
uv run sledd demo.md
```

Running bare `sledd` opens a fullscreen menu. Use `↑` / `↓` to highlight, `Enter` to choose, and `Esc` to quit. Menu actions: **Demo deck**, **Open deck** (type a path), **This folder** (arrow-pick a `.md` from the current directory), **Recent decks** (last eight, stored in `~/.config/sledd/recent.json`), **New deck**, **Quick guide**, and **Quit**.

Choose **Demo deck** in the menu—or run `sledd --demo`—for a seven-slide literary presentation.

Presentation mode is deliberately minimal: one centered block of text per slide, no borders, no headers, no slide counters. Controls: `←` / `→` navigate, `q` or `Esc` returns to the menu, and `Esc` again (or `q`) quits from the menu. Slides reflow live when `Cmd +` / `Cmd -` changes the terminal size; sledd does not alter the terminal font itself.

To install the command globally from this checkout:

```sh
uv tool install .
sledd --init talk.md
sledd talk.md
```

## Deck format

Slides are Markdown blocks separated by a line containing exactly `---`:

````markdown
<!-- sledd
title: Shipping the tiny thing
author: Ada Lovelace
theme: ocean
-->

# Shipping the tiny thing

## A terminal-native story

<!-- notes
Pause here. This text is hidden unless --notes is used.
-->

---

# The plan

- Keep the format readable
- Make automation deterministic
- Export when a terminal is not enough

---

# The code

```python
print("hello from a slide")
```
````

The optional `sledd` comment must be at the very beginning. Supported fields are `title`, `author`, and `theme`. Themes are `ocean`, `ember`, `forest`, and `mono`.

Speaker notes use an HTML comment beginning with `notes` on its own line. They remain in the source but are hidden during a normal presentation. Because `---` is the slide delimiter, use `***` if you need a horizontal rule inside a slide.

Rendering is intentionally plain: Markdown syntax is stripped, not typeset. Headings become plain lines, lists and emphasis are flattened, and tables collapse to space-separated text. No borders, headers, or counters — each slide is just its text, centered both horizontally and vertically on the stage.

## Commands

```sh
# Open the interactive launch menu
sledd

# Run the bundled seven-slide demo
sledd --demo

# Inspect that demo without a TTY
sledd --demo --print --no-color

# Present interactively
sledd talk.md

# Show speaker notes
sledd talk.md --notes

# Render all slides to stdout (CI- and agent-friendly)
sledd talk.md --print --no-color

# Export one SVG per slide
sledd talk.md --export-svg ./exports

# Override deck settings
sledd talk.md --theme ember --width 120

# Create or replace a starter deck
sledd --init talk.md
sledd --init talk.md --force
```

Interactive mode requires a TTY. Piped commands should use `--print`; image-producing workflows should use `--export-svg DIR`.

## Instructions for AI CLI agents

This repository is deliberately agent-readable. Give an AI CLI this section or point it at this README.

**Contract:**

1. Read the entire existing `.md` deck before editing it.
2. Preserve the leading `<!-- sledd ... -->` metadata block.
3. Treat a line containing exactly `---` as the only slide boundary.
4. Keep each slide focused on one idea. Prefer one heading and at most 3–5 bullets.
5. Put narration in `<!-- notes ... -->`, not in visible slide content.
6. Do not put `---` inside code fences; use `***` for visible horizontal rules.
7. Validate non-interactively with `sledd DECK.md --print --no-color`.
8. For a visual artifact, run `sledd DECK.md --export-svg OUTPUT_DIR` and report the generated paths.

A useful agent prompt:

```text
Create a concise 7-slide deck at launch.md using the sledd format in
README.md. Use theme ocean, include speaker notes, keep each slide to one idea,
then validate it with `uv run sledd launch.md --print --no-color`.
Do not install globally and do not modify source code.
```

For automated deck generation, write UTF-8 Markdown directly. There is no hidden database, binary format, or network call. A successful validation exits `0`; parse and file errors exit `2`.

## Development

```sh
uv sync --dev
uv run pytest
uv run sledd --init /tmp/demo.md --force
uv run sledd /tmp/demo.md --print --no-color
```

The project uses a `src/` package layout. Parsing lives in `deck.py`, Rich rendering in `render.py`, and terminal/CLI behavior in `cli.py`.

## License

MIT
