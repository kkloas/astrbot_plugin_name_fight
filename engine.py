from __future__ import annotations

import random
from copy import deepcopy
from hashlib import sha256
from typing import Any


INTRO_TEMPLATES = [
    "{attacker} 与 {defender} 遥遥相对，各自暗自提气，气氛一时凝重到了极点。",
    "伴随着一阵低沉的破风声，{attacker} 越步而出，目光如炬，直逼 {defender}。",
    "{defender} 严阵以待，冷冷注视着前方的 {attacker}，一场恶战在所难免。",
    "两人眼神交汇，不发一语，无形的杀机已在 {attacker} 与 {defender} 之间弥漫开来。",
    "{attacker} 缓缓亮出兵刃，遥指 {defender}，四周的空气仿佛都为之一滞。",
    "场中劲风骤起，{attacker} 看准时机，率先向 {defender} 发难！",
]

QUICK_WIN_TEMPLATES = [
    "不过五手，胜负便已见分晓。【{attacker}】这一轮出手快得像催命，打得【{defender}】连台词都没来得及多说。",
    "这一战结束得比热茶变温还快，【{defender}】尚未站稳阵脚，便被【{attacker}】一口气按到了地上。",
    "转眼之间，【{defender}】就被打得找不着北，【{attacker}】这波属于快刀斩乱麻，半点都没拖泥带水。",
    "这哪里是比武，分明是单方面物理超度！热茶还烫嘴呢，【{defender}】已经被【{attacker}】打到再起不能。",
]

DOMINANT_WIN_TEMPLATES = [
    "从头到尾都被压着打，【{defender}】几次想翻身都被当场按回去，这一局【{attacker}】赢得相当霸道。",
    "这一战几乎尽在【{attacker}】掌控之中，【{defender}】虽咬牙支撑，到底还是被一路推平了场面。",
    "【{attacker}】越打越顺手，【{defender}】越打越胆战心惊，最终只能老老实实认下这一败。",
    "【{defender}】拼尽全力，却连【{attacker}】的衣角都没摸到几下，这场战斗简直是一部惨绝人寰的防守反击反面教材。",
]

STANDARD_WIN_TEMPLATES = [
    "胜负已分！【{defender}】眼前一黑，颓然倒地，此战由【{attacker}】拿下。",
    "【{defender}】闷哼一声，再也压制不住翻涌的气血，连退数步后单膝跪地，败下阵来。",
    "尘埃落定，【{attacker}】缓缓收敛气息，只留【{defender}】倒在原地大口吐血胜负已不言而喻。",
    "伴随着最后一声闷响，【{defender}】再也压制不住翻涌的气血，“扑通”一声跪倒在地，成就了【{attacker}】的威名。",
]

CLUTCH_WIN_TEMPLATES = [
    "这一战打到最后，双方都只剩一口硬气吊着。偏偏就是这口气，让【{attacker}】比【{defender}】多撑住了半步。",
    "两人都已逼近极限，场面惨得像谁都没捞着好处。可到最后，还是【{attacker}】险险把【{defender}】拖垮了。",
    "胜负只在一线之间，【{attacker}】自己也伤得不轻，却还是硬生生把【{defender}】先送出了局。",
    "两人拼到双双重伤，眼看就要同归于尽！【{attacker}】全凭一股“我不能掉分”的顽强意志，比【{defender}】撑得更久！",
]

JUDGED_WIN_TEMPLATES = [
    "两人一路缠斗到推演上限，谁也没能当场拍死谁。可按剩余气血来看，还是【{attacker}】更像那个站到最后的人。",
    "这一战拖得极久，久到旁观的人都替他们累。待战局强行收束时，仍以【{attacker}】略胜半筹。",
    "打到最后已经不是谁更猛，而是谁更能熬。最终按剩余血量裁定，【{attacker}】小胜【{defender}】。",
]

DRAW_TEMPLATES = [
    "这一架打得难解难分，直到推演上限也没谁真正压过谁，最后只能判作平手。",
    "两人鏖战良久，气机都快拧成麻花了，结果谁也没法把对面彻底放倒，只能算作和局。",
    "这场对决从头咬到尾，打得像谁也不服谁。等到战局收住时，终究还是个不分胜负。",
]

DEFAULT_CRIT_REACTIONS = [
    "这一击劲透肌骨，{defender} 周身气血都被震得一阵翻腾！",
    "重创骤至，{defender} 面色顿时一白，脚下也跟着踉跄起来。",
]

TURN_START_TEMPLATES = [
    "【第{action_no}手】{attacker} 气机先动，率先逼近 {defender}。",
    "【第{action_no}手】{attacker} 抢先变招，攻势直指 {defender}。",
    "【第{action_no}手】{attacker} 眼神一厉，先一步朝 {defender} 发难。",
    "【第{action_no}手】{attacker} 脚下骤进，先手压向 {defender}。",
    "【第{action_no}手】{attacker} 看准空当，抢在前头向 {defender} 递出杀招。",
]

HIT_REACTION_TEMPLATES = {
    "head": [
        "{defender} 只觉头颅剧震，眼前一时间金星乱冒。",
        "这一击震得 {defender} 脑中嗡鸣，身形都跟着晃了一晃。",
    ],
    "chest": [
        "{defender} 胸口如遭重锤，气息顿时一滞。",
        "劲力直透胸膛，{defender} 闷哼一声，胸中气血翻腾不休。",
    ],
    "arm": [
        "{defender} 只觉臂膀一麻，半边架势都被这一击震散。",
        "这一击打得 {defender} 手臂酸麻，出招顿时滞涩了几分。",
    ],
    "abdomen": [
        "{defender} 腰腹剧痛，真气运转都跟着散乱起来。",
        "这一击直入腰腹，{defender} 痛得身形微弓，气机一时不畅。",
    ],
    "leg": [
        "{defender} 腿侧吃痛，脚下步伐顿时乱了半拍。",
        "这一击扫得 {defender} 下盘一晃，险些立足不稳。",
    ],
}

BODY_PARTS = {
    "head": {"label": "\u5934\u90e8", "weight": 0.13, "damage_multiplier": 1.35},
    "chest": {"label": "\u5fc3\u53e3", "weight": 0.24, "damage_multiplier": 1.2},
    "arm": {"label": "\u80a9\u81c2", "weight": 0.21, "damage_multiplier": 0.9},
    "abdomen": {"label": "\u8170\u8179", "weight": 0.24, "damage_multiplier": 1.0},
    "leg": {"label": "\u817f\u4fa7", "weight": 0.18, "damage_multiplier": 0.85},
}

TEXT_PART_TO_KEY = {
    "\u5934": "head",
    "\u5934\u90e8": "head",
    "\u5934\u9876": "head",
    "\u5929\u7075": "head",
    "\u9762\u95e8": "head",
    "\u7709\u5fc3": "head",
    "\u592a\u9633\u7a74": "head",
    "\u592a\u9633\u7a9d": "head",
    "\u54bd\u5589": "head",
    "\u540e\u8111": "head",
    "\u989d\u89d2": "head",
    "\u80a9\u9888": "head",
    "\u80f8\u53e3": "chest",
    "\u5de6\u80f8": "chest",
    "\u53f3\u80f8": "chest",
    "\u5fc3\u53e3": "chest",
    "\u80cc\u5fc3": "chest",
    "\u53cc\u80a9": "chest",
    "\u80a9\u81c2": "arm",
    "\u624b\u8155": "arm",
    "\u624b\u81c2": "arm",
    "\u5c0f\u81c2": "arm",
    "\u624b\u8098": "arm",
    "\u8170\u8179": "abdomen",
    "\u5c0f\u8179": "abdomen",
    "\u808b\u4e0b": "abdomen",
    "\u4fa7\u808b": "abdomen",
    "\u8179\u90e8": "abdomen",
    "\u4e39\u7530": "abdomen",
    "\u80cc\u90e8": "abdomen",
    "\u540e\u80cc": "abdomen",
    "\u8170\u95f4": "abdomen",
    "\u5168\u8eab": "abdomen",
    "\u817f\u4fa7": "leg",
    "\u4e0b\u76d8": "leg",
    "\u811a\u8e1d": "leg",
    "\u819d\u5f2f": "leg",
    "\u53cc\u817f": "leg",
}

DODGE_TEMPLATES = [
    "{defender} 脚下一错，借【{qinggong}】之势避开了这一击。",
    "{defender} 身形一晃，险之又险地让过来势，{attacker} 这一招落空。",
    "电光石火之间，{defender} 翻身后撤，将攻势尽数化去。",
]

STATE_TEXT = {
    "stunned": "\u203b[{target}:\u7729\u6655]",
    "slowed": "\u203b[{target}:\u8fdf\u7f13]",
    "bleeding": "\u203b[{target}:\u6d41\u8840]",
    "weakened": "\u203b[{target}:\u865a\u5f31]",
    "disarmed": "\u203b[{target}:\u7f34\u68b0]",
    "armor_broken": "\u203b[{target}:\u7834\u7532]",
}


class CombatEngine:
    def __init__(self, max_ticks: int = 100, max_actions: int = 50) -> None:
        self.max_ticks = max_ticks
        self.max_actions = max_actions

    def battle(self, fighter_a: dict[str, Any], fighter_b: dict[str, Any]) -> list[str]:
        logs, _winner, _state = self.battle_with_state(fighter_a, fighter_b)
        return logs

    def battle_with_result(self, fighter_a: dict[str, Any], fighter_b: dict[str, Any]) -> tuple[list[str], str | None]:
        logs, winner_name, _state = self.battle_with_state(fighter_a, fighter_b)
        return logs, winner_name

    def battle_with_events(self, fighter_a: dict[str, Any], fighter_b: dict[str, Any]) -> dict[str, Any]:
        events: list[dict[str, Any]] = []
        logs, winner_name, state = self.battle_with_state(fighter_a, fighter_b, _events=events)
        victory_time = (int(state["actions"]) + 1) * 1900
        victory = next((event for event in events if event.get("type") == "victory_start"), None)
        if victory is None:
            victory = {"type": "victory_start", "victoryKind": "standard" if winner_name and any(event.get("type") == "damage" and event.get("hpAfter") == 0 for event in events) else "judged" if winner_name else "draw"}
            events.append(victory)
        victory.update(time=victory_time,
                       victoryVariant=sha256("\n".join(logs).encode("utf-8")).digest()[0] % 3)
        events.append({
            "type": "battle_end",
            "time": victory_time + 1800,
            "winner": winner_name,
            "final": {
                "a": {"hp": state["fighter_a_hp"], "maxHp": state["fighter_a_max_hp"]},
                "b": {"hp": state["fighter_b_hp"], "maxHp": state["fighter_b_max_hp"]},
            },
            "logs": [logs[-1]],
        })
        return {"logs": logs, "winner": winner_name, "state": state, "events": events}

    def battle_with_state(
        self,
        fighter_a: dict[str, Any],
        fighter_b: dict[str, Any],
        collect_replay: bool = False,
        _events: list[dict[str, Any]] | None = None,
    ) -> tuple[list[str], str | None, dict[str, Any]]:
        actor_a = self._build_actor(fighter_a)
        actor_b = self._build_actor(fighter_b)
        logs: list[str] = [
            random.choice(INTRO_TEMPLATES).format(attacker=actor_a["name"], defender=actor_b["name"]),
            self._panel_text(actor_a, actor_b),
        ]
        if _events is not None:
            replay = {"events": _events, "time": 0, "action": 0}
            for side, actor in (("a", actor_a), ("b", actor_b)):
                actor["_replay"] = replay
                actor["_side"] = side
            self._emit(actor_a, "battle_start", logs=list(logs), fighters={
                side: {"hp": int(actor["hp"]), "maxHp": int(actor["max_hp"])}
                for side, actor in (("a", actor_a), ("b", actor_b))
            })
        opening_logs = self._apply_battle_start_effects(actor_a, actor_b)
        logs.extend(opening_logs)
        if opening_logs:
            self._emit(actor_a, "opening", logs=opening_logs)

        replay_frames: list[dict[str, Any]] = []
        if collect_replay:
            replay_frames.append(self._replay_snapshot(actor_a, actor_b, 0, None, None, logs, "intro"))
        winner_name: str | None = None
        ticks = 0
        actions = 0
        charge_from: dict[str, Any] | None = None
        charge_ticks = 0
        charge_time = 0
        while ticks < self.max_ticks and actions < self.max_actions:
            if _events is not None and charge_from is None:
                charge_from = self._initiative_snapshot(actor_a, actor_b)
                charge_ticks = 0
                charge_time = int(replay["time"])
            ticks += 1
            actor_a["ag"] += self._effective_spd(actor_a)
            actor_b["ag"] += self._effective_spd(actor_b)
            charge_ticks += 1

            ready = [actor for actor in (actor_a, actor_b) if actor["ag"] >= 100 and actor["hp"] > 0]
            if not ready:
                continue

            if _events is not None:
                replay["time"] = charge_time
                snapshot = self._initiative_snapshot(actor_a, actor_b)
                self._emit(
                    actor_a,
                    "gauge_charge",
                    gaugeFrom=charge_from["gauge"] if charge_from else {"a": 0.0, "b": 0.0},
                    endTime=(actions + 1) * 1900 - 100,
                    ticksAdvanced=charge_ticks,
                    gauge=snapshot["gauge"],
                    speeds=snapshot["speeds"],
                )
                charge_from = None
                charge_ticks = 0
                charge_time = 0

            ready.sort(key=lambda actor: (actor["ag"], random.random()), reverse=True)
            for attacker in ready:
                defender = actor_b if attacker is actor_a else actor_a
                if attacker["hp"] <= 0 or defender["hp"] <= 0 or attacker["ag"] < 100:
                    continue
                gauge_before = self._initiative_snapshot(actor_a, actor_b)
                attacker["ag"] -= 100
                actions += 1
                log_start = len(logs)
                if _events is not None:
                    replay["time"] = actions * 1900
                    replay["action"] = actions
                    current_gauge = self._initiative_snapshot(actor_a, actor_b)
                    self._emit(
                        attacker,
                        "turn_start",
                        target=defender["_side"],
                        gaugeBefore=gauge_before["gauge"],
                        gauge=current_gauge["gauge"],
                        speeds=current_gauge["speeds"],
                    )
                self._take_turn(attacker, defender, logs, actions)
                self._decrement_turn_states(attacker)
                self._cleanup_expired(attacker)
                self._cleanup_expired(defender)
                if collect_replay:
                    replay_frames.append(
                        self._replay_snapshot(
                            actor_a,
                            actor_b,
                            actions,
                            attacker["name"],
                            defender["name"],
                            logs[log_start:],
                            "action",
                        )
                    )
                if _events is not None:
                    replay["time"] = actions * 1900 + 1600
                    current_gauge = self._initiative_snapshot(actor_a, actor_b)
                    self._emit(
                        attacker,
                        "turn_end",
                        logs=logs[log_start:],
                        states={"a": deepcopy(actor_a["states"]), "b": deepcopy(actor_b["states"])},
                        weaponsReady={"a": actor_a["weapon_ready"], "b": actor_b["weapon_ready"]},
                        gauge=current_gauge["gauge"],
                        speeds=current_gauge["speeds"],
                    )
                if defender["hp"] <= 0 or attacker["hp"] <= 0:
                    if defender["hp"] <= 0 and attacker["hp"] <= 0:
                        logs.append(random.choice(DRAW_TEMPLATES))
                        if collect_replay:
                            replay_frames.append(self._replay_snapshot(actor_a, actor_b, actions, None, None, logs[-1:], "outcome"))
                        return logs, None, self._battle_state(actor_a, actor_b, actions, replay_frames, collect_replay)
                    winner = attacker if attacker["hp"] > 0 else defender
                    loser = defender if winner is attacker else attacker
                    logs.append(self._pick_outro_text(winner, loser, actions, judged=False))
                    winner_name = winner["name"]
                    if collect_replay:
                        replay_frames.append(self._replay_snapshot(actor_a, actor_b, actions, winner["name"], loser["name"], logs[-1:], "outcome"))
                    return logs, winner_name, self._battle_state(actor_a, actor_b, actions, replay_frames, collect_replay)
                if actions >= self.max_actions:
                    break

        hp_ratio_a = actor_a["hp"] / actor_a["max_hp"]
        hp_ratio_b = actor_b["hp"] / actor_b["max_hp"]
        if abs(hp_ratio_a - hp_ratio_b) < 0.01:
            logs.append(random.choice(DRAW_TEMPLATES))
        else:
            winner, loser = (actor_a, actor_b) if hp_ratio_a > hp_ratio_b else (actor_b, actor_a)
            logs.append(self._pick_outro_text(winner, loser, actions, judged=True))
            winner_name = winner["name"]
        if collect_replay:
            replay_frames.append(self._replay_snapshot(actor_a, actor_b, actions, winner_name, None, logs[-1:], "outcome"))
        return logs, winner_name, self._battle_state(actor_a, actor_b, actions, replay_frames, collect_replay)

    def _battle_state(
        self,
        actor_a: dict[str, Any],
        actor_b: dict[str, Any],
        actions: int,
        replay_frames: list[dict[str, Any]],
        collect_replay: bool,
    ) -> dict[str, Any]:
        state: dict[str, Any] = {
            "fighter_a_hp": int(actor_a["hp"]),
            "fighter_b_hp": int(actor_b["hp"]),
            "fighter_a_max_hp": int(actor_a["max_hp"]),
            "fighter_b_max_hp": int(actor_b["max_hp"]),
            "actions": actions,
        }
        if collect_replay:
            state["replay"] = replay_frames
        return state

    def _replay_snapshot(
        self,
        actor_a: dict[str, Any],
        actor_b: dict[str, Any],
        action: int,
        attacker: str | None,
        defender: str | None,
        lines: list[str],
        kind: str,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "action": action,
            "attacker": attacker,
            "defender": defender,
            "lines": list(lines),
            "fighter_a_hp": int(actor_a["hp"]),
            "fighter_b_hp": int(actor_b["hp"]),
            "fighter_a_max_hp": int(actor_a["max_hp"]),
            "fighter_b_max_hp": int(actor_b["max_hp"]),
            "fighter_a_states": [str(state.get("type", "")) for state in actor_a.get("states", [])],
            "fighter_b_states": [str(state.get("type", "")) for state in actor_b.get("states", [])],
        }
    def _build_actor(self, fighter: dict[str, Any]) -> dict[str, Any]:
        stats = deepcopy(fighter["stats"])
        return {
            "name": fighter["name"],
            "stats": stats,
            "hp": max(0, min(stats["hp"], int(fighter.get("current_hp", stats["hp"])))),
            "max_hp": stats["hp"],
            "ag": 0.0,
            "martial_art": fighter["martial_art"],
            "neigong": fighter["neigong"],
            "qinggong": fighter["qinggong"],
            "states": [],
            "passive_usage": {},
            "special_usage": {},
            "weapon_ready": True,
        }


    def _panel_text(self, actor_a: dict[str, Any], actor_b: dict[str, Any]) -> str:
        return (
            "{a} [{am}/{an}/{aq}] 气血 {ahp} 攻击 {aatk} 防御 {adef} 速度 {aspd:.1f} 暴击 {acrt:.1f}% 闪避 {aeva:.1f}% | "
            "{b} [{bm}/{bn}/{bq}] 气血 {bhp} 攻击 {batk} 防御 {bdef} 速度 {bspd:.1f} 暴击 {bcrt:.1f}% 闪避 {beva:.1f}%"
        ).format(
            a=actor_a["name"],
            am=actor_a["martial_art"]["name"],
            an=actor_a["neigong"]["name"],
            aq=actor_a["qinggong"]["name"],
            ahp=actor_a["max_hp"],
            aatk=actor_a["stats"]["atk"],
            adef=actor_a["stats"]["def"],
            aspd=actor_a["stats"]["spd"],
            acrt=actor_a["stats"]["crt"],
            aeva=actor_a["stats"]["eva"],
            b=actor_b["name"],
            bm=actor_b["martial_art"]["name"],
            bn=actor_b["neigong"]["name"],
            bq=actor_b["qinggong"]["name"],
            bhp=actor_b["max_hp"],
            batk=actor_b["stats"]["atk"],
            bdef=actor_b["stats"]["def"],
            bspd=actor_b["stats"]["spd"],
            bcrt=actor_b["stats"]["crt"],
            beva=actor_b["stats"]["eva"],
        )

    def _pick_outro_text(self, winner: dict[str, Any], loser: dict[str, Any], actions: int, judged: bool) -> str:
        winner_ratio = 0.0 if winner["max_hp"] <= 0 else winner["hp"] / winner["max_hp"]
        kind = "judged" if judged else "quick" if actions <= 5 else "dominant" if winner_ratio >= 0.55 else "clutch" if winner_ratio <= 0.2 else "standard"
        self._emit(winner, "victory_start", target=None, victoryKind=kind)
        if judged:
            pool = JUDGED_WIN_TEMPLATES
        elif actions <= 5:
            pool = QUICK_WIN_TEMPLATES
        elif winner_ratio >= 0.55:
            pool = DOMINANT_WIN_TEMPLATES
        elif winner_ratio <= 0.2:
            pool = CLUTCH_WIN_TEMPLATES
        else:
            pool = STANDARD_WIN_TEMPLATES
        return random.choice(pool).format(attacker=winner["name"], defender=loser["name"])

    def _take_turn(self, attacker: dict[str, Any], defender: dict[str, Any], logs: list[str], action_no: int) -> None:
        if attacker["hp"] <= 0:
            return
        logs.append(
            random.choice(TURN_START_TEMPLATES).format(
                action_no=action_no,
                attacker=attacker["name"],
                defender=defender["name"],
            )
        )
        if self._resolve_turn_start(attacker, logs):
            self._emit(attacker, "turn_skip", reason="stunned" if attacker["hp"] > 0 else "fallen")
            return
        if not attacker["weapon_ready"]:
            attacker["weapon_ready"] = True
            self._emit(attacker, "turn_skip", reason="disarmed")
            logs.append("{name} 兵刃脱手, 只得先稳住架势并拾回武器, 这一回合未能出手。".format(name=attacker["name"]))
            logs.extend(self._resolve_action_end_effects(attacker))
            return

        move = random.choice(attacker["martial_art"]["moves"])
        if "_replay" in attacker:
            attacker["_replay"]["time"] = action_no * 1900 + 550
            self._emit(attacker, "attack", target=defender.get("_side"), move=move.get("name", ""), martialArtId=attacker["martial_art"].get("id"), weaponType=attacker["martial_art"].get("type"), moveIndex=attacker["martial_art"].get("moves", []).index(move))
        if self._roll(self._effective_eva(defender)):
            if "_replay" in attacker:
                attacker["_replay"]["time"] = action_no * 1900 + 950
                self._emit(attacker, "dodge", target=defender.get("_side"), sourceSkill={"category": "qinggong", "id": defender["qinggong"].get("id"), "name": defender["qinggong"].get("name", "")})
            logs.append(
                random.choice(DODGE_TEMPLATES).format(
                    attacker=attacker["name"],
                    defender=defender["name"],
                    qinggong=defender["qinggong"]["name"],
                )
            )
            logs.extend(self._resolve_dodge_effects(defender))
            logs.extend(self._resolve_action_end_effects(attacker))
            return

        part_key, body_part_text = self._pick_body_part(attacker, move)
        attack_text = self._render_move_text(attacker, defender, move, body_part_text)
        tagged_attack_text = self._tagged_attack_text(attack_text, attacker["name"], defender["name"], body_part_text)
        damage_bonus_ratio = self._next_attack_damage_bonus(attacker)
        damage, crit = self._calculate_damage(attacker, defender, move, part_key, damage_bonus_ratio=damage_bonus_ratio)
        if "_replay" in attacker:
            attacker["_replay"]["time"] = max(attacker["_replay"]["time"], action_no * 1900 + 950)
        guard = float(defender["neigong"].get("part_guard", {}).get(part_key, 1.0))
        if guard != 1.0:
            self._emit(defender, "guard", target=defender.get("_side"), multiplier=guard,
                       bodyPartKey=part_key, sourceSkill=self._skill_summary(defender, "neigong"))
        hp_before = int(defender["hp"])
        damage, mitigation_logs = self._apply_damage_defer(defender, damage)
        defender["hp"] = max(0, defender["hp"] - damage)
        logs.append(self._hit_reaction(defender, part_key))
        logs.append(
            "{text} \u9020\u6210 {damage} \u70b9\u4f24\u5bb3, {defender} \u5269\u4f59 {hp}/{max_hp} \u6c14\u8840\u3002".format(
                text=tagged_attack_text,
                damage=damage,
                defender=defender["name"],
                hp=defender["hp"],
                max_hp=defender["max_hp"],
            )
        )
        logs.extend(mitigation_logs)
        if crit:
            logs.append(self._crit_text(attacker, defender))
        logs.extend(self._consume_next_attack_damage_bonus(attacker, damage_bonus_ratio))
        self._hp_event(defender, hp_before, "strike", source=attacker, amount=damage,
                       crit=crit, bodyPart=body_part_text, bodyPartKey=part_key)
        logs.extend(self._resolve_fatal_block(defender))
        logs.extend(self._resolve_passives_after_hit(attacker, defender, damage, part_key))
        logs.extend(self._apply_move_effects(attacker, defender, move, part_key))
        logs.extend(self._resolve_action_end_effects(attacker))

    def _tag_name(self, name: str) -> str:
        return f"[{name}]"

    def _tag_part(self, body_part_text: str) -> str:
        return f"[{body_part_text}]"

    def _tagged_attack_text(self, text: str, attacker_name: str, defender_name: str, body_part_text: str) -> str:
        tagged = text
        token_map: dict[str, str] = {}
        for index, name in enumerate(sorted({attacker_name, defender_name}, key=len, reverse=True)):
            token = f'__NAME_TOKEN_{index}__'
            token_map[token] = self._tag_name(name)
            tagged = tagged.replace(name, token)
        tagged = tagged.replace(body_part_text, self._tag_part(body_part_text))
        for token, replacement in token_map.items():
            tagged = tagged.replace(token, replacement)
        return tagged

    def _render_move_text(self, attacker: dict[str, Any], defender: dict[str, Any], move: dict[str, Any], body_part_text: str) -> str:
        template = random.choice(move["texts"]) if move.get("texts") else move["template"]
        return template.format(
            attacker=attacker["name"],
            defender=defender["name"],
            martial_art=attacker["martial_art"]["name"],
            move_name=move["name"],
            body_part=body_part_text,
            body_part_text=body_part_text,
        )

    def _crit_text(self, attacker: dict[str, Any], defender: dict[str, Any]) -> str:
        pool = attacker["martial_art"].get("crit_reactions") or DEFAULT_CRIT_REACTIONS
        return random.choice(pool).format(attacker=self._tag_name(attacker["name"]), defender=self._tag_name(defender["name"]))

    def _hit_reaction(self, defender: dict[str, Any], part_key: str) -> str:
        pool = HIT_REACTION_TEMPLATES.get(part_key, HIT_REACTION_TEMPLATES["chest"])
        return random.choice(pool).format(defender=self._tag_name(defender["name"]))

    def _resolve_turn_start(self, actor: dict[str, Any], logs: list[str]) -> bool:
        stunned_state = self._find_state(actor, "stunned")
        if stunned_state is not None:
            stunned_state["duration"] -= 1
            logs.append("{name} \u773c\u524d\u4e00\u9635\u53d1\u9ed1, \u6c14\u673a\u7d0a\u4e71, \u53ea\u80fd\u767d\u767d\u9519\u8fc7\u8fd9\u4e00\u8f6e\u51fa\u624b\u3002".format(name=actor["name"]))
            return True

        for state in list(actor["states"]):
            if state["type"] == "bleeding":
                damage = self._bleeding_damage(actor, state)
                hp_before = int(actor["hp"])
                actor["hp"] = max(0, actor["hp"] - damage)
                logs.append("{name} \u4f24\u53e3\u8ff8\u88c2, \u6d41\u8840\u53d1\u4f5c, \u635f\u5931 {damage} \u70b9\u6c14\u8840\u3002".format(name=actor["name"], damage=damage))
                state["duration"] -= 1
                self._hp_event(actor, hp_before, "bleeding", amount=damage)
                logs.extend(self._resolve_fatal_block(actor))
                if actor["hp"] <= 0:
                    return True
            elif state["type"] == "deferred_damage":
                pending = int(state.get("pending_damage", 0))
                duration = max(1, int(state.get("duration", 1)))
                damage = max(1, (pending + duration - 1) // duration)
                damage = min(damage, pending)
                hp_before = int(actor["hp"])
                actor["hp"] = max(0, actor["hp"] - damage)
                state["pending_damage"] = max(0, pending - damage)
                state["duration"] -= 1
                logs.append("{name} \u4f53\u5185\u88ab\u538b\u4e0b\u7684\u6697\u52b2\u9aa4\u7136\u53d1\u4f5c, \u635f\u5931 {damage} \u70b9\u6c14\u8840\u3002".format(name=actor["name"], damage=damage))
                self._hp_event(actor, hp_before, "deferred_damage", amount=damage)
                logs.extend(self._resolve_fatal_block(actor))
                if actor["hp"] <= 0:
                    return True
            elif state["type"] == "poisoned":
                damage = int(state.get("true_damage", 6))
                hp_before = int(actor["hp"])
                actor["hp"] = max(0, actor["hp"] - damage)
                logs.append("{name} \u4f53\u5185\u6bd2\u6027\u7ffb\u6d8c, \u635f\u5931 {damage} \u70b9\u771f\u5b9e\u4f24\u5bb3\u3002".format(name=actor["name"], damage=damage))
                state["duration"] -= 1
                self._hp_event(actor, hp_before, "poisoned", amount=damage)
                logs.extend(self._resolve_fatal_block(actor))
                if actor["hp"] <= 0:
                    return True

        logs.extend(self._resolve_turn_start_passives(actor))
        hp_before = int(actor["hp"])
        healed = self._resolve_regeneration(actor)
        self._hp_event(actor, hp_before, "regeneration")
        if healed > 0:
            logs.append("{name} \u8fd0\u8f6c\u5185\u606f, \u56de\u6625\u751f\u6548, \u6062\u590d\u4e86 {heal} \u70b9\u6c14\u8840\u3002".format(name=actor["name"], heal=healed))
        return False
    def _resolve_regeneration(self, actor: dict[str, Any]) -> int:
        total_heal = 0
        for passive in actor["neigong"].get("passives", []):
            if passive.get("type") != "regeneration":
                continue
            if random.random() > passive.get("chance", 1.0):
                continue
            heal = max(1, int(actor["max_hp"] * passive.get("heal_ratio", 0.0)))
            real_heal = min(heal, actor["max_hp"] - actor["hp"])
            actor["hp"] += real_heal
            total_heal += real_heal
        return total_heal

    def _resolve_passives_after_hit(self, attacker: dict[str, Any], defender: dict[str, Any], damage: int, part_key: str) -> list[str]:
        logs: list[str] = []
        for passive in attacker["neigong"].get("passives", []):
            if passive.get("type") == "vampirism":
                heal = min(int(damage * passive.get("leech_ratio", 0.0)), attacker["max_hp"] - attacker["hp"])
                if heal > 0:
                    hp_before = int(attacker["hp"])
                    attacker["hp"] += heal
                    self._hp_event(attacker, hp_before, "vampirism", fromSide=defender.get("_side"))
                    logs.append("{name} 借对手伤势反哺自身, 恢复了 {heal} 点气血。".format(name=attacker["name"], heal=heal))
        for passive in defender["neigong"].get("passives", []):
            if passive.get("type") == "thorns":
                reflect = max(1, int(damage * passive.get("reflect_ratio", 0.0)))
                hp_before = int(attacker["hp"])
                attacker["hp"] = max(0, attacker["hp"] - reflect)
                self._hp_event(attacker, hp_before, passive["type"], source=defender, amount=reflect)
                logs.append("{name} 护体劲力反震而出, 令 {target} 反受 {damage} 点伤害。".format(name=defender["name"], target=attacker["name"], damage=reflect))
                logs.extend(self._resolve_fatal_block(attacker))
            elif passive.get("type") == "part_counter":
                trigger_parts = set(passive.get("trigger_parts", []))
                if part_key not in trigger_parts:
                    continue
                reflect = max(1, int(damage * passive.get("reflect_ratio", 0.0)))
                hp_before = int(attacker["hp"])
                attacker["hp"] = max(0, attacker["hp"] - reflect)
                self._hp_event(attacker, hp_before, passive["type"], source=defender, amount=reflect)
                message = self._format_effect_message(passive.get("trigger_msg"), defender)
                if message:
                    logs.append(message)
                logs.append("{name} 借着挪移回转的劲力，当场反震 {target} {damage} 点伤害。".format(name=defender["name"], target=attacker["name"], damage=reflect))
                logs.extend(self._resolve_fatal_block(attacker))
        logs.extend(self._resolve_threshold_effects(defender))
        logs.extend(self._resolve_threshold_effects(attacker))
        return logs

    def _resolve_fatal_block(self, actor: dict[str, Any]) -> list[str]:
        if actor["hp"] > 0:
            return []
        logs: list[str] = []
        for index, passive in enumerate(actor["neigong"].get("passives", [])):
            if passive.get("type") != "fatal_block":
                continue
            key = ("neigong", index)
            limit = int(passive.get("limit", 1))
            used = int(actor["passive_usage"].get(key, 0))
            if used >= limit:
                continue
            actor["passive_usage"][key] = used + 1
            hp_before = int(actor["hp"])
            actor["hp"] = max(1, int(passive.get("survive_hp", 1)))
            self._hp_event(actor, hp_before, "fatal_block")
            message = self._format_effect_message(passive.get("trigger_msg"), actor)
            if message:
                logs.append(message)
            return logs
        return logs

    def _qinggong_effects(self, actor: dict[str, Any]) -> list[dict[str, Any]]:
        effect_data = actor["qinggong"].get("special_effect_data")
        if isinstance(effect_data, dict):
            return [effect_data]
        if isinstance(effect_data, list):
            return [effect for effect in effect_data if isinstance(effect, dict)]
        return []

    def _format_effect_message(self, template: str | None, actor: dict[str, Any]) -> str | None:
        if not template:
            return None
        return template.format(name=actor["name"], actor=actor["name"])

    def _apply_battle_start_effects(self, actor_a: dict[str, Any], actor_b: dict[str, Any]) -> list[str]:
        logs: list[str] = []
        starters: list[tuple[dict[str, Any], int, dict[str, Any]]] = []
        for actor in (actor_a, actor_b):
            for index, effect in enumerate(self._qinggong_effects(actor)):
                if effect.get("type") != "battle_start_first_strike":
                    continue
                starters.append((actor, index, effect))
        if not starters:
            return logs
        for actor, index, effect in starters:
            actor["special_usage"][("qinggong", index)] = 1
            message = self._format_effect_message(effect.get("trigger_msg"), actor)
            if message:
                logs.append(message)
        if len(starters) == 1:
            starters[0][0]["ag"] = max(starters[0][0]["ag"], 100.0)
        else:
            for actor, _index, _effect in starters:
                actor["ag"] = max(actor["ag"], 100.0)
        for actor, _index, effect in starters:
            self._passive_event(actor, effect["type"], "qinggong", gaugeValue=actor["ag"])
        return logs

    def _resolve_threshold_effects(self, actor: dict[str, Any]) -> list[str]:
        logs: list[str] = []
        hp_ratio = 0.0 if actor["max_hp"] <= 0 else actor["hp"] / actor["max_hp"]

        for index, passive in enumerate(actor["neigong"].get("passives", [])):
            trigger_hp_ratio = float(passive.get("trigger_hp_ratio", 0.0))
            if trigger_hp_ratio <= 0.0 or hp_ratio > trigger_hp_ratio:
                continue
            key = ("neigong", index)
            trigger_msg = self._format_effect_message(passive.get("trigger_msg"), actor)
            if passive.get("type") == "burst_heal":
                limit = int(passive.get("limit", 1))
                used = int(actor["passive_usage"].get(key, 0))
                if used >= limit:
                    continue
                heal = max(1, int(actor["max_hp"] * float(passive.get("heal_ratio", 0.0))))
                real_heal = min(heal, actor["max_hp"] - actor["hp"])
                actor["passive_usage"][key] = used + 1
                if trigger_msg:
                    logs.append(trigger_msg)
                if real_heal > 0:
                    hp_before = int(actor["hp"])
                    actor["hp"] += real_heal
                    self._hp_event(actor, hp_before, "burst_heal")
                    logs.append("{name} 强行稳住伤势，恢复了 {heal} 点气血。".format(name=actor["name"], heal=real_heal))
            elif passive.get("type") == "crisis_defense":
                if actor["passive_usage"].get(key):
                    continue
                actor["passive_usage"][key] = 1
                actor["states"].append({
                    "type": "crisis_defense",
                    "duration": 9999,
                    "def_bonus_ratio": float(passive.get("def_bonus_ratio", 0.0)),
                })
                self._emit(actor, "status_apply", target=actor.get("_side"), status="crisis_defense",
                           duration=9999, sourceSkill=self._skill_summary(actor, "neigong"))
                if trigger_msg:
                    logs.append(trigger_msg)

        for index, effect in enumerate(self._qinggong_effects(actor)):
            if effect.get("type") != "low_hp_extra_action":
                continue
            trigger_hp_ratio = float(effect.get("trigger_hp_ratio", 0.0))
            if trigger_hp_ratio <= 0.0 or hp_ratio > trigger_hp_ratio:
                continue
            key = ("qinggong", index)
            limit = int(effect.get("limit", 1))
            used = int(actor["special_usage"].get(key, 0))
            if used >= limit:
                continue
            actor["special_usage"][key] = used + 1
            actor["ag"] = max(actor["ag"], 1000.0)
            self._passive_event(actor, effect["type"], "qinggong", gaugeValue=actor["ag"])
            message = self._format_effect_message(effect.get("trigger_msg"), actor)
            if message:
                logs.append(message)
        return logs

    def _resolve_turn_start_passives(self, actor: dict[str, Any]) -> list[str]:
        logs: list[str] = []
        for index, passive in enumerate(actor["neigong"].get("passives", [])):
            if passive.get("type") != "stacking_defense":
                continue
            key = ("neigong", index)
            max_stacks = max(1, int(passive.get("max_stacks", 1)))
            stacks = min(max_stacks, int(actor["passive_usage"].get(key, 0)) + 1)
            previous = int(actor["passive_usage"].get(key, 0))
            if stacks == previous:
                continue
            actor["passive_usage"][key] = stacks
            self._upsert_state(
                actor,
                {
                    "type": "stacking_defense",
                    "duration": 9999,
                    "def_bonus_ratio": float(passive.get("bonus_per_turn", 0.0)) * stacks,
                },
            )
            self._emit(actor, "status_apply", target=actor.get("_side"), status="stacking_defense",
                       duration=9999, stacks=stacks, sourceSkill=self._skill_summary(actor, "neigong"))
            message = self._format_effect_message(passive.get("trigger_msg"), actor)
            if message:
                logs.append(message)
        return logs

    def _resolve_dodge_effects(self, actor: dict[str, Any]) -> list[str]:
        logs: list[str] = []
        for effect in self._qinggong_effects(actor):
            if effect.get("type") != "dodge_damage_boost":
                continue
            self._upsert_state(
                actor,
                {
                    "type": "next_attack_bonus",
                    "duration": 9999,
                    "damage_bonus_ratio": float(effect.get("damage_bonus_ratio", 0.0)),
                },
            )
            self._passive_event(actor, "dodge_damage_boost", "qinggong", status="next_attack_bonus",
                                speedAfter=self._effective_spd(actor))
            message = self._format_effect_message(effect.get("trigger_msg"), actor)
            if message:
                logs.append(message)
        return logs

    def _resolve_action_end_effects(self, actor: dict[str, Any]) -> list[str]:
        logs: list[str] = []
        for index, effect in enumerate(self._qinggong_effects(actor)):
            if effect.get("type") != "action_spd_stack":
                continue
            key = ("qinggong", index)
            max_stacks = max(1, int(effect.get("max_stacks", 1)))
            stacks = min(max_stacks, int(actor["special_usage"].get(key, 0)) + 1)
            previous = int(actor["special_usage"].get(key, 0))
            if stacks == previous:
                continue
            actor["special_usage"][key] = stacks
            self._upsert_state(
                actor,
                {
                    "type": "action_spd_stack",
                    "duration": 9999,
                    "spd_bonus_ratio": float(effect.get("bonus_per_stack", 0.0)) * stacks,
                },
            )
            self._passive_event(actor, "action_spd_stack", "qinggong", status="action_spd_stack",
                                speedAfter=self._effective_spd(actor))
            message = self._format_effect_message(effect.get("trigger_msg"), actor)
            if message:
                logs.append(message)
        return logs

    def _apply_damage_defer(self, actor: dict[str, Any], damage: int) -> tuple[int, list[str]]:
        final_damage = damage
        logs: list[str] = []
        for passive in actor["neigong"].get("passives", []):
            if passive.get("type") != "damage_defer":
                continue
            defer_ratio = float(passive.get("defer_ratio", 0.0))
            deferred = int(round(final_damage * defer_ratio))
            if deferred <= 0:
                continue
            immediate = max(1, final_damage - deferred)
            final_damage = immediate
            self._upsert_state(
                actor,
                {
                    "type": "deferred_damage",
                    "duration": 2,
                    "pending_damage": deferred,
                },
            )
            self._emit(actor, "status_apply", target=actor.get("_side"), status="deferred_damage",
                       effect="damage_defer", duration=2, amount=deferred,
                       sourceSkill=self._skill_summary(actor, "neigong"))
            message = self._format_effect_message(passive.get("trigger_msg"), actor)
            if message:
                logs.append(message)
        return final_damage, logs

    def _next_attack_damage_bonus(self, actor: dict[str, Any]) -> float:
        state = self._find_state(actor, "next_attack_bonus")
        if state is None:
            return 0.0
        return float(state.get("damage_bonus_ratio", 0.0))

    def _consume_next_attack_damage_bonus(self, actor: dict[str, Any], bonus_ratio: float) -> list[str]:
        if bonus_ratio <= 0.0:
            return []
        actor["states"] = [state for state in actor["states"] if state.get("type") != "next_attack_bonus"]
        return ["{name} 借着方才腾挪蓄下的劲势，令这一击威力陡增。".format(name=actor["name"])]

    def _apply_move_effects(self, attacker: dict[str, Any], defender: dict[str, Any], move: dict[str, Any], part_key: str) -> list[str]:
        logs: list[str] = []
        for effect in move.get("effects", []):
            chance = effect.get("chance", 0.0) + effect.get("part_bonus", {}).get(part_key, 0.0)
            if random.random() > chance:
                continue
            state = {"type": effect["type"], "duration": int(effect.get("duration", 1))}
            if effect["type"] == "weakened":
                state["atk_multiplier"] = effect.get("atk_multiplier", 0.85)
            elif effect["type"] == "slowed":
                state["spd_multiplier"] = effect.get("spd_multiplier", 0.8)
            elif effect["type"] == "bleeding":
                state["source_atk"] = self._effective_atk(attacker)
                state["atk_scale"] = effect.get("atk_scale", 0.2)
            elif effect["type"] == "armor_broken":
                state["def_multiplier"] = effect.get("def_multiplier", 0.5)
            elif effect["type"] == "disarmed":
                defender["weapon_ready"] = False
            self._upsert_state(defender, state)
            self._emit(attacker, "status_apply", target=defender.get("_side"), status=state["type"],
                       duration=state["duration"], speedAfter=self._effective_spd(defender),
                       sourceSkill=self._skill_summary(attacker, "martial_art"))
            template = STATE_TEXT.get(effect["type"])
            if template:
                logs.append(template.format(target=defender["name"]))
        return logs

    def _calculate_damage(
        self,
        attacker: dict[str, Any],
        defender: dict[str, Any],
        move: dict[str, Any],
        part_key: str,
        damage_bonus_ratio: float = 0.0,
    ) -> tuple[int, bool]:
        atk = self._effective_atk(attacker)
        defense = self._effective_def(defender)
        variance = random.uniform(0.92, 1.08)
        move_multiplier = self._move_multiplier(move)
        part_multiplier = BODY_PARTS[part_key]["damage_multiplier"]
        guard_multiplier = defender["neigong"].get("part_guard", {}).get(part_key, 1.0)
        raw_damage = (atk * move_multiplier * variance * part_multiplier * (1.0 + damage_bonus_ratio)) - (defense * 0.5)
        reduced = raw_damage * guard_multiplier
        minimum = max(1, int(atk * 0.1))
        damage = max(minimum, int(round(reduced)))
        crit = self._roll(self._effective_crt(attacker))
        if crit:
            damage *= 2
        return damage, crit

    def _move_multiplier(self, move: dict[str, Any]) -> float:
        if "damage_multiplier" in move:
            return float(move["damage_multiplier"])
        return random.uniform(move["power_min"], move["power_max"])

    def _pick_body_part(self, attacker: dict[str, Any], move: dict[str, Any]) -> tuple[str, str]:
        if move.get("target_weights"):
            labels = list(move["target_weights"].keys())
            weights = list(move["target_weights"].values())
            chosen_text = random.choices(labels, weights=weights, k=1)[0]
            part_key = TEXT_PART_TO_KEY.get(chosen_text, chosen_text if chosen_text in BODY_PARTS else "chest")
            if chosen_text in BODY_PARTS:
                chosen_text = BODY_PARTS[chosen_text]["label"]
            return part_key, chosen_text

        keys = list(BODY_PARTS.keys())
        martial_bias = attacker["martial_art"].get("target_bias", {})
        move_bias = move.get("target_bias", {})
        weights: list[float] = []
        for key in keys:
            weight = BODY_PARTS[key]["weight"]
            weight *= martial_bias.get(key, 1.0)
            weight *= move_bias.get(key, 1.0)
            weights.append(weight)
        chosen_key = random.choices(keys, weights=weights, k=1)[0]
        return chosen_key, BODY_PARTS[chosen_key]["label"]

    def _effective_atk(self, actor: dict[str, Any]) -> float:
        atk = actor["stats"]["atk"]
        for state in actor["states"]:
            if state["type"] == "weakened":
                atk *= state.get("atk_multiplier", 0.85)
        return atk

    def _effective_def(self, actor: dict[str, Any]) -> float:
        defense = actor["stats"]["def"]
        for state in actor["states"]:
            if state["type"] == "armor_broken":
                defense *= state.get("def_multiplier", 0.5)
            elif state["type"] == "crisis_defense":
                defense *= 1.0 + state.get("def_bonus_ratio", 0.0)
            elif state["type"] == "stacking_defense":
                defense *= 1.0 + state.get("def_bonus_ratio", 0.0)
        return defense

    def _effective_spd(self, actor: dict[str, Any]) -> float:
        spd = actor["stats"]["spd"]
        for state in actor["states"]:
            if state["type"] == "slowed":
                spd *= state.get("spd_multiplier", 0.8)
            elif state["type"] == "action_spd_stack":
                spd *= 1.0 + state.get("spd_bonus_ratio", 0.0)
        return max(1.0, spd)
    def _initiative_snapshot(self, actor_a: dict[str, Any], actor_b: dict[str, Any]) -> dict[str, dict[str, float]]:
        return {
            "gauge": {"a": float(actor_a["ag"]), "b": float(actor_b["ag"])},
            "speeds": {
                "a": float(self._effective_spd(actor_a)),
                "b": float(self._effective_spd(actor_b)),
            },
        }

    def _effective_crt(self, actor: dict[str, Any]) -> float:
        return actor["stats"]["crt"]

    def _effective_eva(self, actor: dict[str, Any]) -> float:
        if self._find_state(actor, "stunned") is not None:
            return 0.0
        return actor["stats"]["eva"]

    def _bleeding_damage(self, actor: dict[str, Any], state: dict[str, Any]) -> int:
        source_atk = state.get("source_atk", 10)
        defense = self._effective_def(actor)
        raw = (source_atk * state.get("atk_scale", 0.2)) - (defense * 0.25)
        return max(1, int(round(raw)))

    def _find_state(self, actor: dict[str, Any], state_type: str) -> dict[str, Any] | None:
        for state in actor["states"]:
            if state["type"] == state_type and state.get("duration", 0) > 0:
                return state
        return None

    def _upsert_state(self, actor: dict[str, Any], new_state: dict[str, Any]) -> None:
        existing = self._find_state(actor, new_state["type"])
        if existing is None:
            actor["states"].append(new_state)
            return
        if new_state["type"] == "deferred_damage":
            existing["pending_damage"] = int(existing.get("pending_damage", 0)) + int(new_state.get("pending_damage", 0))
            existing["duration"] = max(int(existing.get("duration", 0)), int(new_state.get("duration", 0)))
            return
        if new_state["type"] == "next_attack_bonus":
            existing["damage_bonus_ratio"] = float(existing.get("damage_bonus_ratio", 0.0)) + float(new_state.get("damage_bonus_ratio", 0.0))
            existing["duration"] = max(int(existing.get("duration", 0)), int(new_state.get("duration", 0)))
            return
        existing.update(new_state)
        existing["duration"] = max(existing["duration"], new_state["duration"])

    def _decrement_turn_states(self, actor: dict[str, Any]) -> None:
        for state in actor["states"]:
            if state["type"] in {"weakened", "slowed", "disarmed", "armor_broken"}:
                state["duration"] -= 1

    def _cleanup_expired(self, actor: dict[str, Any]) -> None:
        actor["states"] = [state for state in actor["states"] if state.get("duration", 0) > 0]

    def _roll(self, threshold: float) -> bool:
        return random.uniform(0.0, 100.0) < threshold
    def _emit(self, actor: dict[str, Any], kind: str, **payload: Any) -> None:
        replay = actor.get("_replay")
        if replay is None:
            return
        if replay["events"]:
            replay["time"] = max(replay["time"], replay["events"][-1]["time"] + 40)
        event = {
            "type": kind,
            "time": int(replay["time"]),
            "action": int(replay["action"]),
            "actor": actor.get("_side"),
        }
        event.update(payload)
        replay["events"].append(event)
        replay["time"] += 40

    def _hp_event(
        self,
        actor: dict[str, Any],
        before: int,
        cause: str,
        source: dict[str, Any] | None = None,
        **payload: Any,
    ) -> None:
        if before == actor["hp"]:
            return
        if cause in {"regeneration", "vampirism", "thorns", "burst_heal", "fatal_block", "part_counter", "deferred_damage"}:
            payload["sourceSkill"] = self._skill_summary(source or actor, "neigong")
        details = {
            "target": actor.get("_side"),
            "amount": abs(int(before) - int(actor["hp"])),
            "hpBefore": int(before),
            "hpAfter": int(actor["hp"]),
            "maxHp": int(actor["max_hp"]),
            "cause": cause,
            "fromSide": source.get("_side") if source else None,
        }
        details.update(payload)
        self._emit(source or actor, "heal" if actor["hp"] > before else "damage", **details)

    def _skill_summary(self, actor: dict[str, Any], category: str) -> dict[str, Any]:
        skill = actor[category]
        return {"category": category, "id": skill.get("id"), "name": skill.get("name", "")}

    def _passive_event(self, actor: dict[str, Any], effect: str, category: str, **payload: Any) -> None:
        self._emit(actor, "passive_trigger", target=actor.get("_side"), effect=effect,
                   sourceSkill=self._skill_summary(actor, category), **payload)
