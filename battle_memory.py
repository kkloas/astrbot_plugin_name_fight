"""Persist a small, group-scoped record of the bot's own recent battles."""
import json
import sqlite3
import time
from pathlib import Path

RETENTION_SECONDS = 48 * 60 * 60


def save_battle(path: Path, group_id: str, payload: dict, occurred_at: float | None = None) -> None:
    now = time.time()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=5) as db:
        db.execute('CREATE TABLE IF NOT EXISTS bot_battles (id INTEGER PRIMARY KEY, group_id TEXT NOT NULL, occurred_at REAL NOT NULL, payload TEXT NOT NULL)')
        db.execute('INSERT INTO bot_battles (group_id, occurred_at, payload) VALUES (?, ?, ?)',
                   (group_id, occurred_at if occurred_at is not None else now, json.dumps(payload, ensure_ascii=False)))
        db.execute('DELETE FROM bot_battles WHERE occurred_at < ?', (now - RETENTION_SECONDS,))
        db.execute('DELETE FROM bot_battles WHERE group_id = ? AND id NOT IN (SELECT id FROM bot_battles WHERE group_id = ? ORDER BY occurred_at DESC, id DESC LIMIT 20)', (group_id, group_id))


def recent_battles(path: Path, group_id: str) -> list[dict]:
    if not path.exists():
        return []
    with sqlite3.connect(path, timeout=5) as db:
        rows = db.execute('SELECT occurred_at, payload FROM bot_battles WHERE group_id = ? AND occurred_at >= ? ORDER BY occurred_at DESC, id DESC LIMIT 3', (group_id, time.time() - RETENTION_SECONDS)).fetchall()
    return [{'time_utc': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(when)), **json.loads(payload)} for when, payload in rows]
