
# Magic Revolver (MDG)

Magic Revolver (MDG) is a lightweight desktop launcher built around a six-slot revolver interface.

Each chamber acts as a spell slot that can store and fire local commands.

MDG is designed for fast local workflow execution, project launching, and tool orchestration.

## Features

- 6 fixed spell slots
- Revolver-style GUI
- Double-click command firing
- Right-click slot editing
- Fire logging
- Lightweight local operation
- PowerShell-friendly workflow

## Files

- `revolver_gui.py`  
  Desktop GUI.

- `revolver.py`  
  Command runner and log writer.

- `spells.json`  
  Local slot configuration. Keep this file private when it contains personal paths or commands.

- `spells.example.json`  
  Public-safe sample slot configuration.

- `logs/`  
  Fire history.

## Usage

Start GUI:

```powershell
py revolver_gui.py
```

Initialize config:

```powershell
py revolver.py init
```

List slots:

```powershell
py revolver.py list
```

Fire slot:

```powershell
py revolver.py fire 1
```

Edit config:

```powershell
py revolver.py edit
```

## Codex-style instruction sample

MDG works best when command preparation and command execution stay separate.

You can give an AI assistant a short instruction like this:

```txt
Read the project instructions first.
Prepare safe, readable MDG slots for the active project.
Use six slots as a small command magazine.
Avoid destructive or external-impact commands unless explicitly requested.
After changing a slot, report the slot number, directory, command, and risk.
The operator reviews and fires slots from the GUI.
```

This is only a usage pattern. Review every command before firing it.

## Slot config

Example:

```json
{
  "name": "Run App",
  "impact_dir": "E:/your_project",
  "command": ".\\.venv\\Scripts\\python.exe app.py"
}
```

## GUI controls

* Single click: select slot
* Double click: fire slot
* Right click: edit slot
* Center click: reload

## Visual customization

The GUI can use a custom background image.

Place a PNG at:

```txt
assets/revolver_bg.png
```

Transparent PNGs work well because the window background color can still show through.

Slot button positions are defined in `revolver_gui.py`:

```python
SLOTS = {
    1: (109, 52),
    2: (155, 78),
    3: (159, 136),
    4: (109, 166),
    5: (60, 137),
    6: (63, 78),
}
```

Adjust these coordinates when your background art uses a different chamber layout.

## Note

MDG is designed as a lightweight local command launcher.

For public sharing, prefer committing `spells.example.json` and keeping `spells.json`, logs, and generated caches local.

## License

MIT License
