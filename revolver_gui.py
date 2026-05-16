import ctypes
import json
import sys
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

BASE_DIR = Path(__file__).resolve().parent
SPELLS_PATH = BASE_DIR / "spells.json"
ASSETS_DIR = BASE_DIR / "assets"
BG_PATH = ASSETS_DIR / "revolver_bg.png"
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


class RevolverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MDG")
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.resizable(False, False)
        apply_dark_title_bar(self.root)

        self.selected_slot = None
        self.bg_image = None

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
        subprocess.Popen(
            ["py", "revolver.py", "fire", str(slot)],
            cwd=str(BASE_DIR)
        )
        self.status.set(f"Fired slot {slot}")

    def reload(self, event=None):
        self.selected_slot = "center"
        self.draw()
        self.status.set("Reloaded")

    def edit_slot(self, slot):
        data = self.load_spells()
        spell = data["slots"][slot - 1]

        name = simpledialog.askstring("Name", "Name", initialvalue=spell.get("name", ""))
        if name is None:
            return

        impact_dir = simpledialog.askstring("Impact Dir", "Impact Dir", initialvalue=spell.get("impact_dir", ""))
        if impact_dir is None:
            return

        command = simpledialog.askstring("Spell", "Spell", initialvalue=spell.get("command", ""))
        if command is None:
            return

        data["slots"][slot - 1] = {
            "name": name,
            "impact_dir": impact_dir.replace("\\", "/"),
            "command": command
        }

        self.save_spells(data)
        self.status.set(f"Loaded slot {slot}: {name}")
        self.draw()


def main():
    if not SPELLS_PATH.exists():
        messagebox.showerror("MDG", "spells.json not found. Run: py revolver.py init")
        return

    root = tk.Tk()
    app = RevolverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
