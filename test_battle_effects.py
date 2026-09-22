"""Replay effect contracts; never access player databases or send messages."""

from __future__ import annotations

import json
import random
import unittest
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch

from engine import CombatEngine

ROOT = Path(__file__).parent


def config(name):
    return json.loads((ROOT / "configs" / f"{name}.json").read_text(encoding="utf-8"))


def fighter(name):
    return {
        "name": name,
        "stats": {"hp": 700, "atk": 100, "def": 60, "spd": 100, "crt": 0, "eva": 0},
        "martial_art": {
            "id": "sword_huashan",
            "name": "Test sword",
            "type": "sword",
            "moves": [
                {
                    "name": "Test strike",
                    "power_min": 1,
                    "power_max": 1,
                    "template": "{attacker} strikes {defender} {body_part}.",
                    "effects": [],
                }
            ],
        },
        "neigong": {"id": "none", "name": "None", "passives": []},
        "qinggong": {"id": "none", "name": "None"},
    }


def internal(identifier):
    return deepcopy(
        next(item for item in config("neigong") if item["id"] == identifier)
    )


def actor_pair(engine, a, b):
    actors = [engine._build_actor(a), engine._build_actor(b)]
    replay = {"events": [], "time": 0, "action": 1}
    for side, actor in zip(("a", "b"), actors):
        actor.update(_side=side, _replay=replay)
    return actors, replay["events"]


class BattleEffectTests(unittest.TestCase):
    def assert_hp_chain(self, events, initial, expected):
        hp = dict(initial)
        self.assertEqual([e["time"] for e in events], sorted(e["time"] for e in events))
        for event in events:
            if "hpAfter" not in event:
                continue
            side = event["target"]
            self.assertEqual(hp[side], event["hpBefore"])
            self.assertEqual(
                event["hpAfter"],
                max(0, event["hpBefore"] - event["amount"])
                if event["type"] == "damage"
                else event["hpBefore"] + event["amount"],
            )
            hp[side] = event["hpAfter"]
        self.assertEqual(hp, expected)

    def test_loadout_matrix_preserves_rules_rng_and_hp_chain(self):
        for seed, (art, neigong, qinggong) in enumerate(
            product(
                config("martial_arts"),
                config("neigong"),
                config("qinggong"),
            )
        ):
            a, b = fighter("A"), fighter("B")
            a.update(martial_art=art, neigong=neigong, qinggong=qinggong)
            b["neigong"] = internal("shenzhao_jing")
            original = deepcopy((a, b))
            random.seed(seed)
            expected = CombatEngine(max_actions=8).battle_with_state(a, b)
            rng = random.getstate()
            random.seed(seed)
            result = CombatEngine(max_actions=8).battle_with_events(a, b)
            self.assertEqual(
                (result["logs"], result["winner"], result["state"]), expected
            )
            self.assertEqual(random.getstate(), rng)
            self.assertEqual((a, b), original)
            self.assert_hp_chain(
                result["events"],
                {"a": 700, "b": 700},
                {
                    "a": result["state"]["fighter_a_hp"],
                    "b": result["state"]["fighter_b_hp"],
                },
            )
            self.assertEqual(
                [line for e in result["events"] for line in e.get("logs", [])],
                result["logs"],
            )

    def test_each_status_and_disarm_recovery(self):
        for status in (
            "bleeding",
            "poisoned",
            "disarmed",
            "stunned",
            "slowed",
            "weakened",
            "armor_broken",
        ):
            with self.subTest(status=status):
                a, b = fighter("A"), fighter("B")
                b["stats"]["spd"] = 90
                a["martial_art"]["moves"][0]["effects"] = [
                    {"type": status, "chance": 1, "duration": 1}
                ]
                events = CombatEngine(max_actions=2).battle_with_events(a, b)["events"]
                applied = next(e for e in events if e.get("status") == status)
                self.assertEqual(applied["sourceSkill"]["category"], "martial_art")
                ends = [e for e in events if e["type"] == "turn_end"]
                self.assertIn(status, [s["type"] for s in ends[0]["states"]["b"]])
                self.assertNotIn(status, [s["type"] for s in ends[-1]["states"]["b"]])
                if status == "disarmed":
                    self.assertFalse(ends[0]["weaponsReady"]["b"])
                    self.assertTrue(ends[-1]["weaponsReady"]["b"])
                    self.assertTrue(any(e.get("reason") == "disarmed" for e in events))
                    self.assertFalse(
                        any(e["type"] == "attack" and e["actor"] == "b" for e in events)
                    )

    def test_shenzhao_lethal_sequence_and_one_use(self):
        a, b = fighter("A"), fighter("B")
        a["stats"]["atk"] = 10000
        b["stats"]["spd"] = 1
        b["neigong"] = internal("shenzhao_jing")
        result = CombatEngine(max_actions=2).battle_with_events(a, b)
        events = result["events"]
        survival = [e for e in events if e.get("cause") == "fatal_block"]
        self.assertEqual(len(survival), 1)
        self.assertEqual((survival[0]["hpBefore"], survival[0]["hpAfter"]), (0, 1))
        self.assertEqual(survival[0]["sourceSkill"]["id"], "shenzhao_jing")
        self.assertEqual(result["state"]["fighter_b_hp"], 0)
        self.assert_hp_chain(events, {"a": 700, "b": 700}, {"a": 700, "b": 0})

    def test_shenzhao_dot_damage_precedes_survival(self):
        for status in ("bleeding", "poisoned", "deferred_damage"):
            with self.subTest(status=status):
                a, b = fighter("A"), fighter("B")
                a["neigong"] = internal("shenzhao_jing")
                engine = CombatEngine()
                (actor, _), events = actor_pair(engine, a, b)
                actor["hp"] = 1
                actor["states"] = [
                    {
                        "type": status,
                        "duration": 1,
                        "source_atk": 100,
                        "atk_scale": 0.2,
                        "pending_damage": 20,
                        "true_damage": 20,
                    }
                ]
                engine._resolve_turn_start(actor, [])
                self.assertEqual(
                    [e.get("cause") for e in events], [status, "fatal_block"]
                )
                self.assert_hp_chain(events, {"a": 1}, {"a": 1})

    def test_healing_reflection_and_crisis_events(self):
        a, b = fighter("A"), fighter("B")
        a["neigong"]["passives"] = [
            {"type": "regeneration", "heal_ratio": 0.1, "chance": 1},
            {"type": "vampirism", "leech_ratio": 0.2},
        ]
        b["neigong"]["passives"] = [
            {"type": "thorns", "reflect_ratio": 0.5},
            {"type": "burst_heal", "trigger_hp_ratio": 0.3, "heal_ratio": 0.2},
            {"type": "crisis_defense", "trigger_hp_ratio": 0.4, "def_bonus_ratio": 0.5},
        ]
        engine = CombatEngine()
        (aa, bb), events = actor_pair(engine, a, b)
        aa["hp"], bb["hp"] = 150, 100
        engine._resolve_turn_start(aa, [])
        engine._resolve_passives_after_hit(aa, bb, 100, "chest")
        self.assertTrue(
            {"regeneration", "vampirism", "thorns", "burst_heal"}
            <= {e.get("cause") for e in events}
        )
        self.assertTrue(any(e.get("status") == "crisis_defense" for e in events))
        self.assertTrue(all(e["sourceSkill"]["category"] == "neigong" for e in events))
        self.assert_hp_chain(
            events, {"a": 150, "b": 100}, {"a": aa["hp"], "b": bb["hp"]}
        )

    def test_added_internal_art_events(self):
        for identifier, part, expected in (
            ("jinzhong_zhao", "chest", "guard"),
            ("jinzhong_zhao", "abdomen", "guard"),
            ("jiayi_shengong", "chest", "damage_defer"),
            ("qiankun_danuoyi", "arm", "part_counter"),
        ):
            with self.subTest(identifier=identifier, part=part):
                a, b = fighter("A"), fighter("B")
                b["stats"]["spd"] = 90
                b["neigong"] = internal(identifier)
                engine = CombatEngine(max_actions=2)
                with patch.object(engine, "_pick_body_part", return_value=(part, part)):
                    result = engine.battle_with_events(a, b)
                matched = [
                    e
                    for e in result["events"]
                    if (e.get("effect") or e.get("cause") or e["type"]) == expected
                ]
                self.assertTrue(matched)
                self.assertEqual(matched[0]["sourceSkill"]["id"], identifier)
                if identifier == "jinzhong_zhao":
                    self.assertEqual(matched[0]["multiplier"] > 1, part == "abdomen")
                if identifier == "jiayi_shengong":
                    self.assertTrue(
                        any(
                            e.get("cause") == "deferred_damage"
                            for e in result["events"]
                        )
                    )
                if identifier == "qiankun_danuoyi":
                    self.assertEqual(
                        (
                            matched[0]["actor"],
                            matched[0]["target"],
                            matched[0]["fromSide"],
                        ),
                        ("b", "a", "b"),
                    )
        a, b = fighter("A"), fighter("B")
        a["neigong"] = internal("zixia_shengong")
        engine = CombatEngine()
        (aa, _), events = actor_pair(engine, a, b)
        for _ in range(7):
            engine._resolve_turn_start_passives(aa)
        self.assertEqual([e["stacks"] for e in events], [1, 2, 3, 4, 5])
        self.assertTrue(all(e["status"] == "stacking_defense" for e in events))

    def test_every_lightness_trigger(self):
        expected = {
            "battle_start_first_strike",
            "low_hp_extra_action",
            "action_spd_stack",
            "dodge_damage_boost",
        }
        observed = set()
        for step in config("qinggong"):
            a, b = fighter("A"), fighter("B")
            a["qinggong"] = step
            engine = CombatEngine()
            (aa, bb), events = actor_pair(engine, a, b)
            engine._apply_battle_start_effects(aa, bb)
            aa["hp"] = 1
            engine._resolve_threshold_effects(aa)
            engine._resolve_dodge_effects(aa)
            engine._resolve_action_end_effects(aa)
            observed.update(e.get("effect") for e in events)
            self.assertTrue(
                all(e["sourceSkill"]["category"] == "qinggong" for e in events)
            )
        self.assertTrue(expected <= observed)


if __name__ == "__main__":
    unittest.main()
