import tkinter as tk
from tkinter import messagebox, filedialog
from reportlab.pdfgen import canvas

from database import Database


class NotesManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Personal Notes Manager")
        self.root.geometry("1000x600")

        self.dark_mode  = False
        self.current_id = None      # None = unsaved new note
        self.is_loading = False     # Guard to prevent save-on-select

        self.db = Database()

        self._build_ui()
        self.load_notes()

        # Auto-save every 5 minutes
        self.root.after(300_000, self.auto_save)

        # Clean up DB connection on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    #  UI CONSTRUCTION
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        # ── Top bar (search + dark mode) ──────────────────────────────
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=5, pady=5)

        tk.Label(top, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_notes())
        tk.Entry(top, textvariable=self.search_var).pack(
            side="left", fill="x", expand=True, padx=5)
        tk.Button(top, text="Dark Mode",
                  command=self.toggle_theme).pack(side="right")

        # ── Left panel (editor) ───────────────────────────────────────
        left = tk.Frame(self.root)
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        tk.Label(left, text="Title").pack(anchor="w")
        self.title_entry = tk.Entry(left)
        self.title_entry.pack(fill="x")

        tk.Label(left, text="Content").pack(anchor="w", pady=(10, 0))
        self.text = tk.Text(left, wrap="word", undo=True)
        self.text.pack(fill="both", expand=True)
        self.text.bind("<KeyRelease>", self.update_word_count)

        self.word_label = tk.Label(left, text="Words: 0 | Characters: 0")
        self.word_label.pack(anchor="e")

        # ── Buttons ───────────────────────────────────────────────────
        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x", pady=5)

        for label, cmd in [
            ("New",        self.new_note),
            ("Save",       self.save_note),
            ("Delete",     self.delete_note),
            ("Pin/Unpin",  self.toggle_pin),
            ("Export PDF", self.export_pdf),
        ]:
            tk.Button(btn_frame, text=label, command=cmd).pack(
                side="left", padx=2)

        # ── Right panel (notes list) ───────────────────────────────────
        right = tk.Frame(self.root)
        right.pack(side="right", fill="y", padx=10, pady=10)

        tk.Label(right, text="Saved Notes").pack()

        scrollbar = tk.Scrollbar(right, orient="vertical")
        self.listbox = tk.Listbox(right, width=35,
                                  yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.listbox.bind("<<ListboxSelect>>", self.load_selected_note)

        # ── Status bar ────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.root, textvariable=self.status_var,
                 anchor="w", relief="sunken").pack(
            side="bottom", fill="x", padx=5, pady=2)

        self.notes_map: dict[str, int] = {}   # display_label -> note id

    # ------------------------------------------------------------------ #
    #  NOTES LIST
    # ------------------------------------------------------------------ #
    def load_notes(self):
        self.listbox.delete(0, tk.END)
        self.notes_map.clear()

        for note_id, title, pinned in self.db.fetch_notes(
                self.search_var.get()):
            display = ("⭐ " if pinned else "") + (title or "(untitled)")
            # Avoid duplicate display keys
            key, suffix = display, 1
            while key in self.notes_map:
                key = f"{display} ({suffix})"
                suffix += 1
            self.notes_map[key] = note_id
            self.listbox.insert(tk.END, key)

        # Re-highlight the currently open note if it's still in the list
        if self.current_id:
            for i, key in enumerate(self.listbox.get(0, tk.END)):
                if self.notes_map.get(key) == self.current_id:
                    self.listbox.selection_set(i)
                    self.listbox.see(i)
                    break

    # ------------------------------------------------------------------ #
    #  SAVE
    # ------------------------------------------------------------------ #
    def save_note(self):
        title   = self.title_entry.get().strip()
        content = self.text.get("1.0", tk.END).strip()

        if not title:
            messagebox.showwarning("Warning", "Please enter a title.")
            return

        if self.current_id:
            self.db.update_note(self.current_id, title, content)
        else:
            self.current_id = self.db.insert_note(title, content)

        self.load_notes()
        self.set_status(f"Saved: {title}")

    # ------------------------------------------------------------------ #
    #  NEW NOTE
    # ------------------------------------------------------------------ #
    def new_note(self):
        self.current_id = None
        self.title_entry.delete(0, tk.END)
        self.text.delete("1.0", tk.END)
        self.listbox.selection_clear(0, tk.END)
        self.update_word_count()
        self.title_entry.focus_set()
        self.set_status("New note – start typing")

    # ------------------------------------------------------------------ #
    #  DELETE
    # ------------------------------------------------------------------ #
    def delete_note(self):
        if not self.current_id:
            messagebox.showinfo("Info", "No note selected.")
            return

        if messagebox.askyesno("Confirm", "Delete this note permanently?"):
            self.db.delete_note(self.current_id)
            self.new_note()
            self.load_notes()
            self.set_status("Note deleted.")

    # ------------------------------------------------------------------ #
    #  LOAD SELECTED NOTE
    # ------------------------------------------------------------------ #
    def load_selected_note(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return

        display = self.listbox.get(sel[0])
        note_id = self.notes_map.get(display)
        if note_id is None or note_id == self.current_id:
            return

        row = self.db.fetch_note(note_id)
        if not row:
            return

        self.is_loading = True
        self.current_id = note_id

        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, row[0] or "")

        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", row[1] or "")

        self.update_word_count()
        self.is_loading = False
        self.set_status(f"Loaded: {row[0]}")

    # ------------------------------------------------------------------ #
    #  WORD COUNT
    # ------------------------------------------------------------------ #
    def update_word_count(self, event=None):
        content = self.text.get("1.0", tk.END)
        words   = len(content.split())
        chars   = len(content.strip())
        self.word_label.config(text=f"Words: {words} | Characters: {chars}")

    # ------------------------------------------------------------------ #
    #  PIN / UNPIN
    # ------------------------------------------------------------------ #
    def toggle_pin(self):
        if not self.current_id:
            messagebox.showinfo("Info", "No note selected.")
            return
        self.db.toggle_pin(self.current_id)
        self.load_notes()
        self.set_status("Pin status toggled.")

    # ------------------------------------------------------------------ #
    #  EXPORT PDF
    # ------------------------------------------------------------------ #
    def export_pdf(self):
        if not self.current_id:
            messagebox.showinfo("Info", "No note selected.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not file_path:
            return

        title   = self.title_entry.get()
        content = self.text.get("1.0", tk.END)

        pdf = canvas.Canvas(file_path)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, 800, title)

        pdf.setFont("Helvetica", 11)
        y = 775
        for line in content.split("\n"):
            while len(line) > 95:
                pdf.drawString(50, y, line[:95])
                line = line[95:]
                y -= 16
                if y < 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 11)
                    y = 800
            pdf.drawString(50, y, line)
            y -= 16
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = 800

        pdf.save()
        messagebox.showinfo("Success", "PDF exported successfully.")
        self.set_status(f"PDF saved: {file_path}")

    # ------------------------------------------------------------------ #
    #  AUTO-SAVE
    # ------------------------------------------------------------------ #
    def auto_save(self):
        if self.current_id and self.title_entry.get().strip():
            self.save_note()
            self.set_status("Auto-saved.")
        self.root.after(300_000, self.auto_save)

    # ------------------------------------------------------------------ #
    #  DARK / LIGHT THEME
    # ------------------------------------------------------------------ #
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        bg       = "#2b2b2b" if self.dark_mode else "SystemButtonFace"
        fg       = "white"   if self.dark_mode else "black"
        text_bg  = "#1e1e1e" if self.dark_mode else "white"

        def recurse(widget):
            try:
                widget.configure(bg=bg, fg=fg)
            except tk.TclError:
                try:
                    widget.configure(bg=bg)
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                recurse(child)

        recurse(self.root)
        self.text.configure(bg=text_bg, fg=fg, insertbackground=fg)
        self.listbox.configure(
            bg=text_bg, fg=fg,
            selectbackground="#555555" if self.dark_mode else "#0078d7",
            selectforeground="white",
        )

    # ------------------------------------------------------------------ #
    #  STATUS BAR
    # ------------------------------------------------------------------ #
    def set_status(self, msg: str):
        self.status_var.set(msg)
        self.root.after(4000, lambda: self.status_var.set("Ready"))

    # ------------------------------------------------------------------ #
    #  CLEANUP
    # ------------------------------------------------------------------ #
    def _on_close(self):
        self.db.close()
        self.root.destroy()