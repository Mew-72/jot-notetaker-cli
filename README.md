# Jot 📝

A simple, fast, and beautiful command-line note-taking utility and interactive Text User Interface (TUI) designed for developer-speed brainstorming, logging, and scratchpad needs.

---

## ✨ Features

- **⚡ Fast Entry:** Type `jot "Your note here"` to instantly save a note. No unnecessary flags or subcommands required.
- **📊 Rich Terminal Output:** View notes in clean, structured tables and panels powered by [Rich](https://github.com/Textualize/rich).
- **🖥️ Full-featured TUI:** Run `jot tui` to open a full-featured terminal workspace powered by [Textual](https://github.com/Textualize/textual). Search, filter, view, edit, and delete notes dynamically.
- **📁 Persistent Storage:** Notes are kept in a simple JSON structure in your home directory (`~/.cli_notes.json`).

---

## 🚀 Installation

Ensure you have Python 3.11 or later installed.

### Using `uv` (Recommended)

```bash
# Clone the repository
git clone https://github.com/Mew-72/jot-notetaker-cli.git
cd jot-notetaker-cli

# Install dependencies and build project
uv pip install .
```

### Using standard `pip`

```bash
# Clone the repository
git clone https://github.com/Mew-72/jot-notetaker-cli.git
cd jot-notetaker-cli

# Install package
pip install .
```

---

## 🛠️ CLI Usage

```bash
# Quick addition (defaults to add subcommand)
jot "Revise the system prompt guidelines before deploying"

# Explicitly add a note
jot add "Water the plants"

# View all saved notes in a table
jot view

# Search notes for keywords
jot search "system prompt"

# Clear all notes
jot clear

# Launch interactive Text User Interface (TUI)
jot tui
```

---

## 🎮 TUI Keybindings & Controls

When running `jot tui`, the following hotkeys are available:

| Key | Action |
| --- | --- |
| `n` | Create a new note |
| `Enter` | Open selected note details / edit / delete screen |
| `d` | Delete selected note |
| `Escape` | Clear current search query |
| `Ctrl + S` | Save note (inside note editor screen) |
| `Ctrl + Q` | Quit the application |

---
