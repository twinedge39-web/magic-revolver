import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SPELLS_PATH = BASE_DIR / "spells.json"
LOG_DIR = BASE_DIR / "logs"
SLOT_COUNT = 6


DEFAULT_CONFIG = {
    "slots": [
        {
            "name": f"Empty {i}",
            "impact_dir": str(BASE_DIR).replace("\\", "/"),
            "command": "pwsh"
        }
        for i in range(1, SLOT_COUNT + 1)
    ]
}


def ensure_files():
    LOG_DIR.mkdir(exist_ok=True)

    if not SPELLS_PATH.exists():
        save_config(DEFAULT_CONFIG)
        print(f"Created: {SPELLS_PATH}")


def load_config():
    ensure_files()
    with SPELLS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    slots = data.get("slots", [])

    while len(slots) < SLOT_COUNT:
        slots.append({
            "name": f"Empty {len(slots) + 1}",
            "impact_dir": str(BASE_DIR).replace("\\", "/"),
            "command": "pwsh"
        })

    data["slots"] = slots[:SLOT_COUNT]
    return data


def save_config(data):
    with SPELLS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_fire(slot_no, spell):
    LOG_DIR.mkdir(exist_ok=True)

    now = datetime.now()
    log_path = LOG_DIR / f"fire_{now.strftime('%Y%m%d')}.log"

    with log_path.open("a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"slot: {slot_no}\n")
        f.write(f"name: {spell.get('name', '')}\n")
        f.write(f"impact_dir: {spell.get('impact_dir', '')}\n")
        f.write(f"command: {spell.get('command', '')}\n")


def launch_command(command, cwd):
    subprocess.Popen(
        ["pwsh", "-NoExit", "-Command", command],
        cwd=str(cwd),
    )


def list_slots():
    data = load_config()

    for i, spell in enumerate(data["slots"], start=1):
        name = spell.get("name", "Unnamed")
        impact_dir = spell.get("impact_dir", "")
        command = spell.get("command", "")

        print(f"[{i}] {name}")
        print(f"    dir : {impact_dir}")
        print(f"    cmd : {command}")


def fire(slot_no):
    data = load_config()

    if slot_no < 1 or slot_no > SLOT_COUNT:
        raise SystemExit("slot must be 1-6")

    spell = data["slots"][slot_no - 1]

    name = spell.get("name", "Unnamed")
    impact_dir = Path(spell.get("impact_dir", "")).expanduser()
    command = spell.get("command", "").strip()

    if not impact_dir.exists():
        raise SystemExit(f"impact_dir not found: {impact_dir}")

    if not command:
        raise SystemExit("command is empty")

    print(f"Firing slot {slot_no}: {name}")
    print(f"Impact dir: {impact_dir}")
    print(f"Command: {command}")

    log_fire(slot_no, spell)

    launch_command(command, impact_dir)


def set_slot(slot_no, name, impact_dir, command):
    data = load_config()

    if slot_no < 1 or slot_no > SLOT_COUNT:
        raise SystemExit("slot must be 1-6")

    data["slots"][slot_no - 1] = {
        "name": name,
        "impact_dir": impact_dir.replace("\\", "/"),
        "command": command
    }

    save_config(data)
    print(f"Loaded slot {slot_no}: {name}")


def edit_config():
    ensure_files()
    launch_command("code spells.json", BASE_DIR)


def open_dir():
    ensure_files()
    subprocess.Popen(
        ["explorer", str(BASE_DIR)]
    )


def main():
    parser = argparse.ArgumentParser(description="Magic Revolver CLI v0.1")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init")
    sub.add_parser("list")
    sub.add_parser("edit")
    sub.add_parser("open")

    fire_p = sub.add_parser("fire")
    fire_p.add_argument("slot", type=int)

    set_p = sub.add_parser("set")
    set_p.add_argument("slot", type=int)
    set_p.add_argument("--name", required=True)
    set_p.add_argument("--dir", required=True)
    set_p.add_argument("--cmd", required=True)

    args = parser.parse_args()

    if args.command == "init":
        ensure_files()
        print("Magic Revolver initialized.")

    elif args.command == "list":
        list_slots()

    elif args.command == "fire":
        fire(args.slot)

    elif args.command == "set":
        set_slot(args.slot, args.name, args.dir, args.cmd)

    elif args.command == "edit":
        edit_config()

    elif args.command == "open":
        open_dir()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
