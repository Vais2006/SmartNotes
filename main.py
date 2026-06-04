import tkinter as tk
from ui import NotesManager

if __name__ == "__main__":
    root = tk.Tk()
    app  = NotesManager(root)
    root.mainloop()