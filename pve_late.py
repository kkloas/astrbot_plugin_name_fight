# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from pve_switch import SwitchDecisions


class LatePveBattle:
    """Chapter 4 and 5 encounter state around the unchanged duel engine."""

    def __init__(self, service: Any, team: list[dict[str, Any]], enemies: list[dict[str, Any]],
                 stage: dict[str, Any], tactic: dict[str, Any], clues: set[str],
                 decider: SwitchDecisions | None = None, engine: Any = None) -> None:
        self.service = service
        self.engine = engine or service.engine
        self.decider = decider
        self.stage = stage
        self.stage_id = str(stage["id"])
        self.tactic = tactic
        self.encounter = stage["encounter"]
        self.clue_active = self.encounter.get("clue_required") in clues
        trait = stage.get("trait", {})
        self.players = []
        for fighter in team:
            prepared = service._apply_trait(service._apply_trait(fighter, trait.get("player")), tactic.get("player"))
            self.players.append({"fighter": prepared, "hp": int(prepared["stats"]["hp"])})
        self.enemies = []
        for fighter in enemies:
            prepared = service._apply_trait(service._apply_trait(fighter, trait.get("enemy")), tactic.get("enemy"))
            self.enemies.append({"fighter": prepared, "hp": int(prepared["stats"]["hp"])})
        self.active: int | None = 0
        self.entered: set[int] = set()
        self.duels: list[dict[str, Any]] = []
        self.metrics: dict[str, Any] = {}
        self.first_opening = f"{tactic['name']}: {tactic['effect_text']}"
        if self.clue_active:
            self.first_opening += f" 情报生效: {self.encounter['clue_effect']}"

    def _next_alive(self, current: int) -> int | None:
        for step in range(1, len(self.players)):
            candidate = (current + step) % len(self.players)
            if self.players[candidate]["hp"] > 0:
                return candidate
        return current if self.players[current]["hp"] > 0 else None

    def _rotate(self) -> None:
        if self.active is not None:
            self.active = self._next_alive(self.active)

    def _choose_or_rotate(self, reason: str) -> None:
        if self.active is None:
            return
        if self.decider is None:
            self._rotate()
        else:
            self.active = self.decider.choose(self.players, self.enemies, self.duels, self.active, reason)
        if self.duels:
            self._append_transition(f"{self.players[self.active]['fighter']['name']} 接战,气血保留.")

    def _harm(self, ratio: float, floor: int = 1) -> int:
        if self.active is None:
            return 0
        entry = self.players[self.active]
        before = entry["hp"]
        amount = max(1, round(entry["fighter"]["stats"]["hp"] * ratio))
        entry["hp"] = max(floor, before - amount)
        return before - entry["hp"]

    def _append_transition(self, message: str) -> None:
        if self.duels:
            previous = self.duels[-1]["transition"]
            self.duels[-1]["transition"] = (previous + " " if previous else "") + message

    def _fight(self, enemy_index: int, *, floor: int = 0, opening: str = "",
               wave: int = 1, phase: int = 0, enemy_bonus: dict[str, float] | None = None,
               player_bonus: dict[str, float] | None = None) -> tuple[bool, int, int | None]:
        enemy = self.enemies[enemy_index]
        total_actions = 0
        finisher: int | None = None
        for attempt in range(12):
            if self.active is None or enemy["hp"] <= floor:
                break
            actor_index = self.active
            player = self.players[actor_index]
            self.entered.add(actor_index)
            attacker = deepcopy(player["fighter"])
            defender = deepcopy(enemy["fighter"])
            for stat, factor in (player_bonus or {}).items():
                attacker["stats"][stat] = max(1, round(attacker["stats"][stat] * factor))
            for stat, factor in (enemy_bonus or {}).items():
                defender["stats"][stat] = max(1, round(defender["stats"][stat] * factor))
            start_a, start_b = player["hp"], enemy["hp"]
            attacker["current_hp"] = start_a
            defender["current_hp"] = start_b
            if floor:
                defender["phase_hp_floor"] = floor
            result = self.engine.battle_with_events(attacker, defender)
            player["hp"] = max(0, int(result["state"]["fighter_a_hp"]))
            enemy["hp"] = max(0, int(result["state"]["fighter_b_hp"]))
            actions = int(result["state"].get("actions", 1))
            total_actions += actions
            boundary = enemy["hp"] <= floor or bool(result["state"].get("phase_boundary"))
            if result["winner"] == attacker["name"]:
                enemy["hp"] = 0
                boundary = True
            elif result["winner"] == defender["name"]:
                player["hp"] = 0
            elif not boundary:
                player["hp"] = 0
            if boundary:
                finisher = actor_index
            transition = (
                "敌人气机变化,进入接战选择." if boundary and floor and self.decider else
                "敌人气机变化,队友接战." if boundary and floor else
                "敌人退场,下一段接战." if boundary else
                "队友接战." if self.active is not None else "队伍暂时退守."
            )
            event_opening = opening if attempt == 0 else "敌人尚未败退,队友继续接战."
            if not self.duels:
                event_opening = self.first_opening + " " + event_opening
            self.duels.append({
                "index": len(self.duels) + 1,
                "attacker": self.service._replay_fighter(attacker, start_a),
                "defender": self.service._replay_fighter(defender, start_b),
                "winner": result["winner"], "state": result["state"],
                "events": result["events"], "logs": result["logs"], "displayLogs": result["logs"],
                "opening": event_opening, "transition": transition, "traitDelta": 0,
                "phase": phase, "bossHp": start_b if phase else None, "wave": wave,
                "playerTeam": [self.service._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in self.players],
                "enemyTeam": [self.service._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in self.enemies],
            })
            if player["hp"] <= 0:
                self._rotate()
            elif boundary and floor and enemy["hp"] > 0:
                self._choose_or_rotate("敌人进入下一阶段")
            if boundary:
                break
        return enemy["hp"] <= floor, total_actions, finisher

    def _ordinary(self) -> None:
        stage_id = self.stage_id
        tactic_id = self.tactic["id"]
        order = list(range(len(self.enemies)))
        if stage_id == "4-3" and tactic_id.endswith("mark"):
            order = [4, 0, 1, 2, 3]
        if stage_id == "4-5" and tactic_id.endswith("seal"):
            order = [3, 0, 1, 2, 4]
        if stage_id == "5-1" and tactic_id.endswith("lure"):
            self.enemies[0]["hp"] = 0
            order.remove(0)
        actions_total = 0
        wave_actions = 0
        marks = 0
        tide_hits = 0
        gears_stopped = 0
        alert = 1 if stage_id == "5-1" and tactic_id.endswith("lure") else 0
        oath = 0
        witness_hp = 100
        ledger_left = 28 if tactic_id.endswith("guard") else 21
        channel_closed = set()
        combination_prevented = True
        for position, enemy_index in enumerate(order):
            if self.active is None:
                break
            wave = 1 + sum(position >= marker for marker in self.encounter.get("wave_after", []))
            opening = f"第 {wave} 波: {self.enemies[enemy_index]['fighter']['name']} 登场."
            bonus: dict[str, float] = {}
            if stage_id == "4-1" and position == 4:
                opening += " 执火人点燃原账,焚毁倒计时开始."
            if stage_id == "4-2" and position in (2, 5):
                opening += " 涨潮预告: 漕埠水位暴涨."
                if tactic_id.endswith("high") or position == 5 and tactic_id.endswith("cable"):
                    opening += " 战术使队伍避开本次涨潮."
                else:
                    damage = self._harm(0.17 if tactic_id.endswith("cable") else 0.12)
                    tide_hits += 1
                    opening += f" 涨潮冲击造成 {damage} 点伤害."
            if stage_id == "4-3" and enemy_index == 4:
                effective_marks = max(0, marks - (1 if self.clue_active else 0))
                bonus["atk"] = 1 + 0.05 * effective_marks
                opening += f" 假银印记 {effective_marks} 层,账房攻势增强."
                if tactic_id.endswith("mark") and any(self.enemies[index]["hp"] > 0 for index in range(4)):
                    bonus["atk"] *= 1.15
                    opening += " 诱敌仍在场外支援账房."
            if stage_id == "4-4" and position % 2 == 0:
                opening += f" 第 {position // 2 + 1} 组齿轮开始蓄力."
            if stage_id == "4-5" and position >= 3 and not combination_prevented:
                bonus["atk"] = 1.15
                opening += " 三司合令,后续敌人攻势增强."
            if stage_id == "4-5" and position == 0 and tactic_id.endswith("seal"):
                bonus["atk"] = 1.15
                opening += " 先夺印触发首战强攻."
            if stage_id == "5-1" and position in (2, 4, 6) and alert >= 3:
                damage = self._harm(0.11)
                opening += f" 警戒齐射造成 {damage} 点伤害."
            if stage_id == "5-2" and position >= 4:
                if "food" not in channel_closed:
                    bonus["atk"] = 1.14
                    opening += " 粮渠未断,敌方攻势增强."
                if "medicine" not in channel_closed:
                    self.enemies[enemy_index]["hp"] = min(
                        self.enemies[enemy_index]["fighter"]["stats"]["hp"],
                        self.enemies[enemy_index]["hp"] + 35,
                    )
                    opening += " 药渠未断,敌方气血得到补给."
            if stage_id == "5-4" and oath >= 3:
                damage = self._harm(0.09)
                opening += f" 誓印反击造成 {damage} 点伤害."
            if stage_id == "5-4" and tactic_id.endswith("curse") and oath:
                target = self.enemies[enemy_index]
                target["hp"] = max(1, target["hp"] - 18 * oath)
                damage = self._harm(0.025)
                opening += f" 借咒反伤敌人,我方承受 {damage} 点反震."
            if stage_id == "5-3" and tactic_id.endswith("key") and position == 0:
                bonus["atk"] = 1.15
                opening += " 夺钥成功,首波狱卒拼死反扑."
            before = len(self.duels)
            passed, actions, _ = self._fight(enemy_index, opening=opening, wave=wave, enemy_bonus=bonus)
            if not passed:
                break
            actions_total += actions
            wave_actions += actions
            if stage_id == "4-1" and position >= 4:
                ledger_left -= actions
                self._append_transition(f"原账焚毁倒计时剩余 {max(0, ledger_left)} 次行动.")
            if stage_id == "4-3" and enemy_index != 4 and self.enemies[4]["hp"] > 0 and actions >= (13 if self.clue_active else 10):
                if not tactic_id.endswith("seal"):
                    marks += 1
                    self._append_transition("诱敌拖延成功,假银印记增加一层.")
            if stage_id == "4-4" and position % 2 == 1:
                limit = 17 if tactic_id.endswith("wedge") else 14
                if self.clue_active:
                    limit += 3
                if wave_actions <= limit:
                    gears_stopped += 1
                    self._append_transition("齿轮被及时停下.")
                    if tactic_id.endswith("counter") and position + 1 < len(order):
                        next_enemy = self.enemies[order[position + 1]]
                        next_enemy["hp"] = max(1, next_enemy["hp"] - 45)
                        self._harm(0.035)
                else:
                    damage = self._harm(0.08)
                    self._append_transition(f"齿轮过热,压制造成 {damage} 点伤害.")
                wave_actions = 0
            if stage_id == "4-5" and position == 3:
                limit = 35 if tactic_id.endswith("seal") else 27
                combination_prevented = actions_total <= limit
                self._append_transition("三司合令被阻止." if combination_prevented else "三司合令完成.")
            if stage_id == "5-1" and position in (1, 3, 5):
                limit = 20 if tactic_id.endswith("quiet") else 18
                alert += int(wave_actions > limit)
                self._append_transition(f"林中警戒升至 {alert} 层.")
                wave_actions = 0
            if stage_id == "5-2" and position in (1, 3):
                channel = "food" if position == 1 else "medicine"
                limit = 31 if self.clue_active else 25
                if actions_total <= limit or (position == 1 and tactic_id.endswith("food")) or (position == 3 and tactic_id.endswith("medicine")):
                    channel_closed.add(channel)
                    self._append_transition("粮渠关闭." if channel == "food" else "药渠关闭.")
            if stage_id == "5-3":
                threat = max(3, actions * (1 if tactic_id.endswith("protect") else 2))
                if tactic_id.endswith("key") and position == 1:
                    threat = 0
                witness_hp = max(0, witness_hp - threat)
                self._append_transition(f"证人保护进度: {witness_hp}/100.")
            if stage_id == "5-4":
                threshold = 14 if self.clue_active else 11
                oath += int(actions >= threshold)
                if tactic_id.endswith("flags") and position in (1, 3):
                    oath = max(0, oath - 2)
                    self._append_transition("誓旗被毁,誓印消散.")
                else:
                    self._append_transition(f"誓印累积至 {oath} 层.")
            if position + 1 in self.encounter.get("rotate_after", []):
                if self.active is not None and self.players[self.active]["hp"] > 0 and position + 1 < len(order):
                    self._choose_or_rotate("下一段敌人即将接战")
            if len(self.duels) == before:
                break
        self.metrics = {
            "ledger_saved": ledger_left > 0,
            "tide_hits": tide_hits,
            "marks": max(0, marks - (1 if self.clue_active and stage_id == "4-3" else 0)),
            "gears_stopped": gears_stopped,
            "combination_prevented": combination_prevented,
            "alert": alert,
            "channels_closed": len(channel_closed),
            "witness_alive": witness_hp > 0,
            "oath": oath,
        }

    def _treasurer(self) -> None:
        # The treasurer appears between two escort waves, keeping one health pool.
        for index, floor, wave, phase in ((0, 0, 1, 0), (1, 0, 1, 0), (4, 0, 2, 1),
                                          (2, 0, 3, 0), (3, 0, 3, 0), (4, 0, 4, 2)):
            if self.active is None:
                break
            boss = index == 4
            if boss and phase == 1:
                floor = round(self.enemies[4]["fighter"]["stats"]["hp"] * 0.5)
            opening = "司库护盾仍由护卫供给." if boss and phase == 1 else "司库半血,焚账开始蓄力." if boss else "司库护卫登场."
            bonus = ({"def": 1.16 if self.clue_active else 1.30} if phase == 1 else
                     {"def": 1.12 if self.tactic["id"].endswith("fire") else 1.0}) if boss else None
            passed, actions, _ = self._fight(index, floor=floor, opening=opening, wave=wave,
                                             phase=phase, enemy_bonus=bonus)
            if not passed:
                break
            if boss and phase == 2:
                limit = 21 if self.tactic["id"].endswith("save") else 15
                interrupted = actions <= limit - 4
                saved = actions <= limit
                self.metrics.update(ledger_saved=saved, burn_interrupted=interrupted)
                if not interrupted:
                    damage = self._harm(0.08 if self.tactic["id"].endswith("fire") else 0.17)
                    self._append_transition(f"焚账火势爆发,我方承受 {damage} 点伤害.")
                else:
                    self._append_transition("焚账蓄力被击破,原账保全.")
            if index in (1, 3):
                if self.active is not None and self.players[self.active]["hp"] > 0:
                    self._choose_or_rotate("下一组护卫即将登场")

    def _twin_bosses(self) -> None:
        interrupted: set[int] = set()
        resonance = 0
        thresholds = self.encounter["phase_thresholds"]
        schedule = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)]
        for enemy_index, phase_index in schedule:
            if self.active is None:
                break
            enemy = self.enemies[enemy_index]
            floor = round(enemy["fighter"]["stats"]["hp"] * thresholds[phase_index] / 100) if phase_index < 2 else 0
            phase_name = self.encounter["phase_names"][phase_index]
            opening = f"{phase_name}: {enemy['fighter']['name']} 登场,场外首领正在积蓄共鸣."
            limit = (22 if self.tactic["id"].endswith("cut") else 16) + (4 if self.clue_active and phase_index == 0 else 0)
            if resonance >= limit:
                damage = self._harm(0.12 if self.tactic["id"].endswith("cut") else 0.17)
                opening += f" 双阙合击造成 {damage} 点伤害."
                resonance = 0
            passed, actions, _ = self._fight(enemy_index, floor=floor, opening=opening,
                                             phase=phase_index + 1, wave=phase_index + 1,
                                             enemy_bonus={"atk": 1.08 if enemy_index else 1.0})
            if not passed:
                break
            resonance += actions
            if resonance < limit and phase_index == 1:
                interrupted.add(enemy_index)
                self._append_transition(f"{enemy['fighter']['name']} 的合击被打断.")
                if self.tactic["id"].endswith("turn") and floor:
                    enemy["hp"] = max(1, enemy["hp"] - 40)
                    self._append_transition("共鸣反噬首领,额外损失 40 气血.")
            elif resonance < limit:
                self._append_transition("双阙共鸣仍在蓄力.")
            else:
                self._append_transition("共鸣蓄满,下一段将发动合击.")
            if floor == 0:
                resonance = 0
            if floor == 0:
                if self.active is not None and self.players[self.active]["hp"] > 0 and any(entry["hp"] > 0 for entry in self.enemies):
                    self._choose_or_rotate("另一名首领即将接战")
        self.metrics = {"interruptions": len(interrupted)}

    def _alliance_chief(self) -> None:
        boss = self.enemies[0]
        maximum = boss["fighter"]["stats"]["hp"]
        broken: dict[int, int] = {}
        for phase_index, percent in enumerate(self.encounter["phase_thresholds"] + [0]):
            if self.active is None:
                break
            floor = round(maximum * percent / 100)
            name = self.encounter["phase_names"][phase_index]
            opening = f"{name} 展开,盟印即将暴露."
            if phase_index == 3:
                opening = "盟主终式蓄力,全队迎接最后一击."
            bonus = ({"def": 1.13} if phase_index < 2 else {"atk": 0.90} if phase_index == 3 else None) if self.tactic["id"].endswith("oath") else None
            passed, actions, finisher = self._fight(0, floor=floor, opening=opening,
                                                    phase=phase_index + 1, wave=phase_index + 1,
                                                    enemy_bonus=bonus)
            if not passed:
                break
            if phase_index < 3:
                window = (17 if self.tactic["id"].endswith("wealth") else 13) if phase_index < 2 else 15
                if self.clue_active:
                    window += 3
                if actions <= window and finisher is not None:
                    broken[phase_index] = finisher
                    self._append_transition(f"{name} 被 {self.players[finisher]['fighter']['name']} 击破.")
                else:
                    damage = self._harm(0.21 if phase_index == 2 and self.tactic["id"].endswith("wealth") else 0.11)
                    self._append_transition(f"{name} 未能及时击破,绝招造成 {damage} 点伤害.")
        self.metrics = {"broken_seals": len(broken), "distinct_seal_breakers": len(set(broken.values()))}

    def run(self) -> dict[str, Any]:
        if self.stage_id == "4-6":
            self._treasurer()
        elif self.stage_id == "5-5":
            self._twin_bosses()
        elif self.stage_id == "5-6":
            self._alliance_chief()
        else:
            self._ordinary()
        victory = all(entry["hp"] <= 0 for entry in self.enemies) and any(entry["hp"] > 0 for entry in self.players)
        survivors = sum(entry["hp"] > 0 for entry in self.players)
        participants = len(self.entered)
        metric = self.metrics
        rules: dict[str, tuple[bool, bool]] = {
            "4-1": (participants >= 2, participants == 3 and metric.get("ledger_saved", False)),
            "4-2": (survivors >= 2, participants == 3 and metric.get("tide_hits", 9) <= 1),
            "4-3": (metric.get("marks", 9) <= 2, participants == 3 and metric.get("marks", 9) <= 1),
            "4-4": (metric.get("gears_stopped", 0) >= 1, participants == 3 and metric.get("gears_stopped", 0) == 3),
            "4-5": (survivors >= 2, participants == 3 and metric.get("combination_prevented", False)),
            "4-6": (metric.get("ledger_saved", False), metric.get("ledger_saved", False) and participants == 3 and metric.get("burn_interrupted", False)),
            "5-1": (metric.get("alert", 9) <= 2, participants == 3 and metric.get("alert", 9) <= 1),
            "5-2": (metric.get("channels_closed", 0) >= 1, metric.get("channels_closed", 0) == 2 and survivors >= 2),
            "5-3": (metric.get("witness_alive", False), metric.get("witness_alive", False) and participants == 3),
            "5-4": (metric.get("oath", 9) <= 2, participants == 3 and metric.get("oath", 9) <= 1),
            "5-5": (metric.get("interruptions", 0) >= 1, participants == 3 and metric.get("interruptions", 0) == 2),
            "5-6": (metric.get("broken_seals", 0) >= 2, metric.get("distinct_seal_breakers", 0) == 3),
        }
        second, third = rules[self.stage_id]
        criteria = [victory, victory and second, victory and second and third]
        return {
            "victory": victory, "stars": sum(criteria) if victory else 0,
            "objectiveResults": [{"description": text, "met": met} for text, met in zip(self.stage["star_objectives"], criteria)],
            "duels": self.duels,
            "playerTeam": [self.service._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in self.players],
            "enemyTeam": [self.service._replay_fighter(entry["fighter"], int(entry["hp"])) for entry in self.enemies],
            "mechanicResults": metric,
        }
