"""Read-only spectator snapshots shared by the QQ bot and web worker."""

import json
import re
import secrets
import sqlite3
import time
import zlib
from contextlib import closing
from pathlib import Path
from typing import Any

TTL_SECONDS = 48 * 3600


def _replay_fighter(fighter: dict[str, Any]) -> dict[str, Any]:
    martial_art = fighter.get("martial_art") or {}
    neigong = fighter.get("neigong") or {}
    qinggong = fighter.get("qinggong") or {}
    stats = fighter.get("stats") or {}
    return {
        "name": str(fighter.get("name") or "未知角色"),
        "bossKey": fighter.get("boss_key"),
        "stats": {
            "hp": int(stats.get("hp", 1)),
            "spd": float(stats.get("spd", 0)),
        },
        "currentHp": int(fighter.get("current_hp", stats.get("hp", 1))),
        "martialArt": {
            "id": martial_art.get("id", ""),
            "name": martial_art.get("name", "无名武学"),
            "type": martial_art.get("type", "sword"),
        },
        "neigong": {"id": neigong.get("id", ""), "name": neigong.get("name", "")},
        "qinggong": {"id": qinggong.get("id", ""), "name": qinggong.get("name", "")},
    }


def battle_payload(
    fighter_a: dict[str, Any],
    fighter_b: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any] | None:
    events = result.get("events") if isinstance(result, dict) else None
    if not isinstance(events, list) or not events:
        return None
    payload = {
        "attacker": _replay_fighter(fighter_a),
        "defender": _replay_fighter(fighter_b),
        "winner": result.get("winner"),
        "boss": result.get("boss"),
        "events": events,
    }
    return payload


def save_replay(
    directory: Path, segments: list[dict], team_outcome: str | None = None
) -> str:
    bouts = []
    for segment in segments:
        bout = battle_payload(
            segment["fighter_a"], segment["fighter_b"], segment["result"]
        )
        if bout is None:
            raise ValueError("Missing battle events")
        bouts.append(bout)
    if not bouts:
        raise ValueError("Empty replay")
    if team_outcome is not None:
        bouts[-1]["teamOutcome"] = {
            "attacker": "挑战方获胜",
            "defender": "应战方获胜",
            "draw": "平局",
        }[team_outcome]
    key = secrets.token_urlsafe(18)
    data = json.dumps(bouts, ensure_ascii=False, separators=(",", ":")).encode()
    now = int(time.time())
    with closing(sqlite3.connect(directory / "spectator.sqlite3", timeout=1)) as db, db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS replays (id TEXT PRIMARY KEY, expires INTEGER NOT NULL, payload BLOB NOT NULL)"
        )
        db.execute("CREATE INDEX IF NOT EXISTS replay_expiry ON replays(expires)")
        db.execute("DELETE FROM replays WHERE expires <= ?", (now,))
        db.execute(
            "INSERT INTO replays VALUES (?, ?, ?)",
            (key, now + TTL_SECONDS, zlib.compress(data, level=1)),
        )
    return key


def read_replay(directory: Path, key: str) -> str | None:
    path = directory / "spectator.sqlite3"
    if not re.fullmatch(r"[A-Za-z0-9_-]{24}", key) or not path.is_file():
        return None
    with closing(
        sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1)
    ) as db:
        row = db.execute(
            "SELECT payload FROM replays WHERE id = ? AND expires > ?",
            (key, int(time.time())),
        ).fetchone()
    return zlib.decompress(row[0]).decode() if row else None
