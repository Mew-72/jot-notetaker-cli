import argparse
import io
import json
import sys
from datetime import datetime
from json.decoder import JSONDecodeError
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from pydantic import BaseModel, Field

# --- Rich Imports ---
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(force_terminal=True)

FILENAME = ".cli_notes.json"
FILEPATH = Path.home() / FILENAME
KNOWN_COMMANDS = ["add", "view", "search", "clear", "tui", "-h", "--help"]


class Note(BaseModel):
    content: str = Field(..., description="The content of the note.")
    created_at: datetime = Field(default_factory=datetime.now)


def load_notes() -> list[Note]:
    if not FILEPATH.exists():
        return []

    try:
        with open(FILEPATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Note.model_validate(item) for item in data]
    except JSONDecodeError:
        return []


def save_notes(notes: list[Note]) -> None:
    with open(FILEPATH, "w", encoding="utf-8") as f:
        json.dump([note.model_dump(mode="json") for note in notes], f, indent=2)


def handle_add(args):
    try:
        notes = load_notes()
        new_note = Note(content=args.text)
        notes.append(new_note)
        save_notes(notes)
        console.print(
            f"[green]✔[/green]  Note added: [italic]{new_note.content}[/italic]"
        )
    except Exception as e:
        console.print(f"[red]✘  Error adding note:[/red] {e}")


def handle_search(args):
    try:
        notes = load_notes()
        if not notes:
            console.print("[yellow]⚠  Notes file is empty![/yellow]")
            return

        for idx, note in enumerate(notes, start=1):
            if args.text.lower() in note.content.lower():
                formatted_time = note.created_at.strftime("%Y-%m-%d %H:%M:%S")
                console.print(
                    Panel(
                        f"[magenta]{note.content}[/magenta]",
                        title=f"Match Found (Index {idx})",
                        subtitle=f"[dim]{formatted_time}[/dim]",
                        expand=False,
                    )
                )
                return
        console.print(
            f"[yellow]⚠  No notes matching '[bold]{args.text}[/bold]' found.[/yellow]"
        )
    except Exception as e:
        console.print(f"[red]✘  Error during search:[/red] {e}")


def handle_view(_):
    try:
        notes = load_notes()
        if not notes:
            console.print(
                "[yellow]⚠  No notes found. Type your note directly to add one![/yellow]"
            )
            return

        table = Table(
            title="📝 Your Saved Notes", show_header=True, header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Note Content", style="white")
        table.add_column("Created At", style="green", justify="center")

        for idx, note in enumerate(notes, start=1):
            formatted_time = note.created_at.strftime("%Y-%m-%d %H:%M:%S")
            table.add_row(str(idx), note.content, formatted_time)

        console.print(table)
    except Exception as e:
        console.print(f"[red]✘  Error viewing notes:[/red] {e}")


def confirm(prompt: str) -> bool:
    ans = (
        console.input(f"[bold yellow]❓ {prompt}[/bold yellow] [dim][y/N][/dim]: ")
        .strip()
        .lower()
    )
    return ans in ["y", "yes"]


def handle_delete_all(_):
    if not confirm("Are you absolutely sure you want to delete all notes? (y/N)"):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    save_notes([])
    console.print("[bold red]💣 All notes have been wiped clean.[/bold red]")


def handle_tui(_):
    from tui import JotApp

    app = JotApp()
    app.run()


def main():
    parser = argparse.ArgumentParser(
        prog="jot",
        description="A simple command-line tool for jotting down quick notes.",
        epilog="Example usage: jot 'Buy groceries'",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    parser_add = subparsers.add_parser("add", help="Add a new note...")
    parser_add.add_argument("text", type=str, help="The note content inside quotes")
    parser_add.set_defaults(func=handle_add)

    # view
    parser_view = subparsers.add_parser("view", help="Show all notes...")
    parser_view.set_defaults(func=handle_view)

    # search
    parser_search = subparsers.add_parser(
        "search", help="Search for a note. Shows the first matching note..."
    )
    parser_search.add_argument(
        "text", type=str, help="The keyword or text to search for"
    )
    parser_search.set_defaults(func=handle_search)

    # clear
    parser_del_all = subparsers.add_parser("clear", help="Delete all notes...")
    parser_del_all.set_defaults(func=handle_delete_all)

    # tui
    parser_tui = subparsers.add_parser("tui", help="Launch the interactive TUI...")
    parser_tui.set_defaults(func=handle_tui)

    # auto-add add to simple usage like: jot "buy groceries" instead of writing jot add "buy groceries"
    argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        return

    if argv[0] not in KNOWN_COMMANDS:
        argv = ["add", *argv]

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
