import sqlite3
from datetime import datetime

DB_NAME = "notes.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self._create_table()

    def _create_table(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT,
                content    TEXT,
                pinned     INTEGER DEFAULT 0,
                updated_at TEXT
            )
        """)
        self.conn.commit()

    # ------------------------------------------------------------------ #
    #  READ
    # ------------------------------------------------------------------ #
    def fetch_notes(self, search=""):
        """Return all notes matching *search* in title or content.
        Pinned notes appear first, then ordered by most recently updated."""
        pattern = f"%{search}%"
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, title, pinned
            FROM   notes
            WHERE  title LIKE ? OR content LIKE ?
            ORDER  BY pinned DESC, updated_at DESC
        """, (pattern, pattern))
        return cur.fetchall()   # list of (id, title, pinned)

    def fetch_note(self, note_id):
        """Return (title, content) for a single note."""
        cur = self.conn.cursor()
        cur.execute("SELECT title, content FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    # ------------------------------------------------------------------ #
    #  WRITE
    # ------------------------------------------------------------------ #
    def insert_note(self, title, content):
        """Insert a new note and return its new id."""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO notes (title, content, updated_at)
            VALUES (?, ?, ?)
        """, (title, content, datetime.now().isoformat()))
        self.conn.commit()
        return cur.lastrowid

    def update_note(self, note_id, title, content):
        """Update title and content of an existing note."""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE notes
            SET title=?, content=?, updated_at=?
            WHERE id=?
        """, (title, content, datetime.now().isoformat(), note_id))
        self.conn.commit()

    def delete_note(self, note_id):
        """Permanently delete a note."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM notes WHERE id=?", (note_id,))
        self.conn.commit()

    def toggle_pin(self, note_id):
        """Flip the pinned flag for a note."""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE notes
            SET pinned = CASE pinned WHEN 1 THEN 0 ELSE 1 END
            WHERE id = ?
        """, (note_id,))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    #  CLEANUP
    # ------------------------------------------------------------------ #
    def close(self):
        self.conn.close()