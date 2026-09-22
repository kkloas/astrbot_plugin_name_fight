# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import hashlib
import random
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configs"
LEGACY_DATA_DIR = BASE_DIR / "data"
HP_BATTLE_SCALE = 2.2
MAX_FIGHTERS_PER_USER = 5
TEAM3_TEAM_SIZE = 3
ELO_INITIAL_RATING = 1200.0
ELO_NEWCOMER_K = 112.0
ELO_STABLE_K = 80.0
ELO_NEWCOMER_BATTLES = 3
STAR_POOL_BY_RATING = {
    1.0: 340,
    1.5: 355,
    2.0: 370,
    2.5: 385,
    3.0: 400,
    3.5: 415,
    4.0: 430,
    4.5: 445,
    5.0: 460,
}
STAR_EXP_REQUIREMENTS = {
    1.0: 100,
    1.5: 140,
    2.0: 190,
    2.5: 250,
    3.0: 330,
    3.5: 400,
    4.0: 450,
    4.5: 540,
}
BREAKTHROUGH_STAGE_MAX = 1
INITIAL_SIX_STAR_CHANCE = 0.003
INNATE_SIX_STAR_POOL = 510
SIGNIN_POINTS = 50
ITEM_CATALOG = {
    "special_summon_token": {"name": "特殊召唤令", "price": 800, "category": "summon"},
    "star_exp_pill_s": {
        "name": "小星尘丹",
        "price": 45,
        "star_exp": 50,
        "category": "growth",
        "description": "用于角色培养, 增加 50 点星尘经验",
    },
    "star_exp_pill_m": {
        "name": "中星尘丹",
        "price": 90,
        "star_exp": 120,
        "category": "growth",
        "description": "用于角色培养, 增加 120 点星尘经验",
    },
    "breakthrough_pill": {
        "name": "破境丹",
        "price": 900,
        "category": "breakthrough",
        "description": "五星角色突破至六星时消耗",
    },
    "martial_token_basic": {
        "name": "洗髓符",
        "price": 220,
        "category": "martial_basic",
        "description": "用于随机更换角色武学",
    },
    "martial_token_type": {
        "name": "换宗令",
        "price": 420,
        "category": "martial_type",
        "description": "用于随机更换角色内功或轻功",
    },
    "martial_token_choice": {
        "name": "天机残卷",
        "price": 500,
        "category": "martial_choice",
        "description": "生成三个武学候选并选择其中一个",
    },
    "energy_pill": {
        "name": "行气丹",
        "price": 80,
        "energy_restore": 30,
        "category": "energy",
        "description": "使用后恢复 30 点历练体力, 最高恢复至 100",
    },
}
ITEM_NAME_TO_ID = {data["name"]: item_id for item_id, data in ITEM_CATALOG.items()}
BATTLE_POINT_REWARDS = {
    "accepted_1v1_win": 20,
    "accepted_1v1_loss": 8,
    "accepted_3v3_win": 40,
    "accepted_3v3_loss": 16,
}
WEEKLY_LEADERBOARD_REWARDS = {
    1: {"points": 500, "item_id": "martial_token_choice", "item_quantity": 1},
    2: {"points": 300, "item_id": "martial_token_type", "item_quantity": 1},
    3: {"points": 300, "item_id": "martial_token_type", "item_quantity": 1},
}
WEEKLY_LEADERBOARD_DEFAULT_POINTS = 150
DAILY_LEADERBOARD_REWARDS = {
    1: 90,
    2: 75,
    3: 60,
}
DAILY_LEADERBOARD_DEFAULT_POINTS = 30
WORLD_BOSS_KILL_REWARDS = {
    1: 300,
    2: 200,
    3: 120,
}
WORLD_BOSS_DEFAULT_POINTS = 50
BREAKTHROUGH_BONUS = {
    "hp": 1.10,
    "atk": 1.08,
    "def": 1.08,
    "spd": 1.05,
    "crt": 3.0,
    "eva": 3.0,
}


def _default_data_dir() -> Path:
    if BASE_DIR.parent.name == "plugins":
        return BASE_DIR.parent.parent / "name_fight_data"
    return BASE_DIR / "name_fight_data"


def _default_db_path() -> Path:
    return _default_data_dir() / "fighters.db"


def _legacy_db_path() -> Path:
    return LEGACY_DATA_DIR / "fighters.db"


WORLD_BOSS_KILL_PARTICIPATION_REWARD = {
    "points": 500,
    "items": {
        "special_summon_token": 2,
        "martial_token_choice": 2,
        "martial_token_type": 2,
        "star_exp_pill_m": 3,
        "star_exp_pill_s": 5,
    },
}


WORLD_BOSS_KILL_RANK_REWARDS = {
    1: {
        "points": 1500,
        "items": {
            "special_summon_token": 3,
            "martial_token_choice": 2,
            "star_exp_pill_m": 6,
        },
    },
    2: {
        "points": 1200,
        "items": {
            "special_summon_token": 2,
            "martial_token_choice": 1,
            "star_exp_pill_m": 5,
        },
    },
    3: {
        "points": 1000,
        "items": {
            "special_summon_token": 1,
            "martial_token_type": 2,
            "star_exp_pill_m": 4,
        },
    },
    4: {
        "points": 800,
        "items": {
            "martial_token_type": 2,
            "star_exp_pill_m": 3,
            "star_exp_pill_s": 4,
        },
    },
    5: {
        "points": 800,
        "items": {
            "martial_token_type": 2,
            "star_exp_pill_m": 3,
            "star_exp_pill_s": 4,
        },
    },
}


WORLD_BOSS_KILL_RANK_DEFAULT_REWARD = {
    "points": 500,
    "items": {
        "martial_token_type": 1,
        "star_exp_pill_m": 2,
        "star_exp_pill_s": 3,
    },
}


WORLD_BOSS_CLOSED_RANK_REWARDS = {
    1: {
        "points": 900,
        "items": {
            "special_summon_token": 1,
            "martial_token_choice": 1,
            "star_exp_pill_m": 4,
        },
    },
    2: {
        "points": 700,
        "items": {
            "martial_token_type": 2,
            "star_exp_pill_m": 3,
        },
    },
    3: {
        "points": 500,
        "items": {
            "martial_token_type": 1,
            "star_exp_pill_m": 2,
        },
    },
}


WORLD_BOSS_CLOSED_RANK_DEFAULT_REWARD = {
    "points": 300,
    "items": {
        "star_exp_pill_s": 3,
    },
}


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

    def _ensure_wallet_row(self, connection: sqlite3.Connection, user_id: str) -> sqlite3.Row:
        connection.execute(
            """
            INSERT INTO user_wallets (user_id, points, last_signin_date)
            VALUES (?, 0, '')
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id,),
        )
        row = connection.execute(
            "SELECT user_id, points, last_signin_date FROM user_wallets WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("wallet row missing")
        return row

    def get_user_points(self, user_id: str) -> int:
        with self._connect() as connection:
            row = self._ensure_wallet_row(connection, user_id)
        return int(row["points"])

    def get_user_wallet(self, user_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = self._ensure_wallet_row(connection, user_id)
        return {
            "user_id": str(row["user_id"]),
            "points": int(row["points"]),
            "last_signin_date": str(row["last_signin_date"] or ""),
        }

    def grant_points(self, user_id: str, amount: int) -> int:
        if amount <= 0:
            return self.get_user_points(user_id)
        with self._connect() as connection:
            row = self._ensure_wallet_row(connection, user_id)
            points = int(row["points"]) + int(amount)
            connection.execute(
                "UPDATE user_wallets SET points = ? WHERE user_id = ?",
                (points, user_id),
            )
            connection.commit()
        return points

    def transfer_points(self, sender_user_id: str, receiver_user_id: str, amount: int) -> dict[str, int]:
        if amount <= 0:
            raise ValueError("\u8d60\u9001\u79ef\u5206\u5fc5\u987b\u662f\u6b63\u6574\u6570")
        if sender_user_id == receiver_user_id:
            raise ValueError("\u4e0d\u80fd\u7ed9\u81ea\u5df1\u8d60\u9001\u79ef\u5206")
        with self._connect() as connection:
            sender_row = self._ensure_wallet_row(connection, sender_user_id)
            receiver_row = self._ensure_wallet_row(connection, receiver_user_id)
            sender_points = int(sender_row["points"])
            if sender_points < amount:
                raise ValueError("\u4f60\u7684\u79ef\u5206\u4e0d\u8db3")
            sender_points -= amount
            receiver_points = int(receiver_row["points"]) + amount
            connection.execute(
                "UPDATE user_wallets SET points = ? WHERE user_id = ?",
                (sender_points, sender_user_id),
            )
            connection.execute(
                "UPDATE user_wallets SET points = ? WHERE user_id = ?",
                (receiver_points, receiver_user_id),
            )
            connection.commit()
        return {
            "amount": amount,
            "sender_points": sender_points,
            "receiver_points": receiver_points,
        }

    def claim_daily_signin(self, user_id: str, today: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = self._ensure_wallet_row(connection, user_id)
            if str(row["last_signin_date"] or "") == today:
                raise ValueError("\u4eca\u5929\u5df2\u7ecf\u7b7e\u5230\u8fc7\u4e86")
            points = int(row["points"]) + SIGNIN_POINTS
            connection.execute(
                "UPDATE user_wallets SET points = ?, last_signin_date = ? WHERE user_id = ?",
                (points, today, user_id),
            )
            connection.commit()
        return {"points": points, "gained": SIGNIN_POINTS, "today": today}

    def get_shop_items(self) -> list[dict[str, Any]]:
        return [{"item_id": item_id, **data} for item_id, data in ITEM_CATALOG.items()]

    def get_item_catalog_entry(self, item_key: str) -> tuple[str, dict[str, Any]]:
        key = str(item_key).strip()
        if key in ITEM_CATALOG:
            return key, ITEM_CATALOG[key]
        if key in ITEM_NAME_TO_ID:
            item_id = ITEM_NAME_TO_ID[key]
            return item_id, ITEM_CATALOG[item_id]
        raise ValueError("\u672a\u77e5\u7684\u9053\u5177")

    def get_user_items(self, user_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT item_id, quantity FROM user_items WHERE user_id = ? AND quantity > 0 ORDER BY item_id ASC",
                (user_id,),
            ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            item_id = str(row["item_id"])
            data = ITEM_CATALOG.get(item_id, {"name": item_id, "price": 0, "category": "unknown"})
            items.append(
                {
                    "item_id": item_id,
                    "name": str(data.get("name", item_id)),
                    "price": int(data.get("price", 0)),
                    "quantity": int(row["quantity"]),
                    "category": str(data.get("category", "unknown")),
                }
            )
        return items

    def _change_item_quantity(self, connection: sqlite3.Connection, user_id: str, item_id: str, delta: int) -> int:
        row = connection.execute(
            "SELECT quantity FROM user_items WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        ).fetchone()
        current = 0 if row is None else int(row["quantity"])
        updated = current + int(delta)
        if updated < 0:
            raise ValueError("\u80cc\u5305\u9053\u5177\u6570\u91cf\u4e0d\u8db3")
        if row is None:
            connection.execute(
                "INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, ?)",
                (user_id, item_id, updated),
            )
        else:
            connection.execute(
                "UPDATE user_items SET quantity = ? WHERE user_id = ? AND item_id = ?",
                (updated, user_id, item_id),
            )
        return updated

    def buy_item(self, user_id: str, item_key: str, quantity: int = 1) -> dict[str, Any]:
        item_id, data = self.get_item_catalog_entry(item_key)
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("\u6570\u91cf\u5fc5\u987b\u5927\u4e8e 0")
        total_cost = int(data.get("price", 0)) * quantity
        with self._connect() as connection:
            row = self._ensure_wallet_row(connection, user_id)
            points = int(row["points"])
            if points < total_cost:
                raise ValueError("\u79ef\u5206\u4e0d\u8db3")
            points -= total_cost
            connection.execute(
                "UPDATE user_wallets SET points = ? WHERE user_id = ?",
                (points, user_id),
            )
            bag_count = self._change_item_quantity(connection, user_id, item_id, quantity)
            connection.commit()
        return {
            "item_id": item_id,
            "item_name": str(data["name"]),
            "quantity": quantity,
            "bag_quantity": bag_count,
            "points": points,
            "cost": total_cost,
        }

    def _ensure_pve_profile(self, connection: sqlite3.Connection, user_id: str, maximum_energy: int, now: int) -> sqlite3.Row:
        connection.execute(
            """
            INSERT INTO pve_profiles (user_id, energy, energy_updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id, int(maximum_energy), int(now)),
        )
        row = connection.execute(
            """
            SELECT user_id, energy, energy_updated_at, team_slot1, team_slot2, team_slot3
            FROM pve_profiles
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("PVE profile row missing")
        return row

    def _refresh_pve_energy(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        maximum_energy: int,
        recovery_seconds: int,
        now: int,
    ) -> sqlite3.Row:
        energy = min(int(maximum_energy), max(0, int(row["energy"])))
        updated_at = min(int(now), int(row["energy_updated_at"]))
        if energy >= int(maximum_energy):
            next_energy = int(maximum_energy)
            next_updated_at = int(now)
        else:
            recovered = max(0, int(now) - updated_at) // max(1, int(recovery_seconds))
            next_energy = min(int(maximum_energy), energy + recovered)
            next_updated_at = updated_at + recovered * max(1, int(recovery_seconds))
            if next_energy >= int(maximum_energy):
                next_updated_at = int(now)
        if next_energy != int(row["energy"]) or next_updated_at != int(row["energy_updated_at"]):
            connection.execute(
                "UPDATE pve_profiles SET energy = ?, energy_updated_at = ? WHERE user_id = ?",
                (next_energy, next_updated_at, str(row["user_id"])),
            )
        refreshed = connection.execute(
            """
            SELECT user_id, energy, energy_updated_at, team_slot1, team_slot2, team_slot3
            FROM pve_profiles
            WHERE user_id = ?
            """,
            (str(row["user_id"]),),
        ).fetchone()
        if refreshed is None:
            raise RuntimeError("PVE profile refresh failed")
        return refreshed

    def _pve_profile_payload(
        self,
        row: sqlite3.Row,
        maximum_energy: int,
        recovery_seconds: int,
        now: int,
    ) -> dict[str, Any]:
        energy = int(row["energy"])
        updated_at = int(row["energy_updated_at"])
        next_recovery_at = None
        if energy < int(maximum_energy):
            next_recovery_at = updated_at + max(1, int(recovery_seconds))
        slots = [row["team_slot1"], row["team_slot2"], row["team_slot3"]]
        return {
            "user_id": str(row["user_id"]),
            "energy": energy,
            "maximum_energy": int(maximum_energy),
            "recovery_seconds": int(recovery_seconds),
            "energy_updated_at": updated_at,
            "next_recovery_at": next_recovery_at,
            "server_time": int(now),
            "team_slots": [int(slot) for slot in slots if slot is not None],
        }

    def get_pve_profile(
        self,
        user_id: str,
        maximum_energy: int = 100,
        recovery_seconds: int = 360,
        now: int | None = None,
    ) -> dict[str, Any]:
        timestamp = int(time.time()) if now is None else int(now)
        with self._connect() as connection:
            row = self._ensure_pve_profile(connection, user_id, maximum_energy, timestamp)
            row = self._refresh_pve_energy(connection, row, maximum_energy, recovery_seconds, timestamp)
            connection.commit()
        return self._pve_profile_payload(row, maximum_energy, recovery_seconds, timestamp)

    def use_pve_energy_item(
        self,
        user_id: str,
        item_key: str,
        maximum_energy: int = 100,
        recovery_seconds: int = 360,
        now: int | None = None,
    ) -> dict[str, Any]:
        item_id, data = self.get_item_catalog_entry(item_key)
        restore_amount = int(data.get("energy_restore", 0))
        if restore_amount <= 0:
            raise ValueError("该道具不能恢复历练体力")
        timestamp = int(time.time()) if now is None else int(now)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            profile = self._ensure_pve_profile(connection, user_id, maximum_energy, timestamp)
            profile = self._refresh_pve_energy(
                connection,
                profile,
                maximum_energy,
                recovery_seconds,
                timestamp,
            )
            current_energy = int(profile["energy"])
            if current_energy >= int(maximum_energy):
                raise ValueError("历练体力已满")
            item_row = connection.execute(
                "SELECT quantity FROM user_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            ).fetchone()
            if item_row is None or int(item_row["quantity"]) <= 0:
                raise ValueError("背包道具数量不足")
            restored = min(restore_amount, int(maximum_energy) - current_energy)
            next_energy = current_energy + restored
            next_updated_at = timestamp if next_energy >= int(maximum_energy) else int(profile["energy_updated_at"])
            remaining = self._change_item_quantity(connection, user_id, item_id, -1)
            connection.execute(
                "UPDATE pve_profiles SET energy = ?, energy_updated_at = ? WHERE user_id = ?",
                (next_energy, next_updated_at, user_id),
            )
            profile = connection.execute(
                """
                SELECT user_id, energy, energy_updated_at, team_slot1, team_slot2, team_slot3
                FROM pve_profiles WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            connection.commit()
        if profile is None:
            raise RuntimeError("PVE energy item update failed")
        return {
            "item_id": item_id,
            "item_name": str(data["name"]),
            "restored": restored,
            "remaining": remaining,
            "profile": self._pve_profile_payload(profile, maximum_energy, recovery_seconds, timestamp),
        }

    def set_pve_team(
        self,
        user_id: str,
        slots: list[int] | tuple[int, int, int],
        maximum_energy: int = 100,
        recovery_seconds: int = 360,
        now: int | None = None,
    ) -> dict[str, Any]:
        normalized = [int(slot) for slot in slots]
        if len(normalized) != 3 or len(set(normalized)) != 3:
            raise ValueError("PVE 出战队伍必须选择三个不重复的角色槽位")
        if any(slot < 1 or slot > MAX_FIGHTERS_PER_USER for slot in normalized):
            raise ValueError(f"角色槽位只能在 1 到 {MAX_FIGHTERS_PER_USER} 之间")
        timestamp = int(time.time()) if now is None else int(now)
        with self._connect() as connection:
            placeholders = ",".join("?" for _ in normalized)
            rows = connection.execute(
                f"SELECT slot_index FROM user_fighters WHERE user_id = ? AND slot_index IN ({placeholders})",
                (user_id, *normalized),
            ).fetchall()
            if {int(row["slot_index"]) for row in rows} != set(normalized):
                raise ValueError("所选槽位中存在空位")
            row = self._ensure_pve_profile(connection, user_id, maximum_energy, timestamp)
            row = self._refresh_pve_energy(connection, row, maximum_energy, recovery_seconds, timestamp)
            connection.execute(
                """
                UPDATE pve_profiles
                SET team_slot1 = ?, team_slot2 = ?, team_slot3 = ?
                WHERE user_id = ?
                """,
                (normalized[0], normalized[1], normalized[2], user_id),
            )
            connection.commit()
            row = connection.execute(
                """
                SELECT user_id, energy, energy_updated_at, team_slot1, team_slot2, team_slot3
                FROM pve_profiles WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError("PVE team update failed")
        return self._pve_profile_payload(row, maximum_energy, recovery_seconds, timestamp)

    def get_pve_stage_progress(self, user_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT stage_id, best_stars, clear_count, first_cleared_at, last_cleared_at
                FROM pve_stage_progress
                WHERE user_id = ?
                ORDER BY stage_id ASC
                """,
                (user_id,),
            ).fetchall()
        return [
            {
                "stage_id": str(row["stage_id"]),
                "best_stars": int(row["best_stars"]),
                "clear_count": int(row["clear_count"]),
                "first_cleared_at": None if row["first_cleared_at"] is None else int(row["first_cleared_at"]),
                "last_cleared_at": None if row["last_cleared_at"] is None else int(row["last_cleared_at"]),
            }
            for row in rows
        ]

    def get_pve_claimed_rewards(self, user_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chapter_id, star_threshold, claimed_at
                FROM pve_chapter_rewards
                WHERE user_id = ?
                ORDER BY chapter_id ASC, star_threshold ASC
                """,
                (user_id,),
            ).fetchall()
        return [
            {
                "chapter_id": str(row["chapter_id"]),
                "star_threshold": int(row["star_threshold"]),
                "claimed_at": int(row["claimed_at"]),
            }
            for row in rows
        ]

    def _grant_pve_reward(
        self,
        connection: sqlite3.Connection,
        user_id: str,
        reward: dict[str, Any],
    ) -> dict[str, Any]:
        points = max(0, int(reward.get("points", 0)))
        wallet = self._ensure_wallet_row(connection, user_id)
        wallet_points = int(wallet["points"]) + points
        connection.execute("UPDATE user_wallets SET points = ? WHERE user_id = ?", (wallet_points, user_id))
        granted_items: list[dict[str, Any]] = []
        for item in reward.get("items", []):
            item_id = str(item.get("item_id") or "")
            quantity = int(item.get("quantity", 0))
            if not item_id or quantity <= 0:
                continue
            if item_id not in ITEM_CATALOG:
                raise ValueError(f"未知的 PVE 奖励道具: {item_id}")
            bag_quantity = self._change_item_quantity(connection, user_id, item_id, quantity)
            granted_items.append({
                "item_id": item_id,
                "name": str(ITEM_CATALOG[item_id]["name"]),
                "quantity": quantity,
                "bag_quantity": bag_quantity,
            })
        return {"points": points, "wallet_points": wallet_points, "items": granted_items}

    def settle_pve_attempt(
        self,
        user_id: str,
        stage_id: str,
        energy_cost: int,
        victory: bool,
        stars: int,
        first_clear_reward: dict[str, Any],
        repeat_reward: dict[str, Any],
        maximum_energy: int = 100,
        recovery_seconds: int = 360,
        now: int | None = None,
    ) -> dict[str, Any]:
        timestamp = int(time.time()) if now is None else int(now)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            profile = self._ensure_pve_profile(connection, user_id, maximum_energy, timestamp)
            profile = self._refresh_pve_energy(connection, profile, maximum_energy, recovery_seconds, timestamp)
            if int(profile["energy"]) < int(energy_cost):
                raise ValueError("体力不足")
            connection.execute(
                "UPDATE pve_profiles SET energy = energy - ? WHERE user_id = ?",
                (int(energy_cost), user_id),
            )
            progress = connection.execute(
                """
                SELECT best_stars, clear_count, first_cleared_at
                FROM pve_stage_progress
                WHERE user_id = ? AND stage_id = ?
                """,
                (user_id, stage_id),
            ).fetchone()
            was_cleared = progress is not None and int(progress["clear_count"]) > 0
            reward_payload = {"points": 0, "wallet_points": int(self._ensure_wallet_row(connection, user_id)["points"]), "items": []}
            best_stars = 0 if progress is None else int(progress["best_stars"])
            clear_count = 0 if progress is None else int(progress["clear_count"])
            first_clear = bool(victory and not was_cleared)
            if victory:
                best_stars = max(best_stars, max(1, min(3, int(stars))))
                clear_count += 1
                first_cleared_at = timestamp if progress is None or progress["first_cleared_at"] is None else int(progress["first_cleared_at"])
                connection.execute(
                    """
                    INSERT INTO pve_stage_progress (
                        user_id, stage_id, best_stars, clear_count, first_cleared_at, last_cleared_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, stage_id) DO UPDATE SET
                        best_stars = MAX(pve_stage_progress.best_stars, excluded.best_stars),
                        clear_count = pve_stage_progress.clear_count + 1,
                        first_cleared_at = COALESCE(pve_stage_progress.first_cleared_at, excluded.first_cleared_at),
                        last_cleared_at = excluded.last_cleared_at
                    """,
                    (user_id, stage_id, best_stars, 1, first_cleared_at, timestamp),
                )
                reward_payload = self._grant_pve_reward(
                    connection,
                    user_id,
                    first_clear_reward if first_clear else repeat_reward,
                )
            profile = connection.execute(
                """
                SELECT user_id, energy, energy_updated_at, team_slot1, team_slot2, team_slot3
                FROM pve_profiles WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            connection.commit()
        if profile is None:
            raise RuntimeError("PVE settlement profile missing")
        return {
            "first_clear": first_clear,
            "best_stars": best_stars,
            "clear_count": clear_count,
            "reward": reward_payload,
            "profile": self._pve_profile_payload(profile, maximum_energy, recovery_seconds, timestamp),
        }

    def claim_pve_chapter_reward(
        self,
        user_id: str,
        chapter_id: str,
        stage_ids: list[str],
        star_threshold: int,
        reward: dict[str, Any],
        now: int | None = None,
    ) -> dict[str, Any]:
        timestamp = int(time.time()) if now is None else int(now)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            placeholders = ",".join("?" for _ in stage_ids)
            row = connection.execute(
                f"SELECT COALESCE(SUM(best_stars), 0) AS stars FROM pve_stage_progress WHERE user_id = ? AND stage_id IN ({placeholders})",
                (user_id, *stage_ids),
            ).fetchone()
            total_stars = 0 if row is None else int(row["stars"])
            if total_stars < int(star_threshold):
                raise ValueError(f"章节星数不足，需要 {int(star_threshold)} 星")
            existing = connection.execute(
                """
                SELECT 1 FROM pve_chapter_rewards
                WHERE user_id = ? AND chapter_id = ? AND star_threshold = ?
                """,
                (user_id, chapter_id, int(star_threshold)),
            ).fetchone()
            if existing is not None:
                raise ValueError("该章节宝箱已经领取")
            reward_payload = self._grant_pve_reward(connection, user_id, reward)
            connection.execute(
                """
                INSERT INTO pve_chapter_rewards (user_id, chapter_id, star_threshold, claimed_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, chapter_id, int(star_threshold), timestamp),
            )
            connection.commit()
        return {
            "chapter_id": chapter_id,
            "star_threshold": int(star_threshold),
            "chapter_stars": total_stars,
            "claimed_at": timestamp,
            "reward": reward_payload,
        }

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
                    star_rating REAL NOT NULL DEFAULT 3.0,
                    base_star_rating REAL NOT NULL DEFAULT 3.0,
                    star_exp INTEGER NOT NULL DEFAULT 0,
                    breakthrough_stage INTEGER NOT NULL DEFAULT 0,
                    martial_reroll_count INTEGER NOT NULL DEFAULT 0,
                    raw_hp REAL DEFAULT NULL,
                    raw_atk REAL DEFAULT NULL,
                    raw_def REAL DEFAULT NULL,
                    raw_spd REAL DEFAULT NULL,
                    raw_crt REAL DEFAULT NULL,
                    raw_eva REAL DEFAULT NULL,
                    avatar_path TEXT DEFAULT NULL
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS team3_orders (
                    user_id TEXT PRIMARY KEY,
                    slot1 INTEGER NOT NULL DEFAULT 1,
                    slot2 INTEGER NOT NULL DEFAULT 2,
                    slot3 INTEGER NOT NULL DEFAULT 3
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS team3_scores (
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    display_name TEXT NOT NULL DEFAULT '',
                    wins INTEGER NOT NULL DEFAULT 0,
                    battles INTEGER NOT NULL DEFAULT 0,
                    elo_rating REAL NOT NULL DEFAULT 1200.0,
                    PRIMARY KEY (group_id, user_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS group_user_labels (
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    display_name TEXT NOT NULL DEFAULT '',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, user_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_wallets (
                    user_id TEXT PRIMARY KEY,
                    points INTEGER NOT NULL DEFAULT 0,
                    last_signin_date TEXT DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_items (
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, item_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS weekly_settlements (
                    group_id TEXT NOT NULL,
                    board_type TEXT NOT NULL,
                    week_key TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    settled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, board_type, week_key)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_settlements (
                    group_id TEXT NOT NULL,
                    board_type TEXT NOT NULL,
                    day_key TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    settled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, board_type, day_key)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS group_boss_activities (
                    boss_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    boss_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    phase1_payload TEXT NOT NULL,
                    phase2_payload TEXT NOT NULL,
                    phase2_max_hp INTEGER NOT NULL,
                    phase2_current_hp INTEGER NOT NULL,
                    created_by TEXT NOT NULL DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    closed_at DATETIME DEFAULT NULL,
                    killed_at DATETIME DEFAULT NULL,
                    settled_at DATETIME DEFAULT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS group_boss_contributions (
                    boss_id INTEGER NOT NULL,
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    display_name TEXT NOT NULL DEFAULT '',
                    total_damage INTEGER NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_attempt_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (boss_id, group_id, user_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS group_boss_attempts (
                    boss_id INTEGER NOT NULL,
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    day_key TEXT NOT NULL,
                    used_attempts INTEGER NOT NULL DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (boss_id, group_id, user_id, day_key)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS group_boss_settlements (
                    boss_id INTEGER NOT NULL,
                    group_id TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    settled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (boss_id, group_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pve_profiles (
                    user_id TEXT PRIMARY KEY,
                    energy INTEGER NOT NULL DEFAULT 100,
                    energy_updated_at INTEGER NOT NULL,
                    team_slot1 INTEGER DEFAULT NULL,
                    team_slot2 INTEGER DEFAULT NULL,
                    team_slot3 INTEGER DEFAULT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pve_stage_progress (
                    user_id TEXT NOT NULL,
                    stage_id TEXT NOT NULL,
                    best_stars INTEGER NOT NULL DEFAULT 0,
                    clear_count INTEGER NOT NULL DEFAULT 0,
                    first_cleared_at INTEGER DEFAULT NULL,
                    last_cleared_at INTEGER DEFAULT NULL,
                    PRIMARY KEY (user_id, stage_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pve_chapter_rewards (
                    user_id TEXT NOT NULL,
                    chapter_id TEXT NOT NULL,
                    star_threshold INTEGER NOT NULL,
                    claimed_at INTEGER NOT NULL,
                    PRIMARY KEY (user_id, chapter_id, star_threshold)
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
            if "base_star_rating" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN base_star_rating REAL NOT NULL DEFAULT 3.0")
            if "star_exp" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN star_exp INTEGER NOT NULL DEFAULT 0")
            if "breakthrough_stage" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN breakthrough_stage INTEGER NOT NULL DEFAULT 0")
            if "martial_reroll_count" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN martial_reroll_count INTEGER NOT NULL DEFAULT 0")
            for column_name in ("raw_hp", "raw_atk", "raw_def", "raw_spd", "raw_crt", "raw_eva"):
                if column_name not in fighter_columns:
                    connection.execute(f"ALTER TABLE fighters ADD COLUMN {column_name} REAL DEFAULT NULL")
            if "avatar_path" not in fighter_columns:
                connection.execute("ALTER TABLE fighters ADD COLUMN avatar_path TEXT DEFAULT NULL")
            connection.execute("UPDATE fighters SET base_star_rating = MIN(star_rating, 5.0) WHERE base_star_rating <= 0")
            connection.execute("UPDATE fighters SET base_star_rating = MIN(star_rating, 5.0) WHERE base_star_rating IS NULL")
            connection.execute(
                """
                UPDATE fighters
                SET base_star_rating = CASE
                    WHEN star_rating >= 6.0 THEN 5.0
                    ELSE star_rating
                END
                WHERE base_star_rating = 3.0
                  AND (ABS(COALESCE(star_rating, 3.0) - 3.0) > 0.001 OR breakthrough_stage > 0)
                """
            )
            connection.execute("UPDATE fighters SET breakthrough_stage = 0 WHERE star_rating >= 6.0 AND base_star_rating >= 6.0")
            connection.execute("UPDATE fighters SET breakthrough_stage = 1 WHERE star_rating >= 6.0 AND breakthrough_stage <= 0 AND base_star_rating < 6.0")
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

    def _normalize_team3_order(self, order: list[int] | tuple[int, int, int]) -> list[int]:
        normalized = [int(item) for item in order]
        if len(normalized) != TEAM3_TEAM_SIZE:
            raise ValueError("3v3 出战顺序必须刚好填 3 个槽位")
        if any(item < 1 or item > MAX_FIGHTERS_PER_USER for item in normalized):
            raise ValueError(f"3v3 出战顺序只能从 1 到 {MAX_FIGHTERS_PER_USER} 号位里选 3 个")
        if len(set(normalized)) != TEAM3_TEAM_SIZE:
            raise ValueError("3v3 出战顺序不能重复选择槽位")
        return normalized

    def get_user_team3_order(self, user_id: str) -> list[int]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT slot1, slot2, slot3 FROM team3_orders WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return [1, 2, 3]
        return self._normalize_team3_order([int(row["slot1"]), int(row["slot2"]), int(row["slot3"])])

    def set_user_team3_order(self, user_id: str, order: list[int] | tuple[int, int, int]) -> list[int]:
        normalized = self._normalize_team3_order(order)
        roster = self.get_user_fighters(user_id)
        fighters_by_slot = {int(fighter.get("slot_index", 0)): fighter for fighter in roster}
        missing_slots = [slot for slot in normalized if slot not in fighters_by_slot]
        if missing_slots:
            missing_text = ", ".join(str(slot) for slot in missing_slots)
            raise ValueError(f"你选的 3v3 槽位里有空位: {missing_text}")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO team3_orders (user_id, slot1, slot2, slot3)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    slot1 = excluded.slot1,
                    slot2 = excluded.slot2,
                    slot3 = excluded.slot3
                """,
                (user_id, normalized[0], normalized[1], normalized[2]),
            )
            connection.commit()
        return normalized

    def get_user_team3_fighters(self, user_id: str) -> list[dict[str, Any]]:
        roster = self.get_user_fighters(user_id)
        fighters_by_slot = {int(fighter.get("slot_index", 0)): fighter for fighter in roster}
        order = self.get_user_team3_order(user_id)
        return [fighters_by_slot[slot] for slot in order if slot in fighters_by_slot]

    def _exp_needed_to_next_star(self, star_rating: float, star_exp: int) -> int:
        requirement = STAR_EXP_REQUIREMENTS[self._star_rating_key(star_rating)]
        return max(0, requirement - int(star_exp))

    def _exp_needed_to_five_star(self, star_rating: float, star_exp: int) -> int:
        current_star = float(star_rating)
        current_exp = int(star_exp)
        total_need = 0
        while current_star < 5.0:
            total_need += self._exp_needed_to_next_star(current_star, current_exp)
            current_star = round(current_star + 0.5, 1)
            current_exp = 0
        return total_need

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


    def set_fighter_avatar_path(self, user_id: str, fighter_name: str, avatar_path: str | None) -> dict[str, Any]:
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError("你名下没有这个角色。")
        with self._connect() as connection:
            connection.execute(
                "UPDATE fighters SET avatar_path = ? WHERE name = ?",
                (avatar_path, fighter_name),
            )
            connection.commit()
        updated = self.get_user_fighter_by_name(user_id, fighter_name)
        if updated is None:
            raise RuntimeError("fighter avatar update failed")
        return updated

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

    def create_fighter_for_user(
        self,
        user_id: str,
        fighter_name: str,
        forced_base_star: float | None = None,
    ) -> dict[str, Any]:
        roster = self.get_user_fighters(user_id)
        if len(roster) >= MAX_FIGHTERS_PER_USER:
            raise ValueError(f"\u6bcf\u540d\u7528\u6237\u6700\u591a\u4fdd\u7559 {MAX_FIGHTERS_PER_USER} \u4e2a\u89d2\u8272\u3002")
        fighter = self.generate_preview_fighter(fighter_name, forced_base_star=forced_base_star)
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

    def generate_preview_fighter(
        self,
        fighter_name: str,
        forced_base_star: float | None = None,
    ) -> dict[str, Any]:
        if self.get_fighter_by_name(fighter_name) is not None:
            raise ValueError("\u89d2\u8272\u540d\u5df2\u5b58\u5728: " + fighter_name)
        return self._build_generated_fighter(fighter_name, forced_base_star=forced_base_star)

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
            raw_stats = prepared_fighter["raw_stats"]
            connection.execute(
                """
                INSERT INTO fighters (
                    name, hp, atk, def, spd, crt, eva,
                    martial_art_id, neigong_id, qinggong_id, star_rating,
                    base_star_rating, star_exp, breakthrough_stage, martial_reroll_count,
                    raw_hp, raw_atk, raw_def, raw_spd, raw_crt, raw_eva, avatar_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    prepared_fighter["base_star_rating"],
                    prepared_fighter["star_exp"],
                    prepared_fighter["breakthrough_stage"],
                    prepared_fighter["martial_reroll_count"],
                    raw_stats["hp"],
                    raw_stats["atk"],
                    raw_stats["def"],
                    raw_stats["spd"],
                    raw_stats["crt"],
                    raw_stats["eva"],
                    prepared_fighter.get("avatar_path"),
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
        raise ValueError(f"\u6bcf\u540d\u7528\u6237\u6700\u591a\u4fdd\u7559 {MAX_FIGHTERS_PER_USER} \u4e2a\u89d2\u8272\u3002")

    def _delete_fighter_binding(self, user_id: str, fighter_name: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM user_fighters WHERE user_id = ? AND fighter_name = ?",
                (user_id, fighter_name),
            )
            connection.execute("DELETE FROM fighters WHERE name = ?", (fighter_name,))
            connection.execute("DELETE FROM fighter_scores WHERE fighter_name = ?", (fighter_name,))
            connection.commit()

    def record_group_battle(
        self,
        group_id: str,
        attacker_name: str,
        defender_name: str,
        winner_name: str | None,
        elo_scale: float = 1.0,
    ) -> dict[str, dict[str, float | str]]:
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
            attacker_elo = attacker_before + (attacker_elo - attacker_before) * float(elo_scale)
            defender_elo = defender_before + (defender_elo - defender_before) * float(elo_scale)

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

    def record_group_team3_battle(
        self,
        group_id: str,
        attacker_user_id: str,
        attacker_label: str,
        defender_user_id: str,
        defender_label: str,
        winner_user_id: str | None,
        elo_scale: float = 1.0,
    ) -> dict[str, dict[str, float | str]]:
        with self._connect() as connection:
            attacker_score = self._ensure_group_team3_score_row(connection, group_id, attacker_user_id, attacker_label)
            defender_score = self._ensure_group_team3_score_row(connection, group_id, defender_user_id, defender_label)

            attacker_before = float(attacker_score["elo_rating"])
            defender_before = float(defender_score["elo_rating"])
            attacker_actual, defender_actual = self._elo_actual_scores(attacker_user_id, defender_user_id, winner_user_id)
            attacker_elo, defender_elo = self._calculate_elo_pair(
                attacker_before,
                defender_before,
                attacker_actual,
                defender_actual,
                int(attacker_score["battles"]),
                int(defender_score["battles"]),
            )
            attacker_elo = attacker_before + (attacker_elo - attacker_before) * float(elo_scale)
            defender_elo = defender_before + (defender_elo - defender_before) * float(elo_scale)

            updates = [
                (attacker_user_id, attacker_label, attacker_actual, attacker_elo),
                (defender_user_id, defender_label, defender_actual, defender_elo),
            ]
            for user_id, display_name, actual_score, elo_rating in updates:
                win_increment = 1 if actual_score == 1.0 else 0
                connection.execute(
                    """
                    UPDATE team3_scores
                    SET display_name = ?,
                        wins = wins + ?,
                        battles = battles + 1,
                        elo_rating = ?
                    WHERE group_id = ? AND user_id = ?
                    """,
                    (display_name, win_increment, elo_rating, group_id, user_id),
                )
            connection.commit()

        return {
            "attacker": {
                "name": attacker_label,
                "before": round(attacker_before, 2),
                "after": round(attacker_elo, 2),
                "delta": round(attacker_elo - attacker_before, 2),
            },
            "defender": {
                "name": defender_label,
                "before": round(defender_before, 2),
                "after": round(defender_elo, 2),
                "delta": round(defender_elo - defender_before, 2),
            },
        }

    def _ensure_group_team3_score_row(
        self,
        connection: sqlite3.Connection,
        group_id: str,
        user_id: str,
        display_name: str,
    ) -> sqlite3.Row:
        connection.execute(
            """
            INSERT INTO team3_scores (group_id, user_id, display_name, wins, battles, elo_rating)
            VALUES (?, ?, ?, 0, 0, ?)
            ON CONFLICT(group_id, user_id) DO NOTHING
            """,
            (group_id, user_id, display_name, ELO_INITIAL_RATING),
        )
        row = connection.execute(
            "SELECT display_name, wins, battles, elo_rating FROM team3_scores WHERE group_id = ? AND user_id = ?",
            (group_id, user_id),
        ).fetchone()
        if row is None:
            raise RuntimeError("team3 score row missing")
        return row


    def set_group_user_label(self, group_id: str, user_id: str, display_name: str) -> None:
        name = str(display_name).strip()
        if not name:
            return
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO group_user_labels (group_id, user_id, display_name)
                VALUES (?, ?, ?)
                ON CONFLICT(group_id, user_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (group_id, user_id, name),
            )
            connection.commit()

    def get_group_user_label(self, group_id: str, user_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT display_name FROM group_user_labels WHERE group_id = ? AND user_id = ?",
                (group_id, user_id),
            ).fetchone()
        if row is None:
            return None
        name = str(row["display_name"] or "").strip()
        return name or None

    def get_group_team3_leaderboard(self, group_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT user_id, display_name, wins, battles, elo_rating
                FROM team3_scores
                WHERE group_id = ?
                ORDER BY elo_rating DESC,
                         battles DESC,
                         wins DESC,
                         user_id ASC
                LIMIT ?
                """,
                (group_id, limit),
            ).fetchall()
        entries: list[dict[str, Any]] = []
        for row in rows:
            user_id = str(row["user_id"])
            fighters = self.get_user_team3_fighters(user_id)
            team_names = [fighter["name"] for fighter in fighters]
            entries.append(
                {
                    "user_id": user_id,
                    "display_name": self.get_group_user_label(group_id, user_id) or str(row["display_name"] or user_id),
                    "elo_rating": round(float(row["elo_rating"]), 2),
                    "wins": int(row["wins"]),
                    "battles": int(row["battles"]),
                    "win_rate": 0.0 if int(row["battles"]) <= 0 else (int(row["wins"]) / int(row["battles"])) * 100.0,
                    "team_names": team_names,
                }
            )
        return entries

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

    def _grant_item_direct(self, user_id: str, item_id: str, quantity: int) -> int:
        with self._connect() as connection:
            updated = self._change_item_quantity(connection, user_id, item_id, quantity)
            connection.commit()
        return updated

    def get_tracked_group_ids(self, board_type: str | None = None) -> list[str]:
        with self._connect() as connection:
            group_ids: set[str] = set()
            if board_type in (None, "1v1"):
                rows = connection.execute("SELECT DISTINCT group_id FROM fighter_scores").fetchall()
                group_ids.update(str(row["group_id"]) for row in rows if row["group_id"] not in (None, ""))
            if board_type in (None, "3v3"):
                rows = connection.execute("SELECT DISTINCT group_id FROM team3_scores").fetchall()
                group_ids.update(str(row["group_id"]) for row in rows if row["group_id"] not in (None, ""))
        return sorted(group_ids)

    def has_daily_settlement(self, group_id: str, board_type: str, day_key: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM daily_settlements WHERE group_id = ? AND board_type = ? AND day_key = ?",
                (group_id, board_type, day_key),
            ).fetchone()
        return row is not None

    def settle_daily_leaderboard(self, group_id: str, board_type: str, day_key: str) -> dict[str, Any]:
        board = str(board_type).strip().lower()
        if board not in ("1v1", "3v3"):
            raise ValueError("\u6392\u884c\u699c\u7c7b\u578b\u53ea\u80fd\u662f 1v1 \u6216 3v3")
        if self.has_daily_settlement(group_id, board, day_key):
            raise ValueError(f"\u672c\u7fa4 {day_key} \u7684 {board} \u65e5\u699c\u5df2\u7ecf\u7ed3\u7b97\u8fc7\u4e86")

        entries = self.get_group_leaderboard(group_id, limit=10) if board == "1v1" else self.get_group_team3_leaderboard(group_id, limit=10)
        rewards: list[dict[str, Any]] = []
        for index, entry in enumerate(entries, start=1):
            user_id = entry.get("user_id")
            if not user_id:
                continue
            points = int(DAILY_LEADERBOARD_REWARDS.get(index, DAILY_LEADERBOARD_DEFAULT_POINTS))
            wallet_points = self.grant_points(str(user_id), points)
            rewards.append(
                {
                    "rank": index,
                    "user_id": str(user_id),
                    "display_name": str(entry.get("display_name") or entry.get("fighter_name") or user_id),
                    "points": points,
                    "wallet_points": wallet_points,
                }
            )

        payload = json.dumps({"board_type": board, "day_key": day_key, "rewards": rewards}, ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO daily_settlements (group_id, board_type, day_key, payload) VALUES (?, ?, ?, ?)",
                (group_id, board, day_key, payload),
            )
            connection.commit()
        return {
            "group_id": group_id,
            "board_type": board,
            "day_key": day_key,
            "entries": entries,
            "rewards": rewards,
        }

    def has_weekly_settlement(self, group_id: str, board_type: str, week_key: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM weekly_settlements WHERE group_id = ? AND board_type = ? AND week_key = ?",
                (group_id, board_type, week_key),
            ).fetchone()
        return row is not None

    def settle_weekly_leaderboard(self, group_id: str, board_type: str, week_key: str) -> dict[str, Any]:
        board = str(board_type).strip().lower()
        if board not in ("1v1", "3v3"):
            raise ValueError("\u6392\u884c\u699c\u7c7b\u578b\u53ea\u80fd\u662f 1v1 \u6216 3v3")
        if self.has_weekly_settlement(group_id, board, week_key):
            raise ValueError(f"\u672c\u7fa4 {week_key} \u7684 {board} \u5468\u699c\u5df2\u7ecf\u7ed3\u7b97\u8fc7\u4e86")

        entries = self.get_group_leaderboard(group_id, limit=10) if board == "1v1" else self.get_group_team3_leaderboard(group_id, limit=10)
        rewards: list[dict[str, Any]] = []
        for index, entry in enumerate(entries, start=1):
            user_id = entry.get("user_id")
            if not user_id:
                continue
            reward_plan = WEEKLY_LEADERBOARD_REWARDS.get(index)
            points = int(reward_plan["points"]) if reward_plan else WEEKLY_LEADERBOARD_DEFAULT_POINTS
            wallet_points = self.grant_points(str(user_id), points)
            item_id = None
            item_name = None
            item_quantity = 0
            if reward_plan and reward_plan.get("item_id"):
                item_id = str(reward_plan["item_id"])
                item_quantity = int(reward_plan.get("item_quantity", 1))
                self._grant_item_direct(str(user_id), item_id, item_quantity)
                item_name = str(ITEM_CATALOG[item_id]["name"])
            rewards.append(
                {
                    "rank": index,
                    "user_id": str(user_id),
                    "display_name": str(entry.get("display_name") or entry.get("fighter_name") or user_id),
                    "points": points,
                    "wallet_points": wallet_points,
                    "item_id": item_id,
                    "item_name": item_name,
                    "item_quantity": item_quantity,
                }
            )

        payload = json.dumps({"board_type": board, "week_key": week_key, "rewards": rewards}, ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO weekly_settlements (group_id, board_type, week_key, payload) VALUES (?, ?, ?, ?)",
                (group_id, board, week_key, payload),
            )
            connection.commit()
        return {
            "group_id": group_id,
            "board_type": board,
            "week_key": week_key,
            "entries": entries,
            "rewards": rewards,
        }

    def _load_payload_json(self, payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        raw = str(payload or '').strip()
        if not raw:
            return {}
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('payload must decode to object')
        return data

    def _dump_payload_json(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))

    def _hydrate_group_boss_activity(self, row: sqlite3.Row | dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        record = dict(row)
        return {
            'boss_id': int(record['boss_id']),
            'group_id': str(record['group_id']),
            'boss_name': str(record['boss_name']),
            'status': str(record['status']),
            'phase1_payload': self._load_payload_json(record.get('phase1_payload')),
            'phase2_payload': self._load_payload_json(record.get('phase2_payload')),
            'phase2_max_hp': int(record['phase2_max_hp']),
            'phase2_current_hp': int(record['phase2_current_hp']),
            'created_by': str(record.get('created_by') or ''),
            'created_at': str(record.get('created_at') or ''),
            'closed_at': None if record.get('closed_at') in (None, '') else str(record.get('closed_at')),
            'killed_at': None if record.get('killed_at') in (None, '') else str(record.get('killed_at')),
            'settled_at': None if record.get('settled_at') in (None, '') else str(record.get('settled_at')),
        }

    def open_group_boss(
        self,
        group_id: str,
        boss_name: str,
        phase1_payload: dict[str, Any],
        phase2_payload: dict[str, Any],
        created_by: str,
    ) -> dict[str, Any]:
        if self.get_active_group_boss(group_id) is not None:
            raise ValueError("��ǰȺ�Ѿ��н����е�����BOSS���")
        phase2_stats = phase2_payload.get("stats", {})
        phase2_max_hp = int(phase2_stats.get("hp", 0))
        if phase2_max_hp <= 0:
            raise ValueError("����BOSS���׶�Ѫ��������Ч��")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO group_boss_activities (
                    group_id, boss_name, status, phase1_payload, phase2_payload,
                    phase2_max_hp, phase2_current_hp, created_by
                )
                VALUES (?, ?, 'active', ?, ?, ?, ?, ?)
                """,
                (
                    group_id,
                    boss_name,
                    self._serialize_boss_payload(phase1_payload),
                    self._serialize_boss_payload(phase2_payload),
                    phase2_max_hp,
                    phase2_max_hp,
                    created_by,
                ),
            )
            boss_id = int(cursor.lastrowid)
            connection.commit()
        activity = self.get_group_boss_by_id(group_id, boss_id)
        if activity is None:
            raise RuntimeError("world boss activity creation failed")
        return activity

    def get_group_boss_by_id(self, group_id: str, boss_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM group_boss_activities WHERE group_id = ? AND boss_id = ?",
                (group_id, boss_id),
            ).fetchone()
        return self._hydrate_boss_activity(row)

    def get_active_group_boss(self, group_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM group_boss_activities
                WHERE group_id = ? AND status = 'active'
                ORDER BY boss_id DESC
                LIMIT 1
                """,
                (group_id,),
            ).fetchone()
        return self._hydrate_boss_activity(row)

    def get_latest_group_boss(self, group_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM group_boss_activities
                WHERE group_id = ?
                ORDER BY boss_id DESC
                LIMIT 1
                """,
                (group_id,),
            ).fetchone()
        return self._hydrate_boss_activity(row)

    def close_group_boss(self, group_id: str, boss_id: int) -> dict[str, Any]:
        activity = self.get_group_boss_by_id(group_id, boss_id)
        if activity is None:
            raise ValueError("δ�ҵ���Ӧ������BOSS���")
        if activity["status"] == "active":
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE group_boss_activities
                    SET status = 'closed', closed_at = CURRENT_TIMESTAMP
                    WHERE group_id = ? AND boss_id = ?
                    """,
                    (group_id, boss_id),
                )
                connection.commit()
        updated = self.get_group_boss_by_id(group_id, boss_id)
        if updated is None:
            raise RuntimeError("world boss close failed")
        return updated

    def get_group_boss_attempt_usage(self, boss_id: int, group_id: str, user_id: str, day_key: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT used_attempts
                FROM group_boss_attempts
                WHERE boss_id = ? AND group_id = ? AND user_id = ? AND day_key = ?
                """,
                (boss_id, group_id, user_id, day_key),
            ).fetchone()
        return 0 if row is None else int(row["used_attempts"])

    def consume_group_boss_attempt(
        self,
        boss_id: int,
        group_id: str,
        user_id: str,
        day_key: str,
        daily_limit: int,
    ) -> dict[str, int]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT used_attempts
                FROM group_boss_attempts
                WHERE boss_id = ? AND group_id = ? AND user_id = ? AND day_key = ?
                """,
                (boss_id, group_id, user_id, day_key),
            ).fetchone()
            used = 0 if row is None else int(row["used_attempts"])
            if used >= int(daily_limit):
                raise ValueError("����������BOSS��ս�����Ѿ������ˡ�")
            used += 1
            connection.execute(
                """
                INSERT INTO group_boss_attempts (boss_id, group_id, user_id, day_key, used_attempts)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(boss_id, group_id, user_id, day_key)
                DO UPDATE SET used_attempts = excluded.used_attempts, updated_at = CURRENT_TIMESTAMP
                """,
                (boss_id, group_id, user_id, day_key, used),
            )
            connection.commit()
        return {"used_attempts": used, "remaining_attempts": max(0, int(daily_limit) - used)}

    def record_group_boss_damage(
        self,
        boss_id: int,
        group_id: str,
        user_id: str,
        display_name: str,
        damage: int,
    ) -> dict[str, Any]:
        damage = max(0, int(damage))
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT total_damage, attempts
                FROM group_boss_contributions
                WHERE boss_id = ? AND group_id = ? AND user_id = ?
                """,
                (boss_id, group_id, user_id),
            ).fetchone()
            total_damage = (0 if row is None else int(row["total_damage"])) + damage
            attempts = (0 if row is None else int(row["attempts"])) + 1
            connection.execute(
                """
                INSERT INTO group_boss_contributions (
                    boss_id, group_id, user_id, display_name, total_damage, attempts
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(boss_id, group_id, user_id)
                DO UPDATE SET
                    display_name = excluded.display_name,
                    total_damage = excluded.total_damage,
                    attempts = excluded.attempts,
                    last_attempt_at = CURRENT_TIMESTAMP
                """,
                (boss_id, group_id, user_id, display_name, total_damage, attempts),
            )
            connection.commit()
        return {
            "boss_id": boss_id,
            "group_id": group_id,
            "user_id": user_id,
            "display_name": display_name,
            "total_damage": total_damage,
            "attempts": attempts,
        }

    def apply_group_boss_phase2_damage(self, boss_id: int, group_id: str, damage: int) -> dict[str, Any]:
        damage = max(0, int(damage))
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT phase2_current_hp, phase2_max_hp, status
                FROM group_boss_activities
                WHERE boss_id = ? AND group_id = ?
                """,
                (boss_id, group_id),
            ).fetchone()
            if row is None:
                raise ValueError("δ�ҵ���Ӧ������BOSS���")
            if str(row["status"]) != "active":
                raise ValueError("��ǰ����BOSS��ѽ����������ټ�¼�˺���")
            before_hp = int(row["phase2_current_hp"])
            after_hp = max(0, before_hp - damage)
            is_killed = after_hp <= 0
            if is_killed:
                connection.execute(
                    """
                    UPDATE group_boss_activities
                    SET phase2_current_hp = ?, status = 'killed', killed_at = CURRENT_TIMESTAMP
                    WHERE boss_id = ? AND group_id = ?
                    """,
                    (after_hp, boss_id, group_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE group_boss_activities
                    SET phase2_current_hp = ?
                    WHERE boss_id = ? AND group_id = ?
                    """,
                    (after_hp, boss_id, group_id),
                )
            connection.commit()
        return {
            "before_hp": before_hp,
            "after_hp": after_hp,
            "phase2_max_hp": int(row["phase2_max_hp"]),
            "is_killed": is_killed,
        }

    def get_group_boss_rank(self, group_id: str, boss_id: int, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT user_id, display_name, total_damage, attempts
                FROM group_boss_contributions
                WHERE group_id = ? AND boss_id = ?
                ORDER BY total_damage DESC, attempts ASC, user_id ASC
                LIMIT ?
                """,
                (group_id, boss_id, limit),
            ).fetchall()
        return [
            {
                "user_id": str(row["user_id"]),
                "display_name": str(row["display_name"] or row["user_id"]),
                "total_damage": int(row["total_damage"]),
                "attempts": int(row["attempts"]),
            }
            for row in rows
        ]

    def get_group_boss_contribution(self, boss_id: int, group_id: str, user_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT boss_id, group_id, user_id, display_name, total_damage, attempts, last_attempt_at
                FROM group_boss_contributions
                WHERE boss_id = ? AND group_id = ? AND user_id = ?
                """,
                (int(boss_id), group_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return {
            'boss_id': int(row['boss_id']),
            'group_id': str(row['group_id']),
            'user_id': str(row['user_id']),
            'display_name': str(row['display_name'] or user_id),
            'total_damage': int(row['total_damage']),
            'attempts': int(row['attempts']),
            'last_attempt_at': str(row['last_attempt_at'] or ''),
        }

    def settle_group_boss(self, group_id: str, boss_id: int) -> dict[str, Any]:
        existing = self.get_group_boss_settlement(group_id, boss_id)
        if existing is not None:
            return existing
        activity = self.get_group_boss_by_id(group_id, boss_id)
        if activity is None:
            raise ValueError("δ�ҵ���Ӧ������BOSS���")
        if activity["status"] not in ("killed", "closed", "settled"):
            raise ValueError("����BOSS��δ���������ܽ��㡣")
        entries = self.get_group_boss_rank(group_id, boss_id, limit=10)
        killed = activity["status"] == "killed"
        participant_rewards: list[dict[str, Any]] = []
        if killed:
            for entry in entries:
                user_id = str(entry["user_id"])
                points = int(WORLD_BOSS_KILL_PARTICIPATION_REWARD["points"])
                wallet_points = self.grant_points(user_id, points)
                item_rewards: list[dict[str, Any]] = []
                for item_id, quantity in (WORLD_BOSS_KILL_PARTICIPATION_REWARD.get("items") or {}).items():
                    if int(quantity) <= 0:
                        continue
                    self._grant_item_direct(user_id, str(item_id), int(quantity))
                    item_rewards.append(
                        {
                            "item_id": str(item_id),
                            "item_name": str(ITEM_CATALOG[str(item_id)]["name"]),
                            "quantity": int(quantity),
                        }
                    )
                participant_rewards.append(
                    {
                        "user_id": user_id,
                        "display_name": str(entry["display_name"]),
                        "points": points,
                        "wallet_points": wallet_points,
                        "items": item_rewards,
                    }
                )
        rank_reward_map = WORLD_BOSS_KILL_RANK_REWARDS if killed else WORLD_BOSS_CLOSED_RANK_REWARDS
        rank_default_reward = WORLD_BOSS_KILL_RANK_DEFAULT_REWARD if killed else WORLD_BOSS_CLOSED_RANK_DEFAULT_REWARD
        rank_rewards: list[dict[str, Any]] = []
        for index, entry in enumerate(entries, start=1):
            reward_plan = dict(rank_reward_map.get(index, rank_default_reward))
            points = int(reward_plan.get("points", 0))
            wallet_points = self.grant_points(entry["user_id"], points) if points > 0 else self.get_user_points(entry["user_id"])
            item_rewards: list[dict[str, Any]] = []
            for item_id, quantity in (reward_plan.get("items") or {}).items():
                if int(quantity) <= 0:
                    continue
                self._grant_item_direct(str(entry["user_id"]), str(item_id), int(quantity))
                item_rewards.append(
                    {
                        "item_id": str(item_id),
                        "item_name": str(ITEM_CATALOG[str(item_id)]["name"]),
                        "quantity": int(quantity),
                    }
                )
            rank_rewards.append(
                {
                    "rank": index,
                    "user_id": entry["user_id"],
                    "display_name": entry["display_name"],
                    "total_damage": int(entry["total_damage"]),
                    "attempts": int(entry["attempts"]),
                    "points": points,
                    "wallet_points": wallet_points,
                    "items": item_rewards,
                }
            )
        payload = {
            "boss_name": activity["boss_name"],
            "settlement_type": "killed" if killed else "closed",
            "participant_rewards": participant_rewards,
            "rank_rewards": rank_rewards,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO group_boss_settlements (boss_id, group_id, payload)
                VALUES (?, ?, ?)
                """,
                (boss_id, group_id, json.dumps(payload, ensure_ascii=False)),
            )
            connection.execute(
                """
                UPDATE group_boss_activities
                SET status = 'settled', settled_at = CURRENT_TIMESTAMP
                WHERE group_id = ? AND boss_id = ?
                """,
                (group_id, boss_id),
            )
            connection.commit()
        settlement = self.get_group_boss_settlement(group_id, boss_id)
        if settlement is None:
            raise RuntimeError("world boss settlement failed")
        return settlement

    def get_group_boss_settlement(self, group_id: str, boss_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT boss_id, group_id, payload, settled_at
                FROM group_boss_settlements
                WHERE group_id = ? AND boss_id = ?
                """,
                (group_id, boss_id),
            ).fetchone()
        return self._hydrate_boss_settlement(row)

    def _build_generated_fighter(self, name: str, forced_base_star: float | None = None) -> dict[str, Any]:
        rng = self._rng_for_name(name)
        martial_art = rng.choice(self.martial_arts)
        neigong = rng.choice(self.neigong)
        qinggong = rng.choice(self.qinggong)
        raw_stats, star_rating = self._generate_base_stats(rng, forced_star_rating=forced_base_star)
        breakthrough_stage = 0
        final_stats = self._recalculate_final_stats(raw_stats, float(star_rating), breakthrough_stage, martial_art, neigong, qinggong)
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
            "base_star_rating": float(star_rating),
            "star_exp": 0,
            "breakthrough_stage": breakthrough_stage,
            "martial_reroll_count": 0,
            "avatar_path": None,
            "raw_stats": dict(raw_stats),
            "martial_art": martial_art,
            "neigong": neigong,
            "qinggong": qinggong,
        }

    def _insert_generated_fighter(self, fighter: dict[str, Any]) -> None:
        raw_stats = fighter["raw_stats"]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO fighters (
                    name, hp, atk, def, spd, crt, eva,
                    martial_art_id, neigong_id, qinggong_id, star_rating,
                    base_star_rating, star_exp, breakthrough_stage, martial_reroll_count,
                    raw_hp, raw_atk, raw_def, raw_spd, raw_crt, raw_eva, avatar_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    fighter["base_star_rating"],
                    fighter["star_exp"],
                    fighter["breakthrough_stage"],
                    fighter["martial_reroll_count"],
                    raw_stats["hp"],
                    raw_stats["atk"],
                    raw_stats["def"],
                    raw_stats["spd"],
                    raw_stats["crt"],
                    raw_stats["eva"],
                    fighter.get("avatar_path"),
                ),
            )
            connection.commit()

    def _rng_for_name(self, name: str) -> random.Random:
        normalized = name.strip().casefold().encode("utf-8")
        digest = hashlib.sha256(normalized).digest()
        seed = int.from_bytes(digest[:8], "big")
        return random.Random(seed)

    def _generate_base_stats(
        self,
        rng: random.Random,
        forced_star_rating: float | None = None,
    ) -> tuple[dict[str, float], float]:
        if forced_star_rating is not None:
            forced_star_rating = float(forced_star_rating)
            if abs(forced_star_rating - 6.0) < 0.001:
                total_pool = INNATE_SIX_STAR_POOL
            else:
                total_pool = self._target_pool_for_star(forced_star_rating)
        elif rng.random() < INITIAL_SIX_STAR_CHANCE:
            total_pool = INNATE_SIX_STAR_POOL
            forced_star_rating = 6.0
        else:
            total_pool = rng.randint(340, 460)
            forced_star_rating = None
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
        return scaled, forced_star_rating if forced_star_rating is not None else self._compute_star_rating(total_pool)

    def _compute_star_rating(self, total_pool: int) -> float:
        step = round((total_pool - 340) / 15)
        step = max(0, min(8, step))
        return 1.0 + (step * 0.5)

    def _star_rating_key(self, star_rating: float) -> float:
        return round(max(1.0, min(5.0, float(star_rating))), 1)

    def _target_pool_for_star(self, star_rating: float) -> int:
        return STAR_POOL_BY_RATING[self._star_rating_key(star_rating)]

    def _scale_raw_stats_to_pool(self, raw_stats: dict[str, float], target_pool: int) -> dict[str, float]:
        total = sum(max(1.0, float(value)) for value in raw_stats.values())
        scale = float(target_pool) / max(1.0, total)
        scaled = {key: max(1.0, float(value) * scale) for key, value in raw_stats.items()}
        scaled["crt"] = max(4.0, min(38.0, scaled["crt"]))
        scaled["eva"] = max(4.0, min(38.0, scaled["eva"]))
        return scaled

    def _apply_breakthrough_bonus(self, stats: dict[str, Any], breakthrough_stage: int) -> dict[str, Any]:
        if breakthrough_stage <= 0:
            return stats
        boosted = dict(stats)
        boosted["hp"] = max(1, int(round(boosted["hp"] * BREAKTHROUGH_BONUS["hp"])))
        boosted["atk"] = max(1, int(round(boosted["atk"] * BREAKTHROUGH_BONUS["atk"])))
        boosted["def"] = max(1, int(round(boosted["def"] * BREAKTHROUGH_BONUS["def"])))
        boosted["spd"] = round(max(1.0, boosted["spd"] * BREAKTHROUGH_BONUS["spd"]), 2)
        boosted["crt"] = round(max(1.0, min(75.0, boosted["crt"] + BREAKTHROUGH_BONUS["crt"])), 2)
        boosted["eva"] = round(max(1.0, min(75.0, boosted["eva"] + BREAKTHROUGH_BONUS["eva"])), 2)
        return boosted

    def _recalculate_final_stats(
        self,
        raw_stats: dict[str, float],
        star_rating: float,
        breakthrough_stage: int,
        martial_art: dict[str, Any],
        neigong: dict[str, Any],
        qinggong: dict[str, Any],
    ) -> dict[str, Any]:
        effective_breakthrough = int(breakthrough_stage)
        if float(star_rating) >= 6.0 and effective_breakthrough <= 0:
            scaled_raw = self._scale_raw_stats_to_pool(raw_stats, INNATE_SIX_STAR_POOL)
        else:
            effective_star = min(5.0, float(star_rating))
            scaled_raw = self._scale_raw_stats_to_pool(raw_stats, self._target_pool_for_star(effective_star))
        final_stats = self._apply_modifiers(scaled_raw, martial_art, neigong, qinggong)
        return self._apply_breakthrough_bonus(final_stats, effective_breakthrough)

    def _resolve_raw_stats(
        self,
        record: dict[str, Any],
        martial_art: dict[str, Any],
        neigong: dict[str, Any],
        qinggong: dict[str, Any],
    ) -> dict[str, float]:
        names = ("hp", "atk", "def", "spd", "crt", "eva")
        if all(record.get(f"raw_{name}") not in (None, 0, 0.0) for name in names):
            return {name: float(record[f"raw_{name}"]) for name in names}
        martial_modifiers = martial_art.get("stat_modifiers", {})
        raw_hp = float(record["hp"]) / HP_BATTLE_SCALE / max(0.01, float(neigong.get("hp_multiplier", 1.0)))
        raw_atk = float(record["atk"]) / max(0.01, float(martial_modifiers.get("atk", 1.0)))
        raw_def = float(record["def"]) / max(0.01, float(neigong.get("def_multiplier", 1.0)))
        raw_spd = float(record["spd"]) / max(0.01, float(qinggong.get("spd_multiplier", 1.0))) / max(0.01, float(martial_modifiers.get("spd", 1.0)))
        raw_crt = float(record["crt"]) / max(0.01, float(martial_modifiers.get("crt", 1.0)))
        raw_eva = (float(record["eva"]) - float(qinggong.get("eva_bonus", 0.0))) / max(0.01, float(martial_modifiers.get("eva", 1.0)))
        return {
            "hp": max(1.0, raw_hp),
            "atk": max(1.0, raw_atk),
            "def": max(1.0, raw_def),
            "spd": max(1.0, raw_spd),
            "crt": max(1.0, raw_crt),
            "eva": max(1.0, raw_eva),
        }

    def _load_fighter_record(self, fighter_name: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM fighters WHERE name = ?", (fighter_name,)).fetchone()
        if row is None:
            raise ValueError("\u672a\u627e\u5230\u89d2\u8272\u8bb0\u5f55")
        return dict(row)

    def _persist_fighter_progression(
        self,
        fighter_name: str,
        stats: dict[str, Any],
        star_rating: float,
        star_exp: int,
        breakthrough_stage: int,
        martial_art_id: str,
        raw_stats: dict[str, float],
        martial_reroll_count: int | None = None,
    ) -> None:
        with self._connect() as connection:
            parameters: list[Any] = [
                stats["hp"],
                stats["atk"],
                stats["def"],
                stats["spd"],
                stats["crt"],
                stats["eva"],
                star_rating,
                star_exp,
                breakthrough_stage,
                martial_art_id,
                raw_stats["hp"],
                raw_stats["atk"],
                raw_stats["def"],
                raw_stats["spd"],
                raw_stats["crt"],
                raw_stats["eva"],
            ]
            sql = """
                UPDATE fighters
                SET hp = ?, atk = ?, def = ?, spd = ?, crt = ?, eva = ?,
                    star_rating = ?, star_exp = ?, breakthrough_stage = ?, martial_art_id = ?,
                    raw_hp = ?, raw_atk = ?, raw_def = ?, raw_spd = ?, raw_crt = ?, raw_eva = ?
            """
            if martial_reroll_count is not None:
                sql += ", martial_reroll_count = ?"
                parameters.append(martial_reroll_count)
            sql += " WHERE name = ?"
            parameters.append(fighter_name)
            connection.execute(sql, tuple(parameters))
            connection.commit()

    def _consume_item(self, user_id: str, item_id: str, quantity: int) -> int:
        with self._connect() as connection:
            remaining = self._change_item_quantity(connection, user_id, item_id, -quantity)
            connection.commit()
        return remaining

    def feed_fighter_star_exp(self, user_id: str, fighter_name: str, item_key: str, quantity: int = 1) -> dict[str, Any]:
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError("你名下没有这个角色")
        before_stats = dict(fighter["stats"])
        before_star_rating = float(fighter.get("star_rating", 0.0))
        item_id, item_data = self.get_item_catalog_entry(item_key)
        if "star_exp" not in item_data:
            raise ValueError("该道具不能用于提升星经验")
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("数量必须大于 0")
        record = self._load_fighter_record(fighter_name)
        star_rating = float(record["star_rating"])
        if star_rating >= 5.0:
            raise ValueError("角色已经达到 5 星, 不能继续喂经验")
        raw_stats = self._resolve_raw_stats(record, fighter["martial_art"], fighter["neigong"], fighter["qinggong"])
        item_exp = int(item_data["star_exp"])
        star_exp = int(record.get("star_exp") or 0)
        exp_needed = self._exp_needed_to_five_star(star_rating, star_exp)
        used_quantity = min(quantity, max(1, (exp_needed + item_exp - 1) // item_exp))
        unused_quantity = max(0, quantity - used_quantity)
        total_exp = item_exp * used_quantity
        self._consume_item(user_id, item_id, used_quantity)
        level_ups = 0
        while star_rating < 5.0 and total_exp > 0:
            requirement = STAR_EXP_REQUIREMENTS[self._star_rating_key(star_rating)]
            need = requirement - star_exp
            if total_exp < need:
                star_exp += total_exp
                total_exp = 0
                break
            total_exp -= need
            star_rating = round(star_rating + 0.5, 1)
            star_exp = 0
            level_ups += 1
        if star_rating >= 5.0:
            star_rating = 5.0
            star_exp = 0
        stats = self._recalculate_final_stats(raw_stats, star_rating, int(record.get("breakthrough_stage") or 0), fighter["martial_art"], fighter["neigong"], fighter["qinggong"])
        self._persist_fighter_progression(
            fighter_name,
            stats,
            star_rating,
            star_exp,
            int(record.get("breakthrough_stage") or 0),
            fighter["martial_art_id"],
            raw_stats,
        )
        updated = self.get_user_fighter_by_name(user_id, fighter_name)
        next_requirement = None if star_rating >= 5.0 else STAR_EXP_REQUIREMENTS[self._star_rating_key(star_rating)]
        return {
            "fighter": updated,
            "before_star_rating": before_star_rating,
            "item_id": item_id,
            "item_name": str(item_data["name"]),
            "quantity": used_quantity,
            "requested_quantity": quantity,
            "unused_quantity": unused_quantity,
            "gained_exp": item_exp * used_quantity,
            "level_ups": level_ups,
            "star_exp": star_exp,
            "next_requirement": next_requirement,
            "stat_delta": {
                key: (
                    int(updated["stats"][key] - before_stats[key]) if key in ("hp", "atk", "def") else round(float(updated["stats"][key] - before_stats[key]), 1)
                ) if level_ups > 0 else 0
                for key in ("hp", "atk", "def", "spd", "crt", "eva")
            },
        }

    def breakthrough_fighter(self, user_id: str, fighter_name: str) -> dict[str, Any]:
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError("\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272")
        before_stats = dict(fighter["stats"])
        record = self._load_fighter_record(fighter_name)
        star_rating = float(record["star_rating"])
        breakthrough_stage = int(record.get("breakthrough_stage") or 0)
        if star_rating < 5.0:
            raise ValueError("\u89d2\u8272\u5c1a\u672a\u8fbe\u5230 5 \u661f, \u4e0d\u80fd\u7a81\u7834")
        if breakthrough_stage >= BREAKTHROUGH_STAGE_MAX or star_rating >= 6.0:
            raise ValueError("\u89d2\u8272\u5df2\u7ecf\u5b8c\u6210\u5f53\u524d\u7248\u672c\u7684\u5168\u90e8\u7a81\u7834")
        self._consume_item(user_id, "breakthrough_pill", 1)
        raw_stats = self._resolve_raw_stats(record, fighter["martial_art"], fighter["neigong"], fighter["qinggong"])
        breakthrough_stage = 1
        star_rating = 6.0
        stats = self._recalculate_final_stats(raw_stats, 5.0, breakthrough_stage, fighter["martial_art"], fighter["neigong"], fighter["qinggong"])
        self._persist_fighter_progression(
            fighter_name,
            stats,
            star_rating,
            0,
            breakthrough_stage,
            fighter["martial_art_id"],
            raw_stats,
        )
        updated = self.get_user_fighter_by_name(user_id, fighter_name)
        return {
            "fighter": updated,
            "item_id": "breakthrough_pill",
            "item_name": ITEM_CATALOG["breakthrough_pill"]["name"],
            "stat_delta": {
                key: int(updated["stats"][key] - before_stats[key]) if key in ("hp", "atk", "def") else round(float(updated["stats"][key] - before_stats[key]), 1)
                for key in ("hp", "atk", "def", "spd", "crt", "eva")
            },
        }

    def _martial_pool_by_mode(self, current_martial: dict[str, Any], mode: str) -> list[dict[str, Any]]:
        if mode == "basic":
            pool = [item for item in self.martial_arts if item["id"] != current_martial["id"]]
        elif mode == "type":
            pool = [item for item in self.martial_arts if item["id"] != current_martial["id"] and item.get("type") == current_martial.get("type")]
        elif mode == "choice":
            pool = [item for item in self.martial_arts if item["id"] != current_martial["id"]]
        else:
            raise ValueError("\u672a\u77e5\u7684\u6d17\u7ec3\u6a21\u5f0f")
        if not pool:
            raise ValueError("\u5f53\u524d\u6ca1\u6709\u53ef\u7528\u7684\u6b66\u5b66\u5019\u9009")
        return pool

    def _update_fighter_loadout(
        self,
        user_id: str,
        fighter_name: str,
        *,
        martial_art_id: str | None = None,
        neigong_id: str | None = None,
        qinggong_id: str | None = None,
        increment_martial_reroll: bool = False,
    ) -> dict[str, Any]:
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError("\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272")
        record = self._load_fighter_record(fighter_name)
        raw_stats = self._resolve_raw_stats(record, fighter["martial_art"], fighter["neigong"], fighter["qinggong"])
        next_martial_id = martial_art_id or fighter["martial_art_id"]
        next_neigong_id = neigong_id or fighter["neigong_id"]
        next_qinggong_id = qinggong_id or fighter["qinggong_id"]
        next_martial = self.martial_arts_map[next_martial_id]
        next_neigong = self.neigong_map[next_neigong_id]
        next_qinggong = self.qinggong_map[next_qinggong_id]
        breakthrough_stage = int(record.get("breakthrough_stage") or 0)
        star_rating = float(record["star_rating"])
        reroll_count = int(record.get("martial_reroll_count") or 0)
        if increment_martial_reroll:
            reroll_count += 1
        stats = self._recalculate_final_stats(raw_stats, star_rating, breakthrough_stage, next_martial, next_neigong, next_qinggong)
        self._persist_fighter_progression(
            fighter_name,
            stats,
            star_rating,
            int(record.get("star_exp") or 0),
            breakthrough_stage,
            next_martial_id,
            raw_stats,
            martial_reroll_count=reroll_count,
        )
        with self._connect() as connection:
            connection.execute(
                "UPDATE fighters SET neigong_id = ?, qinggong_id = ? WHERE name = ?",
                (next_neigong_id, next_qinggong_id, fighter_name),
            )
            connection.commit()
        updated = self.get_user_fighter_by_name(user_id, fighter_name)
        if updated is None:
            raise RuntimeError("fighter loadout update failed")
        return updated

    def _update_fighter_martial(self, user_id: str, fighter_name: str, martial_art_id: str) -> dict[str, Any]:
        return self._update_fighter_loadout(
            user_id,
            fighter_name,
            martial_art_id=martial_art_id,
            increment_martial_reroll=True,
        )

    def _random_pool_for_category(self, fighter: dict[str, Any], category: str) -> list[dict[str, Any]]:
        if category == "martial_art":
            pool = [item for item in self.martial_arts if item["id"] != fighter["martial_art"]["id"]]
        elif category == "neigong":
            pool = [item for item in self.neigong if item["id"] != fighter["neigong"]["id"]]
        elif category == "qinggong":
            pool = [item for item in self.qinggong if item["id"] != fighter["qinggong"]["id"]]
        else:
            raise ValueError("\u672a\u77e5\u7684\u66ff\u6362\u7c7b\u578b")
        if not pool:
            raise ValueError("\u5f53\u524d\u6ca1\u6709\u53ef\u7528\u7684\u5019\u9009")
        return pool

    def reroll_loadout_random(self, user_id: str, fighter_name: str, category: str, item_key: str) -> dict[str, Any]:
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError("\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272")
        item_id, item_data = self.get_item_catalog_entry(item_key)
        if item_id not in ("martial_token_basic", "martial_token_type"):
            raise ValueError("\u8be5\u9053\u5177\u4e0d\u80fd\u7528\u4e8e\u66f4\u6362\u529f\u6cd5")
        pool = self._random_pool_for_category(fighter, category)
        self._consume_item(user_id, item_id, 1)
        chosen = random.choice(pool)
        kwargs = {category + '_id': chosen['id']} if category in ('neigong', 'qinggong') else {'martial_art_id': chosen['id']}
        updated = self._update_fighter_loadout(
            user_id,
            fighter_name,
            increment_martial_reroll=(category == 'martial_art'),
            **kwargs,
        )
        target_label = {
            'martial_art': '\u6b66\u529f',
            'neigong': '\u5185\u529f',
            'qinggong': '\u8f7b\u529f',
        }[category]
        old_entry = fighter['martial_art' if category == 'martial_art' else category]
        result = {
            'fighter': updated,
            'item_id': item_id,
            'item_name': str(item_data['name']),
            'category': category,
            'target_label': target_label,
            'old_entry': old_entry,
            'new_entry': chosen,
        }
        if category == 'martial_art':
            result['old_martial'] = old_entry
            result['new_martial'] = chosen
        return result

    def reroll_martial_random(self, user_id: str, fighter_name: str, item_key: str) -> dict[str, Any]:
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError("\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272")
        item_id, item_data = self.get_item_catalog_entry(item_key)
        if item_id not in ("martial_token_basic", "martial_token_type"):
            raise ValueError("\u8be5\u9053\u5177\u4e0d\u80fd\u7528\u4e8e\u968f\u673a\u6d17\u6b66\u5b66")
        mode = "basic" if item_id == "martial_token_basic" else "type"
        pool = self._martial_pool_by_mode(fighter["martial_art"], mode)
        self._consume_item(user_id, item_id, 1)
        martial_art = random.choice(pool)
        updated = self._update_fighter_martial(user_id, fighter_name, martial_art["id"])
        return {
            "fighter": updated,
            "item_id": item_id,
            "item_name": str(item_data["name"]),
            "category": "martial_art",
            "target_label": "\u6b66\u529f",
            "old_entry": fighter["martial_art"],
            "new_entry": martial_art,
            "old_martial": fighter["martial_art"],
            "new_martial": martial_art,
        }

    def create_loadout_choice_options(self, user_id: str, fighter_name: str, category: str) -> dict[str, Any]:
        fighter = self.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError("\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272")
        self._consume_item(user_id, "martial_token_choice", 1)
        pool = self._random_pool_for_category(fighter, category)
        options = random.sample(pool, min(3, len(pool)))
        target_label = {
            "martial_art": "\u6b66\u529f",
            "neigong": "\u5185\u529f",
            "qinggong": "\u8f7b\u529f",
        }[category]
        old_entry = fighter["martial_art" if category == "martial_art" else category]
        return {
            "fighter_name": fighter_name,
            "category": category,
            "target_label": target_label,
            "old_entry": old_entry,
            "options": options,
            "item_id": "martial_token_choice",
            "item_name": ITEM_CATALOG["martial_token_choice"]["name"],
        }

    def create_martial_choice_options(self, user_id: str, fighter_name: str) -> dict[str, Any]:
        return self.create_loadout_choice_options(user_id, fighter_name, "martial_art")

    def apply_loadout_choice(self, user_id: str, fighter_name: str, category: str, choice_id: str) -> dict[str, Any]:
        kwargs = {category + "_id": choice_id} if category in ("neigong", "qinggong") else {"martial_art_id": choice_id}
        updated = self._update_fighter_loadout(
            user_id,
            fighter_name,
            increment_martial_reroll=(category == "martial_art"),
            **kwargs,
        )
        return {
            "fighter": updated,
            "category": category,
            "target_label": {
                "martial_art": "\u6b66\u529f",
                "neigong": "\u5185\u529f",
                "qinggong": "\u8f7b\u529f",
            }[category],
            "new_entry": updated["martial_art" if category == "martial_art" else category],
        }

    def apply_martial_choice(self, user_id: str, fighter_name: str, martial_art_id: str) -> dict[str, Any]:
        result = self.apply_loadout_choice(user_id, fighter_name, "martial_art", martial_art_id)
        result["new_martial"] = result["new_entry"]
        return result

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
        raw_stats = self._resolve_raw_stats(record, martial_art, neigong, qinggong)
        breakthrough_stage = int(record.get("breakthrough_stage") or 0)
        star_rating = float(record["star_rating"])
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
            "star_rating": star_rating,
            "base_star_rating": float(record.get("base_star_rating") or min(star_rating, 5.0)),
            "star_exp": int(record.get("star_exp") or 0),
            "breakthrough_stage": breakthrough_stage,
            "martial_reroll_count": int(record.get("martial_reroll_count") or 0),
            "avatar_path": str(record.get("avatar_path") or "") or None,
            "raw_stats": raw_stats,
            "martial_art": martial_art,
            "neigong": neigong,
            "qinggong": qinggong,
        }


    def special_summon_preview_fighter(self, user_id: str, fighter_name: str) -> dict[str, Any]:
        item_id = "special_summon_token"
        if self.get_fighter_by_name(fighter_name) is not None:
            raise ValueError("\u89d2\u8272\u540d\u5df2\u5b58\u5728: " + fighter_name)
        forced_base_star = 6.0 if random.random() < 0.10 else 5.0
        fighter = self._build_generated_fighter(fighter_name, forced_base_star=forced_base_star)
        remaining = self._consume_item(user_id, item_id, 1)
        fighter["summon_item_id"] = item_id
        fighter["summon_item_name"] = ITEM_CATALOG[item_id]["name"]
        fighter["summon_remaining"] = remaining
        fighter["summon_base_star"] = forced_base_star
        return fighter


    def bind_prepared_fighter_for_user(self, user_id: str, prepared_fighter: dict[str, Any]) -> dict[str, Any]:
        roster = self.get_user_fighters(user_id)
        if len(roster) >= MAX_FIGHTERS_PER_USER:
            raise ValueError(f"\u6bcf\u540d\u7528\u6237\u6700\u591a\u4fdd\u7559 {MAX_FIGHTERS_PER_USER} \u4e2a\u89d2\u8272\u3002")
        preview_name = str(prepared_fighter["name"])
        existing = self.get_fighter_by_name(preview_name)
        if existing is not None:
            raise ValueError("\u89d2\u8272\u540d\u5df2\u5b58\u5728: " + preview_name)
        self._insert_generated_fighter(prepared_fighter)
        slot_index = self._next_slot_index(roster)
        with self._connect() as connection:
            connection.execute("UPDATE user_fighters SET is_active = 0 WHERE user_id = ?", (user_id,))
            connection.execute(
                """
                INSERT INTO user_fighters (user_id, fighter_name, slot_index, is_active)
                VALUES (?, ?, ?, 1)
                """,
                (user_id, preview_name, slot_index),
            )
            connection.commit()
        bound = self.get_user_fighter_by_name(user_id, preview_name)
        if bound is None:
            raise RuntimeError("fighter binding failed")
        return bound


    def _serialize_boss_payload(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False)


    def _deserialize_boss_payload(self, payload: str) -> dict[str, Any]:
        return json.loads(payload)


    def _hydrate_boss_activity(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        data = dict(row)
        data["boss_id"] = int(data["boss_id"])
        data["phase2_max_hp"] = int(data["phase2_max_hp"])
        data["phase2_current_hp"] = int(data["phase2_current_hp"])
        data["phase1_payload"] = self._deserialize_boss_payload(str(data["phase1_payload"]))
        data["phase2_payload"] = self._deserialize_boss_payload(str(data["phase2_payload"]))
        return data


    def _hydrate_boss_settlement(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        payload = json.loads(str(row["payload"]))
        payload["boss_id"] = int(row["boss_id"])
        payload["group_id"] = str(row["group_id"])
        payload["settled_at"] = str(row["settled_at"])
        return payload


    def update_group_boss_payloads(
        self,
        group_id: str,
        boss_id: int,
        phase1_payload: dict[str, Any],
        phase2_payload: dict[str, Any],
    ) -> dict[str, Any]:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE group_boss_activities
                SET phase1_payload = ?, phase2_payload = ?
                WHERE group_id = ? AND boss_id = ?
                """,
                (
                    self._serialize_boss_payload(phase1_payload),
                    self._serialize_boss_payload(phase2_payload),
                    group_id,
                    boss_id,
                ),
            )
            connection.commit()
        updated = self.get_group_boss_by_id(group_id, boss_id)
        if updated is None:
            raise RuntimeError("world boss payload refresh failed")
        return updated
