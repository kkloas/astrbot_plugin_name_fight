"""Shared world boss encounters, replay snapshots and atomic settlement."""

from __future__ import annotations

import json
import random
import re
import time
from copy import deepcopy
from datetime import date
from typing import Any

try:
    from .boss_resources import apply_boss_phase_skin
    from .database import (
        ITEM_CATALOG,
        WORLD_BOSS_CLOSED_RANK_DEFAULT_REWARD,
        WORLD_BOSS_CLOSED_RANK_REWARDS,
        WORLD_BOSS_KILL_PARTICIPATION_REWARD,
        WORLD_BOSS_KILL_RANK_DEFAULT_REWARD,
        WORLD_BOSS_KILL_RANK_REWARDS,
    )
    from .engine import CombatEngine
    from .world_boss_config import (
        WORLD_BOSS_DAILY_LIMIT,
        WORLD_BOSS_NAME,
        WORLD_BOSS_PHASE1,
        WORLD_BOSS_PHASE2,
    )
except ImportError:
    from boss_resources import apply_boss_phase_skin
    from database import (
        ITEM_CATALOG,
        WORLD_BOSS_CLOSED_RANK_DEFAULT_REWARD,
        WORLD_BOSS_CLOSED_RANK_REWARDS,
        WORLD_BOSS_KILL_PARTICIPATION_REWARD,
        WORLD_BOSS_KILL_RANK_DEFAULT_REWARD,
        WORLD_BOSS_KILL_RANK_REWARDS,
    )
    from engine import CombatEngine
    from world_boss_config import (
        WORLD_BOSS_DAILY_LIMIT,
        WORLD_BOSS_NAME,
        WORLD_BOSS_PHASE1,
        WORLD_BOSS_PHASE2,
    )


def phase_payload(repo, template: dict[str, Any]) -> dict[str, Any]:
    art, inner, light = apply_boss_phase_skin(
        template,
        repo.martial_arts_map[template["martial_art_id"]],
        repo.neigong_map[template["neigong_id"]],
        repo.qinggong_map[template["qinggong_id"]],
    )
    return {
        key: deepcopy(template[key])
        for key in (
            "boss_key",
            "name",
            "label",
            "description",
            "stats",
            "martial_art_id",
            "neigong_id",
            "qinggong_id",
        )
    } | {"martial_art": art, "neigong": inner, "qinggong": light}


def default_boss(repo):
    return (
        WORLD_BOSS_NAME,
        phase_payload(repo, WORLD_BOSS_PHASE1),
        phase_payload(repo, WORLD_BOSS_PHASE2),
    )


def replay_fighter(fighter):
    return {
        "name": fighter["name"],
        "stats": deepcopy(fighter["stats"]),
        "currentHp": fighter.get("current_hp", fighter["stats"]["hp"]),
        "martialArt": {
            key: fighter["martial_art"].get(key, "") for key in ("id", "name", "type")
        },
        "neigong": {key: fighter["neigong"].get(key, "") for key in ("id", "name")},
        "qinggong": {key: fighter["qinggong"].get(key, "") for key in ("id", "name")},
        "bossKey": fighter.get("boss_key"),
    }


def _award(connection, repo, user_id, plan):
    repo._ensure_wallet_row(connection, user_id)
    points = int(plan.get("points", 0))
    connection.execute(
        "UPDATE user_wallets SET points = points + ? WHERE user_id = ?",
        (points, user_id),
    )
    items = []
    for item_id, quantity in (plan.get("items") or {}).items():
        if int(quantity) <= 0:
            continue
        connection.execute(
            """INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + excluded.quantity""",
            (user_id, item_id, int(quantity)),
        )
        items.append(
            {
                "item_id": item_id,
                "item_name": ITEM_CATALOG[item_id]["name"],
                "quantity": int(quantity),
            }
        )
    wallet = connection.execute(
        "SELECT points FROM user_wallets WHERE user_id = ?", (user_id,)
    ).fetchone()
    return {"points": points, "wallet_points": int(wallet["points"]), "items": items}


def settle_in_transaction(connection, repo, group_id, boss_id):
    existing = connection.execute(
        "SELECT * FROM group_boss_settlements WHERE group_id = ? AND boss_id = ?",
        (group_id, boss_id),
    ).fetchone()
    if existing:
        return repo._hydrate_boss_settlement(existing)
    activity = connection.execute(
        "SELECT * FROM group_boss_activities WHERE group_id = ? AND boss_id = ?",
        (group_id, boss_id),
    ).fetchone()
    if activity is None or activity["status"] not in ("killed", "closed"):
        raise ValueError("世界 BOSS 尚未结束, 不能结算。")
    killed = activity["status"] == "killed"
    # All contributors receive participation rewards; only ten receive rank rewards.
    entries = connection.execute(
        """SELECT * FROM group_boss_contributions
        WHERE group_id = ? AND boss_id = ? AND total_damage > 0
        ORDER BY total_damage DESC, last_attempt_at ASC, user_id ASC""",
        (group_id, boss_id),
    ).fetchall()
    participants, ranked = [], []
    if killed:
        for entry in entries:
            reward = _award(
                connection, repo, entry["user_id"], WORLD_BOSS_KILL_PARTICIPATION_REWARD
            )
            participants.append(
                {
                    "user_id": entry["user_id"],
                    "display_name": entry["display_name"],
                    **reward,
                }
            )
    plans = WORLD_BOSS_KILL_RANK_REWARDS if killed else WORLD_BOSS_CLOSED_RANK_REWARDS
    fallback = (
        WORLD_BOSS_KILL_RANK_DEFAULT_REWARD
        if killed
        else WORLD_BOSS_CLOSED_RANK_DEFAULT_REWARD
    )
    for rank, entry in enumerate(entries[:10], 1):
        reward = _award(connection, repo, entry["user_id"], plans.get(rank, fallback))
        ranked.append(
            {
                "rank": rank,
                "user_id": entry["user_id"],
                "display_name": entry["display_name"],
                "total_damage": entry["total_damage"],
                "attempts": entry["attempts"],
                **reward,
            }
        )
    payload = {
        "boss_name": activity["boss_name"],
        "settlement_type": "killed" if killed else "closed",
        "participant_rewards": participants,
        "rank_rewards": ranked,
    }
    connection.execute(
        "INSERT INTO group_boss_settlements (boss_id, group_id, payload) VALUES (?, ?, ?)",
        (boss_id, group_id, json.dumps(payload, ensure_ascii=False)),
    )
    connection.execute(
        "UPDATE group_boss_activities SET status = 'settled', settled_at = CURRENT_TIMESTAMP WHERE group_id = ? AND boss_id = ?",
        (group_id, boss_id),
    )
    row = connection.execute(
        "SELECT * FROM group_boss_settlements WHERE group_id = ? AND boss_id = ?",
        (group_id, boss_id),
    ).fetchone()
    return repo._hydrate_boss_settlement(row)


def settle_boss(repo, group_id, boss_id):
    with repo._connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        return settle_in_transaction(connection, repo, group_id, boss_id)


class WorldBossService:
    def __init__(self, repo, engine_factory=None):
        self.repo = repo
        self.engine_factory = engine_factory or (
            lambda: CombatEngine(rng=random.Random())
        )
        with repo._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS world_boss_replays (
                group_id TEXT NOT NULL, user_id TEXT NOT NULL, request_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL, payload TEXT NOT NULL, created_at INTEGER NOT NULL,
                PRIMARY KEY (group_id, user_id, request_id))""")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS world_boss_replays_recent ON world_boss_replays (group_id, user_id, created_at DESC)"
            )

    def team(self, user_id, slots=None):
        roster = self.repo.get_user_fighters(user_id)
        selected = self.repo.get_user_team3_order(user_id) if slots is None else slots
        if (
            len(selected) != 3
            or len(set(selected)) != 3
            or any(type(slot) is not int for slot in selected)
        ):
            raise ValueError("请选择三个不同的角色出战。")
        by_slot = {fighter["slot_index"]: fighter for fighter in roster}
        if any(slot not in by_slot for slot in selected):
            raise ValueError("需要三个已有角色才能挑战 BOSS。")
        return [deepcopy(by_slot[slot]) for slot in selected]

    def latest(self, group_id, user_id):
        with self.repo._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM world_boss_replays WHERE group_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT 1",
                (group_id, user_id),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def challenge(
        self,
        group_id,
        user_id,
        display_name,
        request_id,
        boss_id,
        *,
        slots=None,
        practice=False,
        phase="full",
    ):
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,96}", request_id):
            raise ValueError("挑战标识无效。")
        if phase not in ("full", "phase1", "phase2") or (
            not practice and phase != "full"
        ):
            raise ValueError("实战必须从一阶段开始。")
        fingerprint = json.dumps(
            [boss_id, slots, practice, phase], separators=(",", ":")
        )
        with self.repo._connect() as connection:
            # Serialize cross-process challenges and commit costs, HP, rewards and replay together.
            # Rendering and network delivery happen only after this transaction is released.
            connection.execute("BEGIN IMMEDIATE")
            cached = connection.execute(
                "SELECT fingerprint, payload FROM world_boss_replays WHERE group_id = ? AND user_id = ? AND request_id = ?",
                (group_id, user_id, request_id),
            ).fetchone()
            if cached:
                if cached["fingerprint"] != fingerprint:
                    raise ValueError("该挑战标识已用于另一场挑战, 请刷新后重试。")
                return json.loads(cached["payload"])
            row = connection.execute(
                "SELECT * FROM group_boss_activities WHERE group_id = ? AND boss_id = ?",
                (group_id, boss_id),
            ).fetchone()
            if row is None or (not practice and row["status"] != "active"):
                raise ValueError("当前 BOSS 活动已结束或不存在, 请刷新。")
            activity = self.repo._hydrate_boss_activity(row)
            team = self.team(user_id, slots)
            day = date.today().isoformat()
            usage = connection.execute(
                "SELECT used_attempts FROM group_boss_attempts WHERE boss_id = ? AND group_id = ? AND user_id = ? AND day_key = ?",
                (boss_id, group_id, user_id, day),
            ).fetchone()
            used = int(usage["used_attempts"]) if usage else 0
            if not practice and used >= WORLD_BOSS_DAILY_LIMIT:
                raise ValueError("你今天的世界 BOSS 挑战次数已经用完了。")
            result = self.simulate(team, activity, practice=practice, phase=phase)
            credited = (
                0
                if practice
                else min(activity["phase2_current_hp"], result["phase2_damage"])
            )
            after_hp = activity["phase2_current_hp"] - credited
            if not practice:
                used += 1
                connection.execute(
                    """INSERT INTO group_boss_attempts (boss_id, group_id, user_id, day_key, used_attempts)
                    VALUES (?, ?, ?, ?, ?) ON CONFLICT(boss_id, group_id, user_id, day_key)
                    DO UPDATE SET used_attempts = excluded.used_attempts, updated_at = CURRENT_TIMESTAMP""",
                    (boss_id, group_id, user_id, day, used),
                )
                connection.execute(
                    "UPDATE group_boss_activities SET phase2_current_hp = ? WHERE boss_id = ? AND group_id = ?",
                    (after_hp, boss_id, group_id),
                )
                if credited:
                    connection.execute(
                        """INSERT INTO group_boss_contributions (boss_id, group_id, user_id, display_name, total_damage, attempts)
                        VALUES (?, ?, ?, ?, ?, 1) ON CONFLICT(boss_id, group_id, user_id) DO UPDATE SET
                        total_damage = total_damage + excluded.total_damage, attempts = attempts + 1,
                        display_name = excluded.display_name, last_attempt_at = CURRENT_TIMESTAMP""",
                        (boss_id, group_id, user_id, display_name, credited),
                    )
                if after_hp == 0:
                    connection.execute(
                        "UPDATE group_boss_activities SET status = 'killed', killed_at = CURRENT_TIMESTAMP WHERE boss_id = ? AND group_id = ?",
                        (boss_id, group_id),
                    )
                    result["settlement"] = settle_in_transaction(
                        connection, self.repo, group_id, boss_id
                    )
            contribution = connection.execute(
                "SELECT total_damage FROM group_boss_contributions WHERE boss_id = ? AND group_id = ? AND user_id = ?",
                (boss_id, group_id, user_id),
            ).fetchone()
            result.update(
                requestId=request_id,
                bossId=boss_id,
                practice=practice,
                creditedDamage=credited,
                phase2_current_hp=after_hp,
                phase2_max_hp=activity["phase2_max_hp"],
                total_damage=int(contribution["total_damage"]) if contribution else 0,
                remaining_attempts=max(0, WORLD_BOSS_DAILY_LIMIT - used),
                daily_limit=WORLD_BOSS_DAILY_LIMIT,
                is_killed=not practice and after_hp == 0,
            )
            connection.execute(
                "INSERT INTO world_boss_replays VALUES (?, ?, ?, ?, ?, ?)",
                (
                    group_id,
                    user_id,
                    request_id,
                    fingerprint,
                    json.dumps(result, ensure_ascii=False),
                    time.time_ns(),
                ),
            )
            return result

    def simulate(self, team, activity, *, practice=False, phase="full"):
        engine = self.engine_factory()
        players = [
            {"fighter": deepcopy(fighter), "hp": int(fighter["stats"]["hp"])}
            for fighter in team
        ]
        duels, entered, cleared, phase2_damage = [], False, False, 0
        phases = [1, 2] if phase == "full" else [int(phase[-1])]
        for number in phases:
            if (
                number == 2
                and phase == "full"
                and (not cleared or not any(p["hp"] > 0 for p in players))
            ):
                break
            payload = deepcopy(activity[f"phase{number}_payload"])
            template = WORLD_BOSS_PHASE1 if number == 1 else WORLD_BOSS_PHASE2
            payload.setdefault("boss_key", template["boss_key"])
            # Existing activities retain their configured stats and names, with stable animation IDs added.
            base_moves = self.repo.martial_arts_map[payload["martial_art_id"]]["moves"]
            for index, move in enumerate(payload["martial_art"]["moves"]):
                if index < len(base_moves):
                    move.setdefault("visual_move", base_moves[index]["name"])
            boss_hp = (
                int(payload["stats"]["hp"])
                if number == 1 or practice
                else int(activity["phase2_current_hp"])
            )
            start_hp = boss_hp
            entered = entered or number == 2
            first = True
            for player in players:
                if player["hp"] <= 0 or boss_hp <= 0:
                    continue
                attacker, defender = deepcopy(player["fighter"]), deepcopy(payload)
                attacker["current_hp"], defender["current_hp"] = player["hp"], boss_hp
                result = engine.battle_with_events(attacker, defender)
                for event in result["events"]:
                    if event.get("actor") == "b" and "moveIndex" in event:
                        index = int(event["moveIndex"])
                        if 0 <= index < len(defender["martial_art"]["moves"]):
                            event["visualMove"] = defender["martial_art"]["moves"][
                                index
                            ].get("visual_move", event.get("move"))
                player["hp"] = max(0, int(result["state"]["fighter_a_hp"]))
                boss_hp = max(0, int(result["state"]["fighter_b_hp"]))
                ending = (
                    "前锋阵破, 真身将现"
                    if number == 1 and boss_hp == 0
                    else "本阵交锋结束"
                )
                boss_meta = {
                    "key": payload["boss_key"],
                    "phase": number,
                    "intro": first,
                    "label": payload.get("label", f"阶段 {number}"),
                    "endingLabel": ending,
                }
                result["boss"] = boss_meta
                result["events"].insert(
                    0,
                    {
                        "type": "boss_phase_start",
                        "time": 0,
                        "phase": number,
                        "intro": first,
                    },
                )
                duels.append(
                    {
                        "index": len(duels) + 1,
                        "phase": number,
                        "boss": boss_meta,
                        "attacker": replay_fighter(attacker),
                        "defender": replay_fighter(defender),
                        "winner": result["winner"],
                        "events": result["events"],
                        "state": result["state"],
                        "logs": result["logs"],
                        "fighter_a": attacker,
                        "fighter_b": defender,
                        "result": result,
                    }
                )
                first = False
            if number == 1:
                cleared = boss_hp == 0
            else:
                phase2_damage = max(0, start_hp - boss_hp)
        return {
            "boss_name": activity["boss_name"],
            "phase1_cleared": cleared,
            "entered_phase2": entered,
            "phase2_damage": phase2_damage,
            "duels": duels,
            "survivors": sum(p["hp"] > 0 for p in players),
            "team": [replay_fighter(p["fighter"]) for p in players],
        }


def reward_preview():
    def describe(plan):
        return {
            "points": int(plan.get("points", 0)),
            "items": [
                {"name": ITEM_CATALOG[key]["name"], "quantity": quantity}
                for key, quantity in (plan.get("items") or {}).items()
            ],
        }

    return {
        "participation": describe(WORLD_BOSS_KILL_PARTICIPATION_REWARD),
        "killed": [
            describe(
                WORLD_BOSS_KILL_RANK_REWARDS.get(
                    rank, WORLD_BOSS_KILL_RANK_DEFAULT_REWARD
                )
            )
            for rank in range(1, 11)
        ],
        "closed": [
            describe(
                WORLD_BOSS_CLOSED_RANK_REWARDS.get(
                    rank, WORLD_BOSS_CLOSED_RANK_DEFAULT_REWARD
                )
            )
            for rank in range(1, 11)
        ],
    }
