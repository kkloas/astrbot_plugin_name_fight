"""Replay regression tests. No repository or player database is opened."""
from __future__ import annotations

import json
import random
import unittest
from copy import deepcopy
from pathlib import Path

from engine import CombatEngine


def fighter(name: str, *, spd: int = 60, eva: int = 20, crt: int = 25) -> dict:
    return {
        "name": name,
        "stats": {"hp": 550, "atk": 85, "def": 60, "spd": spd, "crt": crt, "eva": eva},
        "martial_art": {"name": "清风剑法", "type": "sword", "moves": [{
            "name": "横江一剑", "damage_multiplier": 1.1,
            "template": "{attacker} 使出 {move_name}, 刺向 {defender} 的 {body_part}.",
            "effects": [{"type": "bleeding", "chance": .7, "duration": 3, "atk_scale": .4},
                        {"type": "stunned", "chance": .2, "duration": 1}],
        }]},
        "neigong": {"name": "长青诀", "passives": [
            {"type": "regeneration", "chance": 1, "heal_ratio": .03},
            {"type": "vampirism", "leech_ratio": .2},
            {"type": "thorns", "reflect_ratio": .12},
            {"type": "burst_heal", "trigger_hp_ratio": .3, "heal_ratio": .2, "limit": 1},
        ]},
        "qinggong": {"name": "踏雪无痕"},
    }


class BattleEventsTests(unittest.TestCase):
    def assert_consistent(self, a, b, result):
        events = result["events"]
        self.assertEqual([e["time"] for e in events], sorted(e["time"] for e in events))
        hp = {"a": a["stats"]["hp"], "b": b["stats"]["hp"]}
        for e in events:
            if e["type"] in ("damage", "heal"):
                self.assertEqual(hp[e["target"]], e["hpBefore"])
                hp[e["target"]] = e["hpAfter"]
                self.assertGreaterEqual(e["hpAfter"], 0)
                self.assertLessEqual(e["hpAfter"], e["maxHp"])
                if e["type"] == "damage":
                    self.assertEqual(e["hpAfter"], max(0, e["hpBefore"] - e["amount"]))
                else:
                    self.assertEqual(e["hpAfter"], e["hpBefore"] + e["amount"])
            if e["type"] in ("dodge", "attack"):
                self.assertNotEqual(e["actor"], e["target"])
        self.assertEqual(hp["a"], result["state"]["fighter_a_hp"])
        self.assertEqual(hp["b"], result["state"]["fighter_b_hp"])
        self.assertEqual([line for e in events for line in e.get("logs", [])], result["logs"])
        self.assertEqual(events[0]["type"], "battle_start")
        self.assertEqual(events[-1]["type"], "battle_end")

    def test_text_rng_and_hp_chain_for_100_seeds(self):
        a, b = fighter("甲", spd=95), fighter("乙", spd=43)
        original = deepcopy((a, b))
        observed = set()
        for seed in range(100):
            random.seed(seed)
            expected = CombatEngine().battle_with_state(a, b)
            rng = random.getstate()
            random.seed(seed)
            result = CombatEngine().battle_with_events(a, b)
            self.assertEqual(expected, (result["logs"], result["winner"], result["state"]))
            self.assertEqual(rng, random.getstate())
            self.assert_consistent(a, b, result)
            observed.update(e.get("cause", e["type"]) for e in result["events"])
        self.assertEqual((a, b), original)
        self.assertTrue({"strike", "dodge", "bleeding", "regeneration", "vampirism", "thorns", "burst_heal", "turn_skip"} <= observed)

    def test_real_speed_order_and_guaranteed_dodge(self):
        a, b = fighter("甲", spd=22, eva=100), fighter("乙", spd=100, eva=100)
        result = CombatEngine(max_actions=8).battle_with_events(a, b)
        turns = [e["actor"] for e in result["events"] if e["type"] == "turn_start"]
        self.assertEqual(turns[:3], ["b", "b", "b"])
        self.assertFalse(any(e["type"] == "damage" for e in result["events"]))
        self.assert_consistent(a, b, result)

    def test_crit_lethal_and_zero_action_draw(self):
        a, b = fighter("甲", spd=100, crt=100, eva=0), fighter("乙", spd=20, eva=0)
        a["stats"]["atk"] = 10000
        b["neigong"]["passives"] = []
        result = CombatEngine().battle_with_events(a, b)
        hit = next(e for e in result["events"] if e.get("cause") == "strike")
        self.assertTrue(hit["crit"])
        self.assertEqual(hit["hpAfter"], 0)
        self.assertGreater(hit["amount"], hit["hpBefore"])
        self.assert_consistent(a, b, result)
        result = CombatEngine(max_actions=0).battle_with_events(a, b)
        self.assertIsNone(result["winner"])
        self.assert_consistent(a, b, result)

    def test_real_loadouts(self):
        root = Path(__file__).parent / "configs"
        martial = json.loads((root / "martial_arts.json").read_text(encoding="utf-8"))
        neigong = json.loads((root / "neigong.json").read_text(encoding="utf-8"))
        qinggong = json.loads((root / "qinggong.json").read_text(encoding="utf-8"))
        for seed in range(100):
            random.seed(seed)
            a, b = fighter("甲"), fighter("乙", spd=73)
            for f in (a,b):
                f.update(martial_art=random.choice(martial), neigong=random.choice(neigong), qinggong=random.choice(qinggong))
            self.assert_consistent(a, b, CombatEngine().battle_with_events(a,b))

    def test_current_hp_preserves_original_max_hp(self):
        a, b = fighter("接力者"), fighter("守关者")
        a["current_hp"] = 123
        result = CombatEngine(max_actions=0).battle_with_events(a, b)
        start = result["events"][0]["fighters"]["a"]
        self.assertEqual(start["hp"], 123)
        self.assertEqual(start["maxHp"], 550)
        self.assertEqual(result["state"]["fighter_a_max_hp"], 550)
        self.assertGreaterEqual(result["state"]["fighter_a_hp"], 123)


def preview_fixture() -> dict:
    a, b = fighter("青衫客", spd=85), fighter("试炼剑客", spd=65)
    random.seed(12)
    result = CombatEngine().battle_with_events(a, b)
    def payload(f):
        return {"name": f["name"], "stats": f["stats"], "martialArt": {"name": f["martial_art"]["name"]}}
    return {**result, "attacker": payload(a), "defender": payload(b), "displayLogs": result["logs"],
            "rating": {"a": {"name": a["name"], "before": 1000, "after": 1006, "delta": 6}}}


if __name__ == "__main__":
    import sys
    if "--fixture" in sys.argv:
        out = Path(__file__).parent / "output" / "playwright" / "battle-fixture.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(preview_fixture(), ensure_ascii=False), encoding="utf-8")
        print("Generated battle playback fixture")
    else:
        unittest.main()
