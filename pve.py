# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

from database import FighterRepository, ITEM_CATALOG
from engine import CombatEngine


CONFIG_PATH = Path(__file__).resolve().parent / "configs" / "pve_chapters.json"


class PveService:
    def __init__(
        self,
        repository: FighterRepository,
        engine: CombatEngine,
        config_path: Path | None = None,
    ) -> None:
        self.repo = repository
        self.engine = engine
        path = config_path or CONFIG_PATH
        with path.open("r", encoding="utf-8-sig") as file:
            self.config: dict[str, Any] = json.load(file)
        self.chapters = list(self.config.get("chapters", []))
        self.stage_order: list[str] = []
        self.stage_map: dict[str, dict[str, Any]] = {}
        self.chapter_map: dict[str, dict[str, Any]] = {}
        for chapter in self.chapters:
            chapter_id = str(chapter["id"])
            self.chapter_map[chapter_id] = chapter
            for stage in chapter.get("stages", []):
                stage_id = str(stage["id"])
                if stage_id in self.stage_map:
                    raise ValueError(f"duplicate PVE stage id: {stage_id}")
                self.stage_order.append(stage_id)
                self.stage_map[stage_id] = {**stage, "chapter_id": chapter_id}
        energy = self.config.get("energy", {})
        self.maximum_energy = int(energy.get("maximum", 100))
        self.recovery_seconds = int(energy.get("recovery_seconds", 360))
        self._validate_config()

    def _validate_config(self) -> None:
        if len(self.chapters) != 3 or len(self.stage_order) != 18:
            raise ValueError("PVE configuration must contain 3 chapters and 18 stages")
        for stage_id in self.stage_order:
            stage = self.stage_map[stage_id]
            if stage.get("kind") not in {"normal", "elite", "boss"}:
                raise ValueError(f"invalid PVE stage kind: {stage_id}")
            if float(stage.get("stat_scale", 1.0)) <= 0:
                raise ValueError(f"invalid PVE stage stat scale: {stage_id}")
            if len(stage.get("enemies", [])) != 3:
                raise ValueError(f"PVE stage must contain exactly three enemies: {stage_id}")
            for enemy in stage["enemies"]:
                martial_id = str(enemy.get("martial_art_id") or "")
                neigong_id = str(enemy.get("neigong_id") or "")
                qinggong_id = str(enemy.get("qinggong_id") or "")
                if martial_id not in self.repo.martial_arts_map:
                    raise ValueError(f"unknown martial art in PVE config: {martial_id}")
                if neigong_id not in self.repo.neigong_map:
                    raise ValueError(f"unknown neigong in PVE config: {neigong_id}")
                if qinggong_id not in self.repo.qinggong_map:
                    raise ValueError(f"unknown qinggong in PVE config: {qinggong_id}")
        for item_id in self._configured_item_ids():
            if item_id not in ITEM_CATALOG:
                raise ValueError(f"unknown reward item in PVE config: {item_id}")

    def _configured_item_ids(self) -> set[str]:
        item_ids: set[str] = set()
        for chapter in self.chapters:
            for chest in chapter.get("chests", []):
                item_ids.update(str(item["item_id"]) for item in chest.get("items", []))
            for stage in chapter.get("stages", []):
                item_ids.update(str(item["item_id"]) for item in stage.get("first_clear", {}).get("items", []))
        for reward in self.config.get("repeat_rewards", {}).values():
            item_ids.update(str(item["item_id"]) for item in reward.get("drops", []) if item.get("item_id"))
            item_ids.update(str(item["item_id"]) for item in reward.get("drop_table", []) if item.get("item_id"))
        return item_ids

    def _profile(self, user_id: str) -> dict[str, Any]:
        return self.repo.get_pve_profile(
            user_id,
            maximum_energy=self.maximum_energy,
            recovery_seconds=self.recovery_seconds,
        )

    def set_team(self, user_id: str, slots: list[int]) -> dict[str, Any]:
        profile = self.repo.set_pve_team(
            user_id,
            slots,
            maximum_energy=self.maximum_energy,
            recovery_seconds=self.recovery_seconds,
        )
        return {"profile": profile, "state": self.get_state(user_id)}

    def _progress_map(self, user_id: str) -> dict[str, dict[str, Any]]:
        return {entry["stage_id"]: entry for entry in self.repo.get_pve_stage_progress(user_id)}

    def _claimed_set(self, user_id: str) -> set[tuple[str, int]]:
        return {
            (str(entry["chapter_id"]), int(entry["star_threshold"]))
            for entry in self.repo.get_pve_claimed_rewards(user_id)
        }

    def _is_unlocked(self, stage_id: str, progress: dict[str, dict[str, Any]]) -> bool:
        index = self.stage_order.index(stage_id)
        if index == 0:
            return True
        previous = progress.get(self.stage_order[index - 1])
        return previous is not None and int(previous.get("clear_count", 0)) > 0

    def _stage_enemy(self, stage: dict[str, Any], enemy: dict[str, Any]) -> dict[str, Any]:
        fighter = self._build_enemy(enemy)
        scale = float(stage.get("stat_scale", 1.0))
        for key in ("hp", "atk", "def", "spd"):
            fighter["stats"][key] = max(1, int(round(float(fighter["stats"][key]) * scale)))
        return fighter

    def _public_enemy(self, stage: dict[str, Any], enemy: dict[str, Any]) -> dict[str, Any]:
        fighter = self._stage_enemy(stage, enemy)
        return {
            "name": str(fighter["name"]),
            "stats": dict(fighter["stats"]),
            "martialArt": self._public_entry(fighter["martial_art"]),
            "neigong": self._public_entry(fighter["neigong"]),
            "qinggong": self._public_entry(fighter["qinggong"]),
        }

    def _public_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": entry.get("id"),
            "name": entry.get("name"),
            "type": entry.get("type"),
            "description": entry.get("description", ""),
        }

    def _public_reward(self, reward: dict[str, Any]) -> dict[str, Any]:
        items = []
        for item in reward.get("items", []):
            item_id = str(item.get("item_id") or "")
            items.append({
                "item_id": item_id,
                "name": str(ITEM_CATALOG.get(item_id, {}).get("name", item_id)),
                "quantity": int(item.get("quantity", 0)),
            })
        return {"points": int(reward.get("points", 0)), "items": items}

    def _public_stage(
        self,
        stage: dict[str, Any],
        progress: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        stage_id = str(stage["id"])
        stage_progress = progress.get(stage_id, {})
        return {
            "id": stage_id,
            "chapterId": str(stage["chapter_id"]),
            "name": str(stage["name"]),
            "kind": str(stage["kind"]),
            "recommendedStars": float(stage["recommended_stars"]),
            "energyCost": int(stage["energy_cost"]),
            "trait": deepcopy(stage.get("trait", {})),
            "firstClear": self._public_reward(stage.get("first_clear", {})),
            "enemies": [self._public_enemy(stage, enemy) for enemy in stage.get("enemies", [])],
            "unlocked": self._is_unlocked(stage_id, progress),
            "bestStars": int(stage_progress.get("best_stars", 0)),
            "clearCount": int(stage_progress.get("clear_count", 0)),
        }

    def get_state(self, user_id: str) -> dict[str, Any]:
        profile = self._profile(user_id)
        progress = self._progress_map(user_id)
        claimed = self._claimed_set(user_id)
        chapters: list[dict[str, Any]] = []
        for chapter in self.chapters:
            chapter_id = str(chapter["id"])
            stages = [self._public_stage(self.stage_map[str(stage["id"])], progress) for stage in chapter.get("stages", [])]
            chapter_stars = sum(int(stage["bestStars"]) for stage in stages)
            chests = []
            for chest in chapter.get("chests", []):
                threshold = int(chest["stars"])
                chests.append({
                    **self._public_reward(chest),
                    "stars": threshold,
                    "claimed": (chapter_id, threshold) in claimed,
                    "available": chapter_stars >= threshold and (chapter_id, threshold) not in claimed,
                })
            chapters.append({
                "id": chapter_id,
                "name": str(chapter["name"]),
                "description": str(chapter.get("description", "")),
                "stars": chapter_stars,
                "stages": stages,
                "chests": chests,
            })
        roster = self.repo.get_user_fighters(user_id)
        fighters_by_slot = {int(fighter.get("slot_index", 0)): fighter for fighter in roster}
        team = [fighters_by_slot[slot] for slot in profile["team_slots"] if slot in fighters_by_slot]
        next_stage_id = next((stage_id for stage_id in self.stage_order if self._is_unlocked(stage_id, progress) and int(progress.get(stage_id, {}).get("clear_count", 0)) == 0), self.stage_order[-1])
        return {
            "profile": profile,
            "team": [self._replay_fighter(fighter) | {"slotIndex": int(fighter.get("slot_index", 0))} for fighter in team],
            "chapters": chapters,
            "nextStageId": next_stage_id,
            "hasRequiredRoster": len(roster) >= 3,
        }

    def _build_enemy(self, enemy: dict[str, Any]) -> dict[str, Any]:
        martial_id = str(enemy["martial_art_id"])
        neigong_id = str(enemy["neigong_id"])
        qinggong_id = str(enemy["qinggong_id"])
        return {
            "name": str(enemy["name"]),
            "stats": deepcopy(enemy["stats"]),
            "star_rating": 0.0,
            "martial_art_id": martial_id,
            "neigong_id": neigong_id,
            "qinggong_id": qinggong_id,
            "martial_art": deepcopy(self.repo.martial_arts_map[martial_id]),
            "neigong": deepcopy(self.repo.neigong_map[neigong_id]),
            "qinggong": deepcopy(self.repo.qinggong_map[qinggong_id]),
        }

    def _apply_trait(self, fighter: dict[str, Any], effect: dict[str, Any] | None) -> dict[str, Any]:
        clone = deepcopy(fighter)
        clone["stats"] = dict(clone["stats"])
        if not effect:
            return clone
        for key, multiplier in effect.get("stat_multipliers", {}).items():
            if key in clone["stats"]:
                clone["stats"][key] = float(clone["stats"][key]) * float(multiplier)
        for key, addition in effect.get("stat_additions", {}).items():
            if key in clone["stats"]:
                clone["stats"][key] = float(clone["stats"][key]) + float(addition)
        for key in ("hp", "atk", "def"):
            clone["stats"][key] = max(1, int(round(float(clone["stats"][key]))))
        for key in ("spd", "crt", "eva"):
            maximum = 75.0 if key in {"crt", "eva"} else 9999.0
            clone["stats"][key] = round(max(1.0, min(maximum, float(clone["stats"][key]))), 2)
        return clone

    def _replay_fighter(self, fighter: dict[str, Any], current_hp: int | None = None) -> dict[str, Any]:
        payload = {
            "name": str(fighter["name"]),
            "stats": dict(fighter["stats"]),
            "starRating": float(fighter.get("star_rating", 0.0)),
            "martialArt": self._public_entry(fighter["martial_art"]),
            "neigong": self._public_entry(fighter["neigong"]),
            "qinggong": self._public_entry(fighter["qinggong"]),
        }
        if current_hp is not None:
            payload["currentHp"] = int(current_hp)
        return payload

    def _between_duel_effect(
        self,
        stage: dict[str, Any],
        side: str,
        entry: dict[str, Any],
    ) -> int:
        effect = stage.get("trait", {}).get("between_duels")
        if not effect or str(effect.get("side")) != side or int(entry["hp"]) <= 0:
            return 0
        maximum = int(entry["fighter"]["stats"]["hp"])
        amount = max(1, int(round(maximum * float(effect.get("ratio", 0.0)))))
        before = int(entry["hp"])
        if effect.get("mode") == "heal":
            entry["hp"] = min(maximum, before + amount)
        else:
            entry["hp"] = max(0, before - amount)
        return int(entry["hp"]) - before

    def _team_battle(
        self,
        player_team: list[dict[str, Any]],
        enemy_team: list[dict[str, Any]],
        stage: dict[str, Any],
    ) -> dict[str, Any]:
        trait = stage.get("trait", {})
        players = []
        for fighter in player_team:
            prepared = self._apply_trait(fighter, trait.get("player"))
            players.append({"fighter": prepared, "hp": int(prepared["stats"]["hp"])})
        enemies = []
        for fighter in enemy_team:
            prepared = self._apply_trait(fighter, trait.get("enemy"))
            enemies.append({"fighter": prepared, "hp": int(prepared["stats"]["hp"])})
        player_index = 0
        enemy_index = 0
        duels: list[dict[str, Any]] = []
        while player_index < len(players) and enemy_index < len(enemies):
            player_entry = players[player_index]
            enemy_entry = enemies[enemy_index]
            attacker = deepcopy(player_entry["fighter"])
            defender = deepcopy(enemy_entry["fighter"])
            attacker["current_hp"] = int(player_entry["hp"])
            defender["current_hp"] = int(enemy_entry["hp"])
            result = self.engine.battle_with_events(attacker, defender)
            player_entry["hp"] = max(0, int(result["state"]["fighter_a_hp"]))
            enemy_entry["hp"] = max(0, int(result["state"]["fighter_b_hp"]))
            winner_name = result["winner"]
            transition = ""
            effect_delta = 0
            if winner_name == attacker["name"]:
                enemy_entry["hp"] = 0
                enemy_index += 1
                if enemy_index < len(enemies):
                    effect_delta = self._between_duel_effect(stage, "player", player_entry)
                    if player_entry["hp"] <= 0:
                        transition = f"{attacker['name']} 受关卡影响退场，下一位侠客接战。"
                        player_index += 1
                    else:
                        transition = f"{attacker['name']} 继续迎战 {enemies[enemy_index]['fighter']['name']}。"
            elif winner_name == defender["name"]:
                player_entry["hp"] = 0
                player_index += 1
                if player_index < len(players):
                    effect_delta = self._between_duel_effect(stage, "enemy", enemy_entry)
                    if enemy_entry["hp"] <= 0:
                        transition = f"{defender['name']} 受关卡影响退场，敌方下一人登场。"
                        enemy_index += 1
                    else:
                        transition = f"{defender['name']} 继续迎战 {players[player_index]['fighter']['name']}。"
            else:
                player_entry["hp"] = 0
                enemy_entry["hp"] = 0
                player_index += 1
                enemy_index += 1
                transition = "双方同归于尽，各自换人。"
            duels.append({
                "index": len(duels) + 1,
                "attacker": self._replay_fighter(attacker, int(attacker["current_hp"])),
                "defender": self._replay_fighter(defender, int(defender["current_hp"])),
                "winner": winner_name,
                "state": result["state"],
                "events": result["events"],
                "logs": result["logs"],
                "displayLogs": result["logs"],
                "transition": transition,
                "traitDelta": effect_delta,
                "playerTeam": [self._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in players],
                "enemyTeam": [self._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in enemies],
            })
        alive_players = sum(1 for entry in players if int(entry["hp"]) > 0)
        alive_enemies = sum(1 for entry in enemies if int(entry["hp"]) > 0)
        victory = alive_enemies == 0 and alive_players > 0
        stars = alive_players if victory else 0
        return {
            "victory": victory,
            "stars": stars,
            "duels": duels,
            "playerTeam": [self._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in players],
            "enemyTeam": [self._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in enemies],
        }

    def _roll_repeat_reward(self, kind: str) -> dict[str, Any]:
        configured = deepcopy(self.config["repeat_rewards"][kind])
        reward = {"points": int(configured.get("points", 0)), "items": []}
        if configured.get("drops"):
            for drop in configured["drops"]:
                if random.random() < float(drop.get("chance", 0.0)):
                    reward["items"].append({"item_id": drop["item_id"], "quantity": int(drop.get("quantity", 1))})
        elif configured.get("drop_table"):
            table = configured["drop_table"]
            selected = random.choices(table, weights=[int(entry.get("weight", 0)) for entry in table], k=1)[0]
            if selected.get("item_id"):
                reward["items"].append({"item_id": selected["item_id"], "quantity": int(selected.get("quantity", 1))})
        return reward

    def challenge(self, user_id: str, stage_id: str) -> dict[str, Any]:
        if stage_id not in self.stage_map:
            raise ValueError("未找到该 PVE 关卡")
        stage = self.stage_map[stage_id]
        progress = self._progress_map(user_id)
        if not self._is_unlocked(stage_id, progress):
            raise ValueError("该关卡尚未解锁")
        profile = self._profile(user_id)
        if int(profile["energy"]) < int(stage["energy_cost"]):
            raise ValueError("体力不足")
        if len(profile["team_slots"]) != 3:
            raise ValueError("请先选择三名 PVE 出战角色")
        roster = self.repo.get_user_fighters(user_id)
        fighters_by_slot = {int(fighter.get("slot_index", 0)): fighter for fighter in roster}
        try:
            player_team = [fighters_by_slot[int(slot)] for slot in profile["team_slots"]]
        except KeyError as exc:
            raise ValueError("PVE 队伍中存在已经失效的角色槽位") from exc
        enemy_team = [self._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        battle = self._team_battle(player_team, enemy_team, stage)
        settlement = self.repo.settle_pve_attempt(
            user_id,
            stage_id,
            int(stage["energy_cost"]),
            bool(battle["victory"]),
            int(battle["stars"]),
            deepcopy(stage["first_clear"]),
            self._roll_repeat_reward(str(stage["kind"])),
            maximum_energy=self.maximum_energy,
            recovery_seconds=self.recovery_seconds,
        )
        return {
            "stage": self._public_stage(stage, self._progress_map(user_id)),
            **battle,
            "firstClear": bool(settlement["first_clear"]),
            "bestStars": int(settlement["best_stars"]),
            "clearCount": int(settlement["clear_count"]),
            "reward": settlement["reward"],
            "profile": settlement["profile"],
            "pve": self.get_state(user_id),
        }

    def claim_chapter_reward(self, user_id: str, chapter_id: str, threshold: int) -> dict[str, Any]:
        chapter = self.chapter_map.get(chapter_id)
        if chapter is None:
            raise ValueError("未找到该 PVE 章节")
        chest = next((entry for entry in chapter.get("chests", []) if int(entry["stars"]) == int(threshold)), None)
        if chest is None:
            raise ValueError("未找到该章节宝箱")
        stage_ids = [str(stage["id"]) for stage in chapter.get("stages", [])]
        result = self.repo.claim_pve_chapter_reward(
            user_id,
            chapter_id,
            stage_ids,
            int(threshold),
            {"points": int(chest.get("points", 0)), "items": deepcopy(chest.get("items", []))},
        )
        return {"result": result, "pve": self.get_state(user_id)}
