# NoteVault

A lightweight desktop notes manager built with Python and Tkinter.

## Features

- Create, edit, and delete notes
- Pin important notes to the top
- Full-text search across titles and content
- Live word and character count
- Export any note to PDF
- Dark / light mode toggle
- Auto-save every 5 minutes
- SQLite storage — no external server needed

## Project Structure

```
NoteVault/
├── main.py          # Entry point — launches the Tkinter window
├── database.py      # All SQLite read/write logic (Database class)
├── ui.py            # All UI logic (NotesManager class)
├── requirements.txt # Third-party dependencies
└── README.md        # This file
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `tkinter` ships with the standard Python distribution.
> If it is missing (some Linux systems), install it via your package manager:
> ```bash
> sudo apt install python3-tk   # Debian / Ubuntu
> sudo dnf install python3-tkinter  # Fedora
> ```

### 2. Run the app

```bash
python main.py
```

A `notes.db` SQLite file will be created automatically in the same directory on first run.

## Usage

| Action | How |
|--------|-----|
| New note | Click **New** |
| Save note | Click **Save** (or wait for auto-save) |
| Open note | Click any entry in the **Saved Notes** list |
| Delete note | Open a note, then click **Delete** |
| Pin / unpin | Open a note, then click **Pin/Unpin** |
| Export to PDF | Open a note, click **Export PDF**, choose save location |
| Search | Type in the **Search** box — list filters in real time |
| Toggle theme | Click **Dark Mode** |

## Requirements

- Python 3.8+
- reportlab