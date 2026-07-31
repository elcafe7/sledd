"""Command-line interface for sledd."""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.align import Align
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.terminal_theme import MONOKAI

from . import __version__
from .deck import Deck, load_deck
from .render import THEMES, render_slide


RECENT_LIMIT = 8
RECENT_FILE = Path.home() / ".config" / "sledd" / "recent.json"


SAMPLE = """<!-- sledd
title: Terminal-native presentations
author: Your name
theme: ocean
-->

# Rich Slides

## PowerPoint energy, terminal ergonomics

Write **Markdown**. Present it with one command.

<!-- notes
Welcome everyone and keep this opening short.
-->

---

# What works

- Headings, lists, links, and quotes
- `inline code` and fenced code blocks
- Speaker notes hidden from the audience
- SVG export for sharing

> The deck is just a text file, so people and agents can edit it.

---

# A tiny demo

```python
from rich.console import Console

Console().print("[bold cyan]Hello, slides![/]")
```

## Questions?
"""


@dataclass
class MenuItem:
    label: str
    description: str
    action: str


MENU_ITEMS: list[MenuItem] = [
    MenuItem("Demo deck", "see the look and feel", "demo"),
    MenuItem("Open deck", "present a markdown file", "open"),
    MenuItem("This folder", "pick a .md from here", "folder"),
    MenuItem("Recent decks", "return to a previous show", "recent"),
    MenuItem("New deck", "write a fresh template", "new"),
    MenuItem("Quick guide", "learn the format", "guide"),
    MenuItem("Quit", "return to the shell", "quit"),
]


def _read_key() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    prev = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key == "\x1b":
            key += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, prev)
    return key


def _render_menu(console: Console, items: list[MenuItem], selected: int, info: str = "") -> None:
    console.clear()
    lines: list[Text] = [
        Text("sledd.", style="bold bright_white", justify="center"),
        Text("present ideas. nothing else.", style="grey62", justify="center"),
        Text(),
    ]
    for i, item in enumerate(items):
        cursor = "[bold cyan]  \u25b6 [/]" if i == selected else "    "
        line = Text(justify="center")
        line.append(cursor, style="bold cyan")
        line.append(item.label, style="bold bright_white")
        line.append(f"  \u2014  {item.description}", style="grey62")
        lines.append(line)
    lines.extend([Text(), Text(info, style="grey42", justify="center"), Text()])
    console.print(Align.center(Group(*lines)))


def _run_menu(console: Console, no_color: bool) -> None:
    items = MENU_ITEMS
    selected = 0
    _render_menu(console, items, selected)
    try:
        while True:
            key = _read_key()
            if key in ("q", "\x1b", "\x03"):
                console.clear()
                return
            if key == "\x1b[A":
                selected = (selected - 1) % len(items)
                _render_menu(console, items, selected)
            elif key == "\x1b[B":
                selected = (selected + 1) % len(items)
                _render_menu(console, items, selected)
            elif key in ("\r", "\n"):
                action = items[selected].action
                if action == "quit":
                    console.clear()
                    return
                try:
                    _handle_action(console, action, no_color)
                except (OSError, ValueError, RuntimeError) as error:
                    console.clear()
                    console.print(Align.center(Text(f"error: {error}", style="bold red")))
                    Prompt.ask("", default="", show_default=False, console=console)
                _render_menu(console, items, selected)
    except KeyboardInterrupt:
        console.clear()


def _handle_action(console: Console, action: str, no_color: bool) -> None:
    if action == "demo":
        deck = load_deck(Path(__file__).with_name("cat_in_the_hat_demo.md"))
        present(deck, _theme(deck, None), False, no_color)
        return
    if action == "open":
        path = Prompt.ask("path", default="talk.md", console=console)
        path = Path(path).expanduser()
        deck = load_deck(path)
        _remember(path)
        present(deck, _theme(deck, None), False, no_color)
        return
    if action == "folder":
        root = Path.cwd()
        decks = sorted(
            p for p in root.iterdir()
            if p.is_file() and p.suffix.lower() == ".md" and not p.name.startswith(".")
        )
        if not decks:
            console.clear()
            console.print(Align.center(Text(f"no .md files in {root}", style="grey62")))
            Prompt.ask("", default="", show_default=False, console=console)
            return
        selected = 0
        while True:
            console.clear()
            console.print(Align.center(Text("this folder", style="bold bright_white")))
            console.print(Align.center(Text(str(root), style="grey42")))
            console.print()
            for i, p in enumerate(decks):
                mark = "[bold cyan]\u25b6[/] " if i == selected else "  "
                console.print(Align.center(Text.from_markup(f"{mark}{p.name}")))
            key = _read_key()
            if key in ("q", "\x1b", "\x03"):
                return
            if key == "\x1b[A":
                selected = (selected - 1) % len(decks)
            elif key == "\x1b[B":
                selected = (selected + 1) % len(decks)
            elif key in ("\r", "\n"):
                deck = load_deck(decks[selected])
                _remember(decks[selected])
                present(deck, _theme(deck, None), False, no_color)
                return
        return
    if action == "recent":
        try:
            decks = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            decks = []
        if not isinstance(decks, list):
            decks = []
        paths = []
        for v in decks:
            p = Path(v).expanduser() if isinstance(v, str) else None
            if p and p.is_file():
                paths.append(p)
        paths = paths[:RECENT_LIMIT]
        if not paths:
            console.clear()
            console.print(Align.center(Text("no recent decks", style="grey62")))
            Prompt.ask("", default="", show_default=False, console=console)
            return
        selected = 0
        while True:
            console.clear()
            console.print(Align.center(Text("recent decks", style="bold bright_white")))
            console.print()
            for i, p in enumerate(paths):
                mark = "[bold cyan]\u25b6[/] " if i == selected else "  "
                console.print(Align.center(Text.from_markup(f"{mark}{p.stem}")))
                console.print(Align.center(Text(str(p), style="grey42")))
            key = _read_key()
            if key in ("q", "\x1b", "\x03"):
                return
            if key == "\x1b[A":
                selected = (selected - 1) % len(paths)
            elif key == "\x1b[B":
                selected = (selected + 1) % len(paths)
            elif key in ("\r", "\n"):
                deck = load_deck(paths[selected])
                _remember(paths[selected])
                present(deck, _theme(deck, None), False, no_color)
                return
        return
    if action == "new":
        path = Prompt.ask("new deck path", default="talk.md", console=console)
        path = Path(path).expanduser()
        force = path.exists() and Confirm.ask(
            f"replace {path}?", default=False, console=console
        )
        if path.exists() and not force:
            return
        init_deck(path, force)
        return
    if action == "guide":
        console.clear()
        console.print(Align.center(Text("sledd quick guide", style="bold bright_white")))
        console.print()
        console.print(Align.center(Markdown("""```markdown
<!-- sledd
title: My talk
theme: ocean
-->

# One idea

- Keep it concise

---

# The next idea
```

**Navigate:** `\u2190` back \u00b7 `\u2192` forward \u00b7 `Esc` exit
""", code_theme="monokai", justify="center")))
        console.print()
        console.print(Align.center(Text("Full docs in README.md", style="grey62")))
        Prompt.ask("", default="", show_default=False, console=console)
        return


def demo_deck_path() -> Path:
    return Path(__file__).with_name("cat_in_the_hat_demo.md")


def _remember(path: Path) -> None:
    resolved = path.expanduser().resolve()
    if not resolved.is_file() or resolved == demo_deck_path().resolve():
        return
    try:
        decks = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        decks = []
    if not isinstance(decks, list):
        decks = []
    decks = [str(resolved), *(v for v in decks if Path(v).expanduser().resolve() != resolved)]
    RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECENT_FILE.write_text(json.dumps(decks[:RECENT_LIMIT], indent=2) + "\n", encoding="utf-8")


def launch_menu(*, no_color: bool = False) -> int:
    console = Console(no_color=no_color)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        console.print("[grey62]Interactive menu needs a TTY. Run sledd --help for options.[/]")
        return 0
    _run_menu(console, no_color)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="sledd",
        description="Present Markdown slide decks in the terminal.",
    )
    result.add_argument("deck", nargs="?", type=Path, help="Markdown deck to present")
    result.add_argument("--demo", action="store_true", help="present the bundled seven-slide demo")
    result.add_argument("--theme", choices=sorted(THEMES), help="override the deck theme")
    result.add_argument("--notes", action="store_true", help="show speaker notes")
    result.add_argument("--print", dest="print_all", action="store_true", help="render every slide without interaction")
    result.add_argument("--export-svg", metavar="DIR", type=Path, help="export each slide as SVG")
    result.add_argument("--init", metavar="PATH", type=Path, help="write a sample deck and exit")
    result.add_argument("--force", action="store_true", help="overwrite an existing file with --init")
    result.add_argument("--width", type=int, default=100, help="output width for print/export (default: 100)")
    result.add_argument("--no-color", action="store_true", help="disable color")
    result.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return result


def _theme(deck: Deck, override: str | None) -> str:
    selected = override or deck.theme
    if selected not in THEMES:
        choices = ", ".join(sorted(THEMES))
        raise ValueError(f"unknown theme {selected!r}; choose one of: {choices}")
    return selected


def init_deck(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {path}; pass --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SAMPLE, encoding="utf-8")


def print_deck(deck: Deck, theme: str, notes: bool, width: int, no_color: bool) -> None:
    console = Console(width=width, no_color=no_color)
    for index in range(len(deck)):
        if index:
            console.print("\n")
        console.print(
            render_slide(
                deck,
                index,
                theme_name=theme,
                show_notes=notes,
                navigation=False,
                width=width,
            )
        )


def export_deck(deck: Deck, directory: Path, theme: str, notes: bool, width: int) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    digits = len(str(len(deck)))
    for index in range(len(deck)):
        console = Console(record=True, width=width, force_terminal=True, file=io.StringIO())
        console.print(
            render_slide(
                deck,
                index,
                theme_name=theme,
                show_notes=notes,
                navigation=False,
                width=width,
                height=30,
            )
        )
        output = directory / f"slide-{index + 1:0{digits}d}.svg"
        console.save_svg(str(output), theme=MONOKAI, clear=True)


def present(deck: Deck, theme: str, notes: bool, no_color: bool) -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("interactive mode needs a TTY; use --print or --export-svg")
    console = Console(no_color=no_color)
    index = 0

    def show():
        console.clear()
        console.print(render_slide(deck, index, theme_name=theme, show_notes=notes, width=console.width, height=max(console.height - 1, 1)))

    show()
    try:
        while True:
            key = _read_key()
            if key in ("q", "\x1b", "\x03"):
                break
            if key in ("\x1b[C", "l"):
                index = min(index + 1, len(deck) - 1)
                show()
            elif key in ("\x1b[D", "h"):
                index = max(index - 1, 0)
                show()
    except KeyboardInterrupt:
        pass
    console.clear()


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[1:] if argv is None else argv
    args = parser().parse_args(raw_args)
    console = Console(stderr=True)
    try:
        if not raw_args:
            return launch_menu()
        if args.init:
            init_deck(args.init, args.force)
            console.print(f"Created [bold]{args.init}[/]")
            return 0
        if args.demo and args.deck:
            raise ValueError("pass either a deck path or --demo, not both")
        if not args.deck and not args.demo:
            parser().error("a deck path is required (or use --demo / run bare sledd)")
        if args.width < 40:
            raise ValueError("--width must be at least 40")
        deck = load_deck(demo_deck_path() if args.demo else args.deck)
        theme = _theme(deck, args.theme)
        if args.export_svg:
            export_deck(deck, args.export_svg, theme, args.notes, args.width)
            console.print(f"Exported {len(deck)} slides to [bold]{args.export_svg}[/]")
        elif args.print_all:
            print_deck(deck, theme, args.notes, args.width, args.no_color)
        else:
            if not args.demo and args.deck is not None:
                _remember(args.deck)
            present(deck, theme, args.notes, args.no_color)
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        console.print(f"[bold red]error:[/] {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
