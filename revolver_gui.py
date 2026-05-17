import ctypes
import json
import sys
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import revolver

BASE_DIR = Path(__file__).resolve().parent
SPELLS_PATH = BASE_DIR / "spells.json"
ASSETS_DIR = BASE_DIR / "assets"
BG_PATH = ASSETS_DIR / "revolver_bg.png"
FIRE_SOUND_PATH = ASSETS_DIR / "fire.wav"
FONT_SLOT = ("Consolas", 12, "bold")
FONT_CENTER = ("Consolas", 15, "bold")
FONT_STATUS = ("Consolas", 8)
COLOR_BG = "#111111"
COLOR_SHELL = "#666666"
COLOR_SLOT = "#222222"
COLOR_SLOT_SELECTED = "#f0f0f0"
COLOR_CENTER = "#333333"
COLOR_CENTER_SELECTED = "#ffffff"
COLOR_TEXT = "#f5f5f5"
COLOR_TEXT_INVERT = "#111111"
COLOR_STATUS_BG = "#111111"
COLOR_STATUS_FG = "#dddddd"

WINDOW_W = 220
WINDOW_H = 220

SLOTS = {
    1: (109, 52),
    2: (155, 78),
    3: (159, 136),
    4: (109, 166),
    5: (60, 137),
    6: (63, 78),
}

CENTER = (110, 110)
R = 21


def apply_dark_title_bar(root):
    if sys.platform != "win32":
        return

    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1)

        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            if result == 0:
                break
    except Exception:
        pass


def play_fire_sound():
    if sys.platform != "win32":
        return

    try:
        import winsound

        if FIRE_SOUND_PATH.exists():
            winsound.PlaySound(
                str(FIRE_SOUND_PATH),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass


class RevolverGUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.resizable(False, False)
        self.topmost = True
        self.root.attributes("-topmost", self.topmost)
        apply_dark_title_bar(self.root)

        self.selected_slot = None
        self.bg_image = None
        self.current_book = self.detect_current_book()
        self.update_title()

        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.status = tk.StringVar(value="Ready")
        self.label = tk.Label(
            root,
            textvariable=self.status,
            anchor="w",
            font=FONT_STATUS,
            bg=COLOR_STATUS_BG,
            fg=COLOR_STATUS_FG
        )
        self.label.pack(fill="x")

        self.draw()

    def load_spells(self):
        with SPELLS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_spells(self, data):
        with SPELLS_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def update_title(self):
        self.root.title("MDG")

    def list_spellbooks(self):
        revolver.ensure_files()
        return sorted(path.stem for path in revolver.SPELLBOOKS_DIR.glob("*.json") if path.is_file())

    def detect_current_book(self):
        try:
            active = json.dumps(revolver.load_config(), ensure_ascii=False, sort_keys=True)
            for book in self.list_spellbooks():
                path = revolver.spellbook_path(book)
                with path.open("r", encoding="utf-8") as f:
                    data = revolver.normalize_config(json.load(f))
                if json.dumps(data, ensure_ascii=False, sort_keys=True) == active:
                    return book
        except Exception:
            return None

        return None

    def draw(self):
        self.canvas.delete("all")

        if BG_PATH.exists():
            try:
                self.bg_image = tk.PhotoImage(file=str(BG_PATH))
                self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            except Exception:
                self.draw_fallback_shell()
        else:
            self.draw_fallback_shell()

        for slot, (x, y) in SLOTS.items():
            self.draw_slot(slot, x, y)

        cx, cy = CENTER
        center_fill = COLOR_CENTER_SELECTED if self.selected_slot == "center" else COLOR_CENTER
        center_text = COLOR_TEXT_INVERT if self.selected_slot == "center" else COLOR_TEXT

        self.canvas.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, fill=center_fill, outline=COLOR_SHELL, tags="center")
        self.canvas.create_text(cx, cy, text="↻", font=FONT_CENTER, fill=center_text, tags="center")
        self.canvas.tag_bind("center", "<Button-1>", self.reload)
        self.canvas.tag_bind("center", "<Button-3>", self.open_spellbook_menu)
        self.canvas.tag_bind("center", "<Button-2>", self.toggle_topmost)

    def draw_fallback_shell(self):

        cx, cy = CENTER
        self.canvas.create_oval(20, 20, 200, 200, outline=COLOR_SHELL, width=3)
        self.canvas.create_oval(cx - 35, cy - 35, cx + 35, cy + 35, outline=COLOR_SHELL, width=2)

    def draw_slot(self, slot, x, y):
        tag = f"slot_{slot}"

        fill = COLOR_SLOT_SELECTED if slot == self.selected_slot else COLOR_SLOT
        text_fill = COLOR_TEXT_INVERT if slot == self.selected_slot else COLOR_TEXT

        self.canvas.create_oval(x - R, y - R, x + R, y + R, fill=fill, outline=COLOR_SHELL, width=2, tags=tag)
        self.canvas.create_text(x, y, text=str(slot), font=FONT_SLOT, fill=text_fill, tags=tag)

        self.canvas.tag_bind(tag, "<Button-1>", lambda e, n=slot: self.select_slot(n))
        self.canvas.tag_bind(tag, "<Double-Button-1>", lambda e, n=slot: self.fire_slot(n))
        self.canvas.tag_bind(tag, "<Button-3>", lambda e, n=slot: self.edit_slot(n))
        self.canvas.tag_bind(tag, "<Enter>", lambda e, n=slot: self.hover_slot(n))

    def select_slot(self, slot):
        self.selected_slot = slot
        spell = self.load_spells()["slots"][slot - 1]
        self.status.set(f"[{slot}] {spell.get('name', 'Unnamed')}")
        self.draw()

    def hover_slot(self, slot):
        spell = self.load_spells()["slots"][slot - 1]
        self.status.set(f"[{slot}] {spell.get('name', 'Unnamed')}")

    def fire_slot(self, slot):
        play_fire_sound()
        subprocess.Popen(
            ["py", "revolver.py", "fire", str(slot)],
            cwd=str(BASE_DIR)
        )
        self.status.set(f"Fired slot {slot}")

    def reload(self, event=None):
        self.selected_slot = "center"
        self.current_book = self.detect_current_book()
        self.update_title()
        self.draw()
        self.status.set("Reloaded")

    def toggle_topmost(self, event=None):
        self.topmost = not self.topmost
        self.root.attributes("-topmost", self.topmost)
        state = "on" if self.topmost else "off"
        self.status.set(f"Topmost: {state}")

    def open_spellbook_menu(self, event):
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            activebackground=COLOR_SLOT_SELECTED,
            activeforeground=COLOR_TEXT_INVERT,
            relief="flat",
            borderwidth=1,
        )
        books = self.list_spellbooks()

        if not books:
            menu.add_command(label="No spellbooks", state="disabled")
        else:
            for book in books:
                menu.add_command(label=book, command=lambda name=book: self.load_spellbook(name))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def load_spellbook(self, book):
        try:
            revolver.load_book(book)
        except SystemExit as e:
            messagebox.showerror("MDG", str(e))
            return
        except Exception as e:
            messagebox.showerror("MDG", f"Failed to load spellbook: {e}")
            return

        self.selected_slot = None
        self.current_book = book
        self.update_title()
        self.draw()
        self.status.set(f"Loaded book: {book}")

    def edit_slot(self, slot):
        data = self.load_spells()
        spell = data["slots"][slot - 1]

        result = self.open_slot_editor(slot, spell)
        if result is None:
            return

        name, impact_dir, command = result

        data["slots"][slot - 1] = {
            "name": name,
            "impact_dir": impact_dir.replace("\\", "/"),
            "command": command
        }

        self.save_spells(data)
        self.status.set(f"Loaded slot {slot}: {name}")
        self.draw()

    def open_slot_editor(self, slot, spell):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Slot {slot}")
        dialog.geometry("560x160")
        dialog.configure(bg=COLOR_BG)
        dialog.resizable(True, False)
        dialog.transient(self.root)
        dialog.grab_set()
        apply_dark_title_bar(dialog)

        result = {"value": None}

        frame = tk.Frame(dialog, padx=12, pady=10, bg=COLOR_BG)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Name", spell.get("name", "")),
            ("Impact Dir", spell.get("impact_dir", "")),
            ("Command", spell.get("command", "")),
        ]
        entries = []

        for row, (label_text, initial_value) in enumerate(fields):
            label = tk.Label(frame, text=label_text, anchor="w", bg=COLOR_BG, fg=COLOR_STATUS_FG)
            label.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)

            entry = tk.Entry(
                frame,
                bg=COLOR_SLOT,
                fg=COLOR_TEXT,
                insertbackground=COLOR_TEXT,
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLOR_SHELL,
                highlightcolor=COLOR_SLOT_SELECTED,
            )
            entry.insert(0, initial_value)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            entries.append(entry)

        button_row = tk.Frame(frame, bg=COLOR_BG)
        button_row.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(8, 0))

        def save():
            result["value"] = tuple(entry.get() for entry in entries)
            dialog.destroy()

        def cancel():
            dialog.destroy()

        button_options = {
            "bg": COLOR_SLOT,
            "fg": COLOR_TEXT,
            "activebackground": COLOR_SLOT_SELECTED,
            "activeforeground": COLOR_TEXT_INVERT,
            "relief": "flat",
            "padx": 12,
        }
        tk.Button(button_row, text="Cancel", command=cancel, **button_options).pack(side="right", padx=(6, 0))
        tk.Button(button_row, text="Save", command=save, **button_options).pack(side="right")

        dialog.bind("<Return>", lambda event: save())
        dialog.bind("<Escape>", lambda event: cancel())
        entries[0].focus_set()
        dialog.wait_window()

        return result["value"]


def main():
    if not SPELLS_PATH.exists():
        messagebox.showerror("MDG", "spells.json not found. Run: py revolver.py init")
        return

    root = tk.Tk()
    app = RevolverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
