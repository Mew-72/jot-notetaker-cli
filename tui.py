import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable, TextArea, Input, Button, ListView, ListItem, Label
from textual.containers import Vertical, Horizontal, Center
from textual.events import Key

FILENAME = ".cli_notes.json"
FILEPATH = Path.home() / FILENAME


class Note(BaseModel):
    content: str
    created_at: datetime = Field(default_factory=datetime.now)


def load_notes():
    if not FILEPATH.exists():
        return []
    try:
        with open(FILEPATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Note.model_validate(item) for item in data]
    except Exception:
        return []


def save_notes(notes):
    with open(FILEPATH, "w", encoding="utf-8") as f:
        json.dump([note.model_dump(mode="json") for note in notes], f, indent=2)


class ConfirmDialog(Screen):
    CSS = """
    ConfirmDialog { align: center middle; }
    #confirm-box { width: 50; height: auto; padding: 1 2; background: $surface; border: tall $primary; }
    #confirm-msg { margin: 0 0 1 0; text-align: center; }
    #confirm-btns { align: center middle; height: auto; }
    Button { margin: 0 1; }
    """

    BINDINGS = [Binding("escape", "no", "No"), Binding("y", "yes", "Yes"), Binding("n", "no", "No")]

    def __init__(self, message):
        super().__init__()
        self.message = message

    def compose(self):
        with Vertical(id="confirm-box"):
            yield Static(self.message, id="confirm-msg")
            with Horizontal(id="confirm-btns"):
                yield Button("Yes", variant="error", id="yes")
                yield Button("No", variant="primary", id="no")

    def action_yes(self):
        self.dismiss(True)

    def action_no(self):
        self.dismiss(False)

    def on_button_pressed(self, event):
        self.dismiss(event.button.id == "yes")


class EditorScreen(Screen):
    CSS = """
    EditorScreen { padding: 1 2; }
    #editor-title { dock: top; padding: 0 0 1 0; text-style: bold; color: $primary; }
    #note-body { height: 1fr; margin: 0 0 1 0; }
    #note-tags { dock: bottom; }
    #editor-help { dock: bottom; color: $text-muted; padding: 0 0 1 0; }
    """

    def __init__(self, content="", tags=""):
        super().__init__()
        self.initial_content = content
        self.initial_tags = tags

    def compose(self):
        with Vertical():
            yield Static("Edit Note" if self.initial_content else "New Note", id="editor-title")
            yield TextArea(self.initial_content, id="note-body")
            yield Input(value=self.initial_tags, placeholder="Tags (comma-separated)", id="note-tags")
            yield Static("Ctrl+S: Save | Escape: Cancel", id="editor-help")

    def on_key(self, event):
        if event.key == "ctrl+s":
            event.stop()
            self._save()

    def _save(self):
        content = self.query_one("#note-body", TextArea).text.strip()
        if not content:
            self.notify("Note cannot be empty!", severity="warning")
            return
        tags = self.query_one("#note-tags", Input).value.strip()
        self.dismiss({"content": content, "tags": tags})

    def action_cancel(self):
        self.dismiss(None)


class NoteDetailScreen(Screen):
    CSS = """
    NoteDetailScreen { padding: 1 2; }
    #detail-header { dock: top; text-style: bold; color: $primary; padding: 0 0 1 0; }
    #detail-meta { dock: top; color: $text-muted; padding: 0 0 1 0; }
    #detail-content { height: 1fr; padding: 0 0 1 0; }
    #detail-help { dock: bottom; color: $text-muted; }
    """

    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("d", "delete", "Delete"),
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self, note, index):
        super().__init__()
        self.note = note
        self.index = index

    def compose(self):
        with Vertical():
            yield Static(f"Note #{self.index + 1}", id="detail-header")
            yield Static(self.note.created_at.strftime("%Y-%m-%d %H:%M:%S"), id="detail-meta")
            yield Static(self.note.content, id="detail-content")
            yield Static("e: Edit | d: Delete | Esc: Back", id="detail-help")

    def action_edit(self):
        self.run_worker(self._edit())

    async def _edit(self):
        tags = ", ".join(getattr(self.note, "tags", [])) if hasattr(self.note, "tags") else ""
        result = await self.app.push_screen_wait(EditorScreen(self.note.content, tags))
        if result:
            notes = load_notes()
            if self.index < len(notes):
                notes[self.index].content = result["content"]
                save_notes(notes)
                self.notify("Note updated!")
                self.app.pop_screen()

    def action_delete(self):
        self.run_worker(self._delete())

    async def _delete(self):
        result = await self.app.push_screen_wait(ConfirmDialog("Delete this note?"))
        if result:
            notes = load_notes()
            if self.index < len(notes):
                notes.pop(self.index)
                save_notes(notes)
                self.notify("Note deleted!")
                self.app.pop_screen()

    def action_go_back(self):
        self.app.pop_screen()


class ListScreen(Screen):
    CSS = """
    ListScreen { layout: vertical; }
    #search-bar { dock: top; height: 3; padding: 0 0 1 0; }
    #search-input { width: 100%; }
    #note-list { height: 1fr; }
    #status-bar { dock: bottom; height: 1; color: $text-muted; }
    #help-bar { dock: bottom; height: 1; color: $text-muted; }
    """

    BINDINGS = [
        Binding("n", "new_note", "New"),
        Binding("enter", "open_note", "Open"),
        Binding("d", "delete_note", "Delete"),
        Binding("escape", "clear_search", "Clear"),
    ]

    def compose(self):
        with Vertical():
            with Horizontal(id="search-bar"):
                yield Input(placeholder="Search notes...", id="search-input")
            yield DataTable(id="note-list")
            yield Static("", id="status-bar")
            yield Static("n: New | Enter: Open | d: Delete | Esc: Clear", id="help-bar")

    def on_mount(self):
        table = self.query_one("#note-list", DataTable)
        table.add_columns("#", "Content", "Created")
        table.cursor_type = "row"
        self.refresh_list()

    def refresh_list(self):
        query = self.query_one("#search-input", Input).value.lower()
        notes = load_notes()
        if query:
            notes = [n for n in notes if query in n.content.lower()]

        table = self.query_one("#note-list", DataTable)
        table.clear()
        for i, note in enumerate(notes):
            created = note.created_at.strftime("%Y-%m-%d %H:%M")
            content = note.content[:50] + "..." if len(note.content) > 50 else note.content
            table.add_row(str(i + 1), content, created)

        self.query_one("#status-bar", Static).update(f"Notes: {len(notes)}")

    def on_input_changed(self, event):
        if event.input.id == "search-input":
            self.refresh_list()

    def _get_selected_index(self):
        table = self.query_one("#note-list", DataTable)
        if table.cursor_row is None:
            return None
        query = self.query_one("#search-input", Input).value.lower()
        notes = load_notes()
        if query:
            notes = [n for n in notes if query in n.content.lower()]
        if table.cursor_row < len(notes):
            return load_notes().index(notes[table.cursor_row])
        return None

    def action_new_note(self):
        self.run_worker(self._new_note())

    async def _new_note(self):
        result = await self.app.push_screen_wait(EditorScreen())
        if result:
            notes = load_notes()
            tags = [t.strip() for t in result["tags"].split(",") if t.strip()] if result["tags"] else []
            note = Note(content=result["content"])
            if tags:
                note.tags = tags
            notes.append(note)
            save_notes(notes)
            self.refresh_list()

    def action_open_note(self):
        idx = self._get_selected_index()
        if idx is not None:
            notes = load_notes()
            if idx < len(notes):
                self.app.push_screen(NoteDetailScreen(notes[idx], idx))

    def action_delete_note(self):
        idx = self._get_selected_index()
        if idx is not None:
            self.run_worker(self._delete_note(idx))

    async def _delete_note(self, idx):
        notes = load_notes()
        if idx < len(notes):
            result = await self.app.push_screen_wait(ConfirmDialog(f"Delete: {notes[idx].content[:30]}...?"))
            if result:
                notes.pop(idx)
                save_notes(notes)
                self.notify("Note deleted!")
                self.refresh_list()

    def action_clear_search(self):
        self.query_one("#search-input", Input).value = ""
        self.refresh_list()


class JotApp(App):
    TITLE = "Jot"
    SUB_TITLE = "Your notes"
    CSS_PATH = "styles.tcss"

    BINDINGS = [Binding("ctrl+q", "quit", "Quit", priority=True)]

    def compose(self):
        yield Header()
        yield Footer()

    def on_mount(self):
        self.push_screen(ListScreen())


if __name__ == "__main__":
    JotApp().run()
