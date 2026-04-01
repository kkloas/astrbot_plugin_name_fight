from __future__ import annotations

import random
from copy import deepcopy
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
]

DOMINANT_WIN_TEMPLATES = [
    "从头到尾都被压着打，【{defender}】几次想翻身都被当场按回去，这一局【{attacker}】赢得相当霸道。",
    "这一战几乎尽在【{attacker}】掌控之中，【{defender}】虽咬牙支撑，到底还是被一路推平了场面。",
    "【{attacker}】越打越顺手，【{defender}】越打越像在补作业，最终只能老老实实认下这一败。",
]

STANDARD_WIN_TEMPLATES = [
    "胜负已分！【{defender}】眼前一黑，颓然倒地，此战由【{attacker}】拿下。",
    "【{defender}】闷哼一声，再也压制不住翻涌的气血，连退数步后单膝跪地，败下阵来。",
    "尘埃落定，【{attacker}】缓缓收敛气息，只留【{defender}】倒在原地大口喘息，胜负已不言而喻。",
]

CLUTCH_WIN_TEMPLATES = [
    "这一战打到最后，双方都只剩一口硬气吊着。偏偏就是这口气，让【{attacker}】比【{defender}】多撑住了半步。",
    "两人都已逼近极限，场面惨得像谁都没捞着好处。可到最后，还是【{attacker}】险险把【{defender}】拖垮了。",
    "胜负只在一线之间，【{attacker}】自己也伤得不轻，却还是硬生生把【{defender}】先送出了局。",
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
    "head": {"label": "头部", "weight": 0.13, "damage_multiplier": 1.35},
    "chest": {"label": "心口", "weight": 0.24, "damage_multiplier": 1.2},
    "arm": {"label": "肩臂", "weight": 0.21, "damage_multiplier": 0.9},
    "abdomen": {"label": "腰腹", "weight": 0.24, "damage_multiplier": 1.0},
    "leg": {"label": "腿侧", "weight": 0.18, "damage_multiplier": 0.85},
}

TEXT_PART_TO_KEY = {
    "头部": "head",
    "面门": "head",
    "咽喉": "head",
    "头顶": "head",
    "天灵": "head",
    "胸口": "chest",
    "心口": "chest",
    "手臂": "arm",
    "手腕": "arm",
    "肩井": "arm",
    "肩臂": "arm",
    "腰腹": "abdomen",
    "小腹": "abdomen",
    "丹田": "abdomen",
    "肋下": "abdomen",
    "腰间": "abdomen",
    "后背": "abdomen",
    "腿侧": "leg",
    "膝盖": "leg",
    "全身": "chest",
}

DODGE_TEMPLATES = [
    "{defender} 脚下一错，借【{qinggong}】之势避开了这一击。",
    "{defender} 身形一晃，险之又险地让过来势，{attacker} 这一招落空。",
    "电光石火之间，{defender} 翻身后撤，将攻势尽数化去。",
]

STATE_TEXT = {
    "stunned": "{target} 眼前发黑，陷入【眩晕】。",
    "slowed": "{target} 下盘一滞，陷入【迟缓】。",
    "bleeding": "{target} 伤口崩裂，陷入【流血】。",
    "weakened": "{target} 气力受挫，陷入【虚弱】。",
    "disarmed": "{target} 手中兵刃被震飞，一时间难以再攻。",
    "armor_broken": "{target} 护体架势被破，空门大开。",
}


class CombatEngine:
    def __init__(self, max_ticks: int = 100, max_actions: int = 50) -> None:
        self.max_ticks = max_ticks
        self.max_actions = max_actions

    def battle(self, fighter_a: dict[str, Any], fighter_b: dict[str, Any]) -> list[str]:
        logs, _winner = self.battle_with_result(fighter_a, fighter_b)
        return logs

    def battle_with_result(self, fighter_a: dict[str, Any], fighter_b: dict[str, Any]) -> tuple[list[str], str | None]:
        actor_a = self._build_actor(fighter_a)
        actor_b = self._build_actor(fighter_b)
        logs: list[str] = [
            random.choice(INTRO_TEMPLATES).format(attacker=actor_a["name"], defender=actor_b["name"]),
            self._panel_text(actor_a, actor_b),
        ]

        ticks = 0
        actions = 0
        while ticks < self.max_ticks and actions < self.max_actions:
            ticks += 1
            actor_a["ag"] += self._effective_spd(actor_a)
            actor_b["ag"] += self._effective_spd(actor_b)

            ready = [actor for actor in (actor_a, actor_b) if actor["ag"] >= 100 and actor["hp"] > 0]
            if not ready:
                continue

            ready.sort(key=lambda actor: (actor["ag"], random.random()), reverse=True)
            for attacker in ready:
                defender = actor_b if attacker is actor_a else actor_a
                if attacker["hp"] <= 0 or defender["hp"] <= 0 or attacker["ag"] < 100:
                    continue
                attacker["ag"] -= 100
                actions += 1
                self._take_turn(attacker, defender, logs, actions)
                self._decrement_turn_states(attacker)
                self._cleanup_expired(attacker)
                self._cleanup_expired(defender)
                if defender["hp"] <= 0 or attacker["hp"] <= 0:
                    winner = attacker if attacker["hp"] > 0 else defender
                    loser = defender if winner is attacker else attacker
                    logs.append(self._pick_outro_text(winner, loser, actions, judged=False))
                    return logs, winner["name"]
                if actions >= self.max_actions:
                    break

        hp_ratio_a = actor_a["hp"] / actor_a["max_hp"]
        hp_ratio_b = actor_b["hp"] / actor_b["max_hp"]
        if abs(hp_ratio_a - hp_ratio_b) < 0.01:
            logs.append(random.choice(DRAW_TEMPLATES))
            return logs, None

        winner, loser = (actor_a, actor_b) if hp_ratio_a > hp_ratio_b else (actor_b, actor_a)
        logs.append(self._pick_outro_text(winner, loser, actions, judged=True))
        return logs, winner["name"]

    def _build_actor(self, fighter: dict[str, Any]) -> dict[str, Any]:
        stats = deepcopy(fighter["stats"])
        return {
            "name": fighter["name"],
            "stats": stats,
            "hp": stats["hp"],
            "max_hp": stats["hp"],
            "ag": 0.0,
            "martial_art": fighter["martial_art"],
            "neigong": fighter["neigong"],
            "qinggong": fighter["qinggong"],
            "states": [],
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
            return
        if not attacker["weapon_ready"]:
            attacker["weapon_ready"] = True
            logs.append("{name} 兵刃脱手，只得先稳住架势并拾回武器，这一回合未能出手。".format(name=attacker["name"]))
            return

        move = random.choice(attacker["martial_art"]["moves"])
        if self._roll(self._effective_eva(defender)):
            logs.append(
                random.choice(DODGE_TEMPLATES).format(
                    attacker=attacker["name"],
                    defender=defender["name"],
                    qinggong=defender["qinggong"]["name"],
                )
            )
            return

        part_key, body_part_text = self._pick_body_part(attacker, move)
        attack_text = self._render_move_text(attacker, defender, move, body_part_text)
        tagged_attack_text = self._tagged_attack_text(attack_text, attacker["name"], defender["name"], body_part_text)
        damage, crit = self._calculate_damage(attacker, defender, move, part_key)
        defender["hp"] = max(0, defender["hp"] - damage)
        logs.append(self._hit_reaction(defender, part_key))
        logs.append(
            "{text} 造成 {damage} 点伤害，{defender} 剩余 {hp}/{max_hp}。".format(
                text=tagged_attack_text,
                damage=damage,
                defender=defender["name"],
                hp=defender["hp"],
                max_hp=defender["max_hp"],
            )
        )
        if crit:
            logs.append(self._crit_text(attacker, defender))
        logs.extend(self._resolve_passives_after_hit(attacker, defender, damage))
        logs.extend(self._apply_move_effects(attacker, defender, move, part_key))

    def _tag_name(self, name: str) -> str:
        return f"[{name}]"

    def _tag_part(self, body_part_text: str) -> str:
        return f"[{body_part_text}]"

    def _tagged_attack_text(self, text: str, attacker_name: str, defender_name: str, body_part_text: str) -> str:
        tagged = text.replace(attacker_name, self._tag_name(attacker_name))
        tagged = tagged.replace(defender_name, self._tag_name(defender_name))
        tagged = tagged.replace(body_part_text, self._tag_part(body_part_text))
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
            logs.append("{name} 眼前一阵发黑，气机紊乱，只能白白错过这一轮出手。".format(name=actor["name"]))
            return True

        for state in list(actor["states"]):
            if state["type"] == "bleeding":
                damage = self._bleeding_damage(actor, state)
                actor["hp"] = max(0, actor["hp"] - damage)
                logs.append("{name} 伤口迸裂，流血发作，损失 {damage} 点气血。".format(name=actor["name"], damage=damage))
                state["duration"] -= 1
                if actor["hp"] <= 0:
                    return True
            elif state["type"] == "poisoned":
                damage = int(state.get("true_damage", 6))
                actor["hp"] = max(0, actor["hp"] - damage)
                logs.append("{name} 体内毒性翻涌，损失 {damage} 点真伤。".format(name=actor["name"], damage=damage))
                state["duration"] -= 1
                if actor["hp"] <= 0:
                    return True

        healed = self._resolve_regeneration(actor)
        if healed > 0:
            logs.append("{name} 运转内息，回春生效，恢复了 {heal} 点气血。".format(name=actor["name"], heal=healed))
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

    def _resolve_passives_after_hit(self, attacker: dict[str, Any], defender: dict[str, Any], damage: int) -> list[str]:
        logs: list[str] = []
        for passive in attacker["neigong"].get("passives", []):
            if passive.get("type") == "vampirism":
                heal = min(int(damage * passive.get("leech_ratio", 0.0)), attacker["max_hp"] - attacker["hp"])
                if heal > 0:
                    attacker["hp"] += heal
                    logs.append("{name} 借对手伤势反哺自身，恢复了 {heal} 点气血。".format(name=attacker["name"], heal=heal))
        for passive in defender["neigong"].get("passives", []):
            if passive.get("type") == "thorns":
                reflect = max(1, int(damage * passive.get("reflect_ratio", 0.0)))
                attacker["hp"] = max(0, attacker["hp"] - reflect)
                logs.append("{name} 护体劲反震而出，令 {target} 反受 {damage} 点伤害。".format(name=defender["name"], target=attacker["name"], damage=reflect))
        return logs

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
            template = STATE_TEXT.get(effect["type"])
            if template:
                logs.append(template.format(target=defender["name"]))
        return logs

    def _calculate_damage(self, attacker: dict[str, Any], defender: dict[str, Any], move: dict[str, Any], part_key: str) -> tuple[int, bool]:
        atk = self._effective_atk(attacker)
        defense = self._effective_def(defender)
        variance = random.uniform(0.92, 1.08)
        move_multiplier = self._move_multiplier(move)
        part_multiplier = BODY_PARTS[part_key]["damage_multiplier"]
        guard_multiplier = defender["neigong"].get("part_guard", {}).get(part_key, 1.0)
        raw_damage = (atk * move_multiplier * variance * part_multiplier) - (defense * 0.5)
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
        return defense

    def _effective_spd(self, actor: dict[str, Any]) -> float:
        spd = actor["stats"]["spd"]
        for state in actor["states"]:
            if state["type"] == "slowed":
                spd *= state.get("spd_multiplier", 0.8)
        return max(1.0, spd)

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
