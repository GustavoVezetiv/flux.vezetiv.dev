from __future__ import annotations
import json
from pathlib import Path

APP_CONFIG = Path("config/app.json")
SELECTORS_CONFIG = Path("config/selectors.json")

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_app_config():
    return load_json(APP_CONFIG)

def load_selectors():
    return load_json(SELECTORS_CONFIG)
