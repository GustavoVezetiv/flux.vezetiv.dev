from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("data/imobi_automation.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS packages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  source_name TEXT,
  created_at TEXT NOT NULL,
  raw_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  package_id INTEGER NOT NULL,
  item_key TEXT NOT NULL,
  reference TEXT,
  title TEXT NOT NULL,
  action TEXT NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  message TEXT,
  UNIQUE(package_id, item_key)
);
CREATE TABLE IF NOT EXISTS control (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  pause_requested INTEGER NOT NULL DEFAULT 0,
  stop_requested INTEGER NOT NULL DEFAULT 0,
  worker_status TEXT NOT NULL DEFAULT 'idle',
  current_item_id INTEGER,
  message TEXT,
  updated_at TEXT
);
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  level TEXT NOT NULL,
  item_id INTEGER,
  message TEXT NOT NULL
);
INSERT OR IGNORE INTO control (id, updated_at) VALUES (1, datetime('now'));
"""

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.executescript(SCHEMA)

def log(message: str, level: str = "INFO", item_id: int | None = None):
    with connect() as con:
        con.execute("INSERT INTO logs(ts,level,item_id,message) VALUES (?,?,?,?)",
                    (datetime.now().isoformat(timespec="seconds"), level, item_id, message))

def set_control(**kwargs):
    if not kwargs:
        return
    kwargs["updated_at"] = datetime.now().isoformat(timespec="seconds")
    sets = ", ".join(f"{k}=?" for k in kwargs)
    with connect() as con:
        con.execute(f"UPDATE control SET {sets} WHERE id=1", tuple(kwargs.values()))

def get_control():
    with connect() as con:
        return dict(con.execute("SELECT * FROM control WHERE id=1").fetchone())

def list_logs(limit=200):
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
