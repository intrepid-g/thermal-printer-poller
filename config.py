"""Settings, asked once and remembered. Environment variables always win."""

import json
import os
import sys
from pathlib import Path

PATH = Path(os.environ.get("THERMAL_PRINTER_CONFIG", Path.home() / ".config" / "thermal-printer" / "config.json"))
ENV = {"printer_addr": "BTPRINT_ADDR", "server_url": "EVERYTHING_URL", "token": "EVERYTHING_PRINT_TOKEN"}


def _load() -> dict:
    try:
        return json.loads(PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, indent=2))
    PATH.chmod(0o600)  # holds the poller token


def get(key: str, prompt: str, ask=input) -> str:
    """Env var, else the saved value, else ask once and save."""
    value = os.environ.get(ENV[key]) or _load().get(key)
    if value:
        return value
    if not sys.stdin.isatty():
        sys.exit(f"{key} is not set: export {ENV[key]} or run once in a terminal to be asked.")
    value = ask(prompt).strip()
    if not value:
        sys.exit(f"{key} is required.")
    _save({**_load(), key: value})
    print(f"saved {key} to {PATH}", file=sys.stderr)
    return value
