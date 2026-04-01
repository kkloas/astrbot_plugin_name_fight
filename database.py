# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import hashlib
import random
import shutil
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configs"
LEGACY_DATA_DIR = BASE_DIR / "data"
HP_BATTLE_SCALE = 2.2
MAX_FIGHTERS_PER_USER = 3
ELO_INITIAL_RATING = 1200.0
ELO_NEWCOMER_K = 112.0
ELO_STABLE_K = 80.0
ELO_NEWCOMER_BATTLES = 3


def _default_data_dir() -> Path:
    if BASE_DIR.parent.name == "plugins":
        return BASE_DIR.parent.parent / "name_fight_data"
    return BASE_DIR / "name_fight_data"


def _default_db_path() -> Path:
    return _default_data_dir() / "fighters.db"


def _legacy_db_path() -> Path:
    return LEGACY_DATA_DIR / "fighters.db"


class FighterRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or _default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_db()
        self.martial_arts = self._load_json(CONFIG_DIR / "martial_arts.json")
        self.neigong = self._load_json(CONFIG_DIR / "neigong.json")
        self.qinggong = self._load_json(CONFIG_DIR / "qinggong.json")
        self.martial_arts_map = {item["id"]: item for item in self.martial_arts}
        self.neigong_map = {item["id"]: item for item in self.neigong}
        self.qinggong_map = {item["id"]: item for item in self.qinggong}
        self._init_db()

    def _migrate_legacy_db(self) -> None:
        legacy_db = _legacy_db_path()
        if self.db_path.exists() or not legacy_db.exists() or legacy_db == self.db_path:
            return
        shutil.copy2(legacy_db, self.db_path)

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS fighters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    hp INTEGER NOT NULL,
                    atk INTEGER NOT NULL,
                    def INTEGER NOT NULL,
                    spd REAL NOT NULL,
                    crt REAL NOT NULL,
                    eva REAL NOT NULL,
                    martial_art_id TEXT NOT NULL,
                    neigong_id TEXT NOT NULL,
                    qinggong_id TEXT NOT NULL,
                    weapon_id TEXT DEFAULT NULL,
                    level INTEGER NOT NULL DEFAULT 1,
                    exp INTEGER NOT NULL DEFAULT 0,
                    wins INTEGER NOT NULL DEFAULT 0,
                    battles INTEGER NOT NULL DEFAULT 0,
                    star_rating REAL NOT NULL DEFAULT 3.0
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    fighter_name TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(fighter_name) REFERENCES fighters(name)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_fighters (
                    user_id TEXT NOT NULL,
                    fighter_name TEXT NOT NULL UNIQUE,
                    slot_index INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, fighter_name),
                    UNIQUE (user_id, slot_index),
                    FOREIGN KEY(fighter_name) REFERENCES fighters(name)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS fighter_scores (
                    group_id TEXT NOT NULL,
                    fighter_name TEXT NOT NULL,
                    wins INTEGER NOT NULL DEFAULT 0,
                    battles INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (group_id, fighter_name)
                )
                """
            )
            fighter_columns = {row["name"] for row in connection.execute("PRAGMA table_info(fighters)").fetchall()}
            if "wins" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN wins INTEGER NOT NULL DEFAULT 0")
            if "battles" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN battles INTEGER NOT NULL DEFAULT 0")
            if "star_rating" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN star_rating REAL NOT NULL DEFAULT 3.0")
            connection.execute("UPDATE fighters SET battles = wins WHERE battles < wins")
            score_columns = {row["name"] for row in connection.execute("PRAGMA table_info(fighter_scores)").fetchall()}
            if "battles" not in score_columns:
                connection.execute("ALTER TABLE fighter_scores ADD COLUMN battles INTEGER NOT NULL DEFAULT 0")
            if "elo_rating" not in score_columns:
                connection.execute(f"ALTER TABLE fighter_scores ADD COLUMN elo_rating REAL NOT NULL DEFAULT {ELO_INITIAL_RATING}")
            connection.execute("UPDATE fighter_scores SET battles = wins WHERE battles < wins")
            connection.execute(
                "UPDATE fighter_scores SET elo_rating = ? WHERE elo_rating IS NULL OR elo_rating <= 0",
                (ELO_INITIAL_RATING,),
            )
            legacy_rows = connection.execute("SELECT user_id, fighter_name FROM user_profiles").fetchall()
            roster_count = connection.execute("SELECT COUNT(*) FROM user_fighters").fetchone()[0]
            if roster_count == 0 and legacy_rows:
                for row in legacy_rows:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO user_fighters (user_id, fighter_name, slot_index, is_active)
                        VALUES (?, ?, 1, 1)
                        """,
                        (str(row["user_id"]), str(row["fighter_name"])),
                    )
            connection.commit()

    def get_fighter_by_name(self, name: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM fighters WHERE name = ?",
                (name,),
            ).fetchone()
        if row is None:
            return None
        return self._hydrate_fighter(dict(row))

    def get_user_fighters(self, user_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT fighter_name, slot_index, is_active
                FROM user_fighters
                WHERE user_id = ?
                ORDER BY slot_index ASC
                """,
                (user_id,),
            ).fetchall()
        fighters: list[dict[str, Any]] = []
        for row in rows:
            fighter = self.get_fighter_by_name(str(row["fighter_name"]))
            if fighter is None:
                continue
            fighter["slot_index"] = int(row["slot_index"])
            fighter["is_active"] = bool(row["is_active"])
            fighters.append(fighter)
        return fighters

    def get_active_fighter(self, user_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT fighter_name
                FROM user_fighters
                WHERE user_id = ? AND is_active = 1
                ORDER BY slot_index ASC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if row is None:
                row = connection.execute(
                    """
                    SELECT fighter_name
                    FROM user_fighters
                    WHERE user_id = ?
                    ORDER BY slot_index ASC
                    LIMIT 1
                    """,
                    (user_id,),
                ).fetchone()
        if row is None:
            return None
        fighter = self.get_fighter_by_name(str(row["fighter_name"]))
        if fighter is None:
            return None
        return fighter

    def get_user_fighter_by_name(self, user_id: str, fighter_name: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT fighter_name, slot_index, is_active
                FROM user_fighters
                WHERE user_id = ? AND fighter_name = ?
                """,
                (user_id, fighter_name),
            ).fetchone()
        if row is None:
            return None
        fighter = self.get_fighter_by_name(str(row["fighter_name"]))
        if fighter is None:
            return None
        fighter["slot_index"] = int(row["slot_index"])
        fighter["is_active"] = bool(row["is_active"])
        return fighter

    def get_owner_user_id_by_fighter_name(self, fighter_name: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT user_id FROM user_fighters WHERE fighter_name = ?",
                (fighter_name,),
            ).fetchone()
        return None if row is None else str(row["user_id"])

    def user_owns_fighter(self, user_id: str, fighter_name: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM user_fighters WHERE user_id = ? AND fighter_name = ?",
                (user_id, fighter_name),
            ).fetchone()
        return row is not None

    def set_active_fighter(self, user_id: str, fighter_name: str) -> dict[str, Any]:
        with self._connect() as connection:
            owned = connection.execute(
                "SELECT 1 FROM user_fighters WHERE user_id = ? AND fighter_name = ?",
                (user_id, fighter_name),
            ).fetchone()
            if owned is None:
                raise ValueError("\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272\u3002")
            connection.execute("UPDATE user_fighters SET is_active = 0 WHERE user_id = ?", (user_id,))
            connection.execute(
                "UPDATE user_fighters SET is_active = 1 WHERE user_id = ? AND fighter_name = ?",
                (user_id, fighter_name),
            )
            connection.commit()
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise RuntimeError("active fighter lookup failed")
        return fighter

    def create_fighter_for_user(self, user_id: str, fighter_name: str) -> dict[str, Any]:
        roster = self.get_user_fighters(user_id)
        if len(roster) >= MAX_FIGHTERS_PER_USER:
            raise ValueError("\u6bcf\u540d\u7528\u6237\u6700\u591a\u4fdd\u7559 3 \u4e2a\u89d2\u8272\u3002")
        fighter = self.generate_preview_fighter(fighter_name)
        self._insert_generated_fighter(fighter)
        slot_index = self._next_slot_index(roster)
        with self._connect() as connection:
            connection.execute("UPDATE user_fighters SET is_active = 0 WHERE user_id = ?", (user_id,))
            connection.execute(
                """
                INSERT INTO user_fighters (user_id, fighter_name, slot_index, is_active)
                VALUES (?, ?, ?, 1)
                """,
                (user_id, fighter_name, slot_index),
            )
            connection.commit()
        bound = self.get_user_fighter_by_name(user_id, fighter_name)
        if bound is None:
            raise RuntimeError("fighter binding failed")
        return bound

    def generate_preview_fighter(self, fighter_name: str) -> dict[str, Any]:
        if self.get_fighter_by_name(fighter_name) is not None:
            raise ValueError("\u89d2\u8272\u540d\u5df2\u5b58\u5728: " + fighter_name)
        return self._build_generated_fighter(fighter_name)

    def replace_fighter_for_user(
        self,
        user_id: str,
        slot_index: int,
        fighter_name: str | None = None,
        prepared_fighter: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT fighter_name FROM user_fighters WHERE user_id = ? AND slot_index = ?",
                (user_id, slot_index),
            ).fetchone()
            if row is None:
                raise ValueError("\u672a\u627e\u5230\u8981\u66ff\u6362\u7684\u89d2\u8272\u680f\u4f4d\u3002")
            old_name = str(row["fighter_name"])
            if prepared_fighter is None:
                if fighter_name is None:
                    raise ValueError("\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272\u3002")
                prepared_fighter = self.generate_preview_fighter(fighter_name)
            else:
                preview_name = str(prepared_fighter["name"])
                existing = self.get_fighter_by_name(preview_name)
                if existing is not None and preview_name != old_name:
                    raise ValueError("\u89d2\u8272\u540d\u5df2\u5b58\u5728: " + preview_name)

            connection.execute(
                "DELETE FROM user_fighters WHERE user_id = ? AND fighter_name = ?",
                (user_id, old_name),
            )
            connection.execute("DELETE FROM fighters WHERE name = ?", (old_name,))
            connection.execute("DELETE FROM fighter_scores WHERE fighter_name = ?", (old_name,))
            connection.execute(
                """
                INSERT INTO fighters (
                    name, hp, atk, def, spd, crt, eva,
                    martial_art_id, neigong_id, qinggong_id, star_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prepared_fighter["name"],
                    prepared_fighter["stats"]["hp"],
                    prepared_fighter["stats"]["atk"],
                    prepared_fighter["stats"]["def"],
                    prepared_fighter["stats"]["spd"],
                    prepared_fighter["stats"]["crt"],
                    prepared_fighter["stats"]["eva"],
                    prepared_fighter["martial_art_id"],
                    prepared_fighter["neigong_id"],
                    prepared_fighter["qinggong_id"],
                    prepared_fighter["star_rating"],
                ),
            )
            connection.execute("UPDATE user_fighters SET is_active = 0 WHERE user_id = ?", (user_id,))
            connection.execute(
                """
                INSERT INTO user_fighters (user_id, fighter_name, slot_index, is_active)
                VALUES (?, ?, ?, 1)
                """,
                (user_id, prepared_fighter["name"], slot_index),
            )
            connection.commit()

        bound = self.get_user_fighter_by_name(user_id, str(prepared_fighter["name"]))
        if bound is None:
            raise RuntimeError("fighter replacement failed")
        return old_name, bound

    def _next_slot_index(self, roster: list[dict[str, Any]]) -> int:
        used = {int(fighter.get("slot_index", 0)) for fighter in roster}
        for index in range(1, MAX_FIGHTERS_PER_USER + 1):
            if index not in used:
                return index
        raise ValueError("\u6bcf\u540d\u7528\u6237\u6700\u591a\u4fdd\u7559 3 \u4e2a\u89d2\u8272\u3002")

    def _delete_fighter_binding(self, user_id: str, fighter_name: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM user_fighters WHERE user_id = ? AND fighter_name = ?",
                (user_id, fighter_name),
            )
            connection.execute("DELETE FROM fighters WHERE name = ?", (fighter_name,))
            connection.execute("DELETE FROM fighter_scores WHERE fighter_name = ?", (fighter_name,))
            connection.commit()

    def record_group_battle(self, group_id: str, attacker_name: str, defender_name: str, winner_name: str | None) -> dict[str, dict[str, float | str]]:
        with self._connect() as connection:
            attacker_score = self._ensure_group_score_row(connection, group_id, attacker_name)
            defender_score = self._ensure_group_score_row(connection, group_id, defender_name)

            attacker_before = float(attacker_score["elo_rating"])
            defender_before = float(defender_score["elo_rating"])
            attacker_actual, defender_actual = self._elo_actual_scores(attacker_name, defender_name, winner_name)
            attacker_elo, defender_elo = self._calculate_elo_pair(
                attacker_before,
                defender_before,
                attacker_actual,
                defender_actual,
                int(attacker_score["battles"]),
                int(defender_score["battles"]),
            )

            for fighter_name in (attacker_name, defender_name):
                connection.execute(
                    "UPDATE fighters SET battles = battles + 1 WHERE name = ?",
                    (fighter_name,),
                )

            if winner_name is not None:
                connection.execute(
                    "UPDATE fighters SET wins = wins + 1 WHERE name = ?",
                    (winner_name,),
                )

            updates = [
                (attacker_name, attacker_actual, attacker_elo),
                (defender_name, defender_actual, defender_elo),
            ]
            for fighter_name, actual_score, elo_rating in updates:
                win_increment = 1 if actual_score == 1.0 else 0
                connection.execute(
                    """
                    UPDATE fighter_scores
                    SET wins = wins + ?,
                        battles = battles + 1,
                        elo_rating = ?
                    WHERE group_id = ? AND fighter_name = ?
                    """,
                    (win_increment, elo_rating, group_id, fighter_name),
                )
            connection.commit()

        return {
            "attacker": {
                "name": attacker_name,
                "before": round(attacker_before, 2),
                "after": round(attacker_elo, 2),
                "delta": round(attacker_elo - attacker_before, 2),
            },
            "defender": {
                "name": defender_name,
                "before": round(defender_before, 2),
                "after": round(defender_elo, 2),
                "delta": round(defender_elo - defender_before, 2),
            },
        }

    def _ensure_group_score_row(self, connection: sqlite3.Connection, group_id: str, fighter_name: str) -> sqlite3.Row:
        connection.execute(
            """
            INSERT INTO fighter_scores (group_id, fighter_name, wins, battles, elo_rating)
            VALUES (?, ?, 0, 0, ?)
            ON CONFLICT(group_id, fighter_name) DO NOTHING
            """,
            (group_id, fighter_name, ELO_INITIAL_RATING),
        )
        row = connection.execute(
            "SELECT wins, battles, elo_rating FROM fighter_scores WHERE group_id = ? AND fighter_name = ?",
            (group_id, fighter_name),
        ).fetchone()
        if row is None:
            raise RuntimeError("group score row missing")
        return row

    def _elo_expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

    def _elo_k_factor(self, battles: int) -> float:
        return ELO_NEWCOMER_K if battles < ELO_NEWCOMER_BATTLES else ELO_STABLE_K

    def _elo_actual_scores(self, attacker_name: str, defender_name: str, winner_name: str | None) -> tuple[float, float]:
        if winner_name is None:
            return 0.5, 0.5
        if winner_name == attacker_name:
            return 1.0, 0.0
        return 0.0, 1.0

    def _calculate_elo_pair(
        self,
        attacker_rating: float,
        defender_rating: float,
        attacker_actual: float,
        defender_actual: float,
        attacker_battles: int,
        defender_battles: int,
    ) -> tuple[float, float]:
        attacker_expected = self._elo_expected_score(attacker_rating, defender_rating)
        defender_expected = self._elo_expected_score(defender_rating, attacker_rating)
        attacker_new = attacker_rating + self._elo_k_factor(attacker_battles) * (attacker_actual - attacker_expected)
        defender_new = defender_rating + self._elo_k_factor(defender_battles) * (defender_actual - defender_expected)
        return round(attacker_new, 2), round(defender_new, 2)

    def get_group_leaderboard(self, group_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT fs.fighter_name, fs.wins, fs.battles, fs.elo_rating, uf.user_id
                FROM fighter_scores fs
                LEFT JOIN user_fighters uf ON uf.fighter_name = fs.fighter_name
                WHERE fs.group_id = ?
                ORDER BY fs.elo_rating DESC,
                         fs.battles DESC,
                         fs.wins DESC,
                         fs.fighter_name ASC
                LIMIT ?
                """,
                (group_id, limit),
            ).fetchall()
        return [
            {
                "fighter_name": str(row["fighter_name"]),
                "elo_rating": round(float(row["elo_rating"]), 2),
                "wins": int(row["wins"]),
                "battles": int(row["battles"]),
                "win_rate": 0.0 if int(row["battles"]) <= 0 else (int(row["wins"]) / int(row["battles"])) * 100.0,
                "user_id": None if row["user_id"] is None else str(row["user_id"]),
            }
            for row in rows
        ]

    def _build_generated_fighter(self, name: str) -> dict[str, Any]:
        rng = self._rng_for_name(name)
        martial_art = rng.choice(self.martial_arts)
        neigong = rng.choice(self.neigong)
        qinggong = rng.choice(self.qinggong)
        base_stats, star_rating = self._generate_base_stats(rng)
        final_stats = self._apply_modifiers(base_stats, martial_art, neigong, qinggong)
        return {
            "id": None,
            "name": name,
            "stats": final_stats,
            "martial_art_id": martial_art["id"],
            "neigong_id": neigong["id"],
            "qinggong_id": qinggong["id"],
            "weapon_id": None,
            "level": 1,
            "exp": 0,
            "wins": 0,
            "battles": 0,
            "star_rating": float(star_rating),
            "martial_art": martial_art,
            "neigong": neigong,
            "qinggong": qinggong,
        }

    def _insert_generated_fighter(self, fighter: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO fighters (
                    name, hp, atk, def, spd, crt, eva,
                    martial_art_id, neigong_id, qinggong_id, star_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fighter["name"],
                    fighter["stats"]["hp"],
                    fighter["stats"]["atk"],
                    fighter["stats"]["def"],
                    fighter["stats"]["spd"],
                    fighter["stats"]["crt"],
                    fighter["stats"]["eva"],
                    fighter["martial_art_id"],
                    fighter["neigong_id"],
                    fighter["qinggong_id"],
                    fighter["star_rating"],
                ),
            )
            connection.commit()

    def _rng_for_name(self, name: str) -> random.Random:
        normalized = name.strip().casefold().encode("utf-8")
        digest = hashlib.sha256(normalized).digest()
        seed = int.from_bytes(digest[:8], "big")
        return random.Random(seed)

    def _generate_base_stats(self, rng: random.Random) -> tuple[dict[str, float], float]:
        total_pool = rng.randint(340, 460)
        raw_stats = {
            "hp": rng.randint(110, 190),
            "atk": rng.randint(42, 96),
            "def": rng.randint(32, 88),
            "spd": rng.randint(22, 64),
            "crt": rng.randint(6, 26),
            "eva": rng.randint(6, 24),
        }
        scale = total_pool / sum(raw_stats.values())
        scaled = {key: value * scale for key, value in raw_stats.items()}
        scaled["crt"] = max(4.0, min(38.0, scaled["crt"]))
        scaled["eva"] = max(4.0, min(38.0, scaled["eva"]))
        return scaled, self._compute_star_rating(total_pool)

    def _compute_star_rating(self, total_pool: int) -> float:
        step = round((total_pool - 340) / 15)
        step = max(0, min(8, step))
        return 1.0 + (step * 0.5)

    def _apply_modifiers(
        self,
        base_stats: dict[str, float],
        martial_art: dict[str, Any],
        neigong: dict[str, Any],
        qinggong: dict[str, Any],
    ) -> dict[str, Any]:
        stats = dict(base_stats)
        martial_modifiers = martial_art.get("stat_modifiers", {})

        stats["atk"] *= martial_modifiers.get("atk", 1.0)
        stats["spd"] *= martial_modifiers.get("spd", 1.0)
        stats["crt"] *= martial_modifiers.get("crt", 1.0)
        stats["eva"] *= martial_modifiers.get("eva", 1.0)

        stats["hp"] *= neigong.get("hp_multiplier", 1.0)
        stats["def"] *= neigong.get("def_multiplier", 1.0)

        stats["spd"] *= qinggong.get("spd_multiplier", 1.0)
        stats["eva"] += qinggong.get("eva_bonus", 0.0)

        return {
            "hp": max(1, int(round(stats["hp"] * HP_BATTLE_SCALE))),
            "atk": max(1, int(round(stats["atk"]))),
            "def": max(1, int(round(stats["def"]))),
            "spd": round(max(1.0, stats["spd"]), 2),
            "crt": round(max(1.0, min(65.0, stats["crt"])), 2),
            "eva": round(max(1.0, min(65.0, stats["eva"])), 2),
        }

    def _hydrate_fighter(self, record: dict[str, Any]) -> dict[str, Any]:
        martial_art = self.martial_arts_map[record["martial_art_id"]]
        neigong = self.neigong_map[record["neigong_id"]]
        qinggong = self.qinggong_map[record["qinggong_id"]]
        return {
            "id": record["id"],
            "name": record["name"],
            "stats": {
                "hp": int(record["hp"]),
                "atk": int(record["atk"]),
                "def": int(record["def"]),
                "spd": float(record["spd"]),
                "crt": float(record["crt"]),
                "eva": float(record["eva"]),
            },
            "martial_art_id": record["martial_art_id"],
            "neigong_id": record["neigong_id"],
            "qinggong_id": record["qinggong_id"],
            "weapon_id": record["weapon_id"],
            "level": int(record["level"]),
            "exp": int(record["exp"]),
            "wins": int(record["wins"]),
            "battles": int(record["battles"]),
            "star_rating": float(record["star_rating"]),
            "martial_art": martial_art,
            "neigong": neigong,
            "qinggong": qinggong,
        }
