"""Action-gauge snapshots must describe existing ticks, not a new scheduler."""
import json
import random
import unittest
from copy import deepcopy
from pathlib import Path

from engine import CombatEngine
from test_battle_events import fighter
from test_battle_visuals import config, effect_fixtures, fixture


class ActionGaugeTests(unittest.TestCase):
    def assert_gauge_chain(self, result):
        gauge = {"a": 0.0, "b": 0.0}
        charge_end = 0
        for event in result["events"]:
            kind = event["type"]
            if kind == "gauge_charge":
                self.assertLess(event["time"], event["endTime"])
                self.assertGreaterEqual(event["ticksAdvanced"], 1)
                charge_end = event["endTime"]
                for side in ("a", "b"):
                    self.assertAlmostEqual(event["gaugeFrom"][side], gauge[side])
                    self.assertAlmostEqual(event["gauge"][side], gauge[side] + event["speeds"][side] * event["ticksAdvanced"])
            if kind == "turn_start":
                self.assertGreaterEqual(event["time"], charge_end)
                self.assertGreaterEqual(event["gaugeBefore"][event["actor"]], 100)
                for side in ("a", "b"):
                    self.assertAlmostEqual(event["gaugeBefore"][side], gauge[side])
                    self.assertAlmostEqual(event["gauge"][side], gauge[side] - (100 if side == event["actor"] else 0))
            if kind == "turn_end":
                for side in ("a", "b"):
                    self.assertAlmostEqual(event["gauge"][side], gauge[side])
            if "gauge" in event:
                gauge.update(event["gauge"])
            if "gaugeValue" in event:
                gauge[event["target"]] = event["gaugeValue"]

    def test_real_tick_and_spending_chain(self):
        for seed in range(100):
            a, b = fighter("甲", spd=23), fighter("乙", spd=127)
            for offset, f in enumerate((a, b)):
                f.update(martial_art=config("martial_arts")[(seed+offset) % 11],
                         neigong=config("neigong")[(seed+offset) % 7],
                         qinggong=config("qinggong")[(seed+offset) % 7])
            random.seed(seed)
            self.assert_gauge_chain(CombatEngine().battle_with_events(a, b))

    def test_simultaneous_ready_does_not_add_a_tick(self):
        a, b = fighter("甲", spd=100, eva=100), fighter("乙", spd=100, eva=100)
        result = CombatEngine(max_actions=2).battle_with_events(a, b)
        self.assert_gauge_chain(result)
        charges = [e for e in result["events"] if e["type"] == "gauge_charge"]
        turns = [e for e in result["events"] if e["type"] == "turn_start"]
        self.assertEqual(len(charges), 1)
        self.assertEqual(turns[0]["gaugeBefore"], {"a": 100, "b": 100})
        self.assertEqual(turns[1]["gauge"], {"a": 0, "b": 0})

    def test_special_boosts_and_speed_changes_are_explicit(self):
        for item in effect_fixtures():
            self.assert_gauge_chain(item["battle"])
            for event in item["battle"]["events"]:
                if event.get("effect") == "battle_start_first_strike":
                    self.assertEqual(event["gaugeValue"], 100)
                if event.get("effect") == "low_hp_extra_action":
                    self.assertGreaterEqual(event["gaugeValue"], 1000)
                if event.get("status") == "slowed":
                    self.assertGreater(event["speedAfter"], 0)
                    self.assertLess(event["speedAfter"], 75)

    def test_victory_matches_existing_outro_categories(self):
        cases = [(3, .8, False, "quick"), (8, .8, False, "dominant"),
                 (8, .1, False, "clutch"), (8, .4, False, "standard"), (8, .8, True, "judged")]
        for actions, ratio, judged, expected in cases:
            events = []
            winner = {"name": "甲", "hp": int(ratio*100), "max_hp": 100, "_side": "a",
                      "_replay": {"time": 0, "action": actions, "events": events}}
            CombatEngine()._pick_outro_text(winner, {"name": "乙"}, actions, judged)
            self.assertEqual(events[-1]["victoryKind"], expected)

    def test_victory_variant_is_stable_and_varied_without_extra_rng(self):
        variants = set()
        for seed in range(20):
            a, b = fighter("甲", spd=100), fighter("乙", spd=10)
            a["stats"]["atk"] = 1000
            random.seed(seed)
            plain = CombatEngine().battle_with_state(a, b)
            rng = random.getstate()
            random.seed(seed)
            replay = CombatEngine().battle_with_events(a, b)
            self.assertEqual(rng, random.getstate())
            self.assertEqual(plain, (replay["logs"], replay["winner"], replay["state"]))
            victory = next(e for e in replay["events"] if e["type"] == "victory_start")
            variants.add(victory["victoryVariant"])
            self.assertEqual(replay["events"][-1]["time"]-victory["time"], 1800)
        self.assertEqual(variants, {0, 1, 2})


def skill_fixtures():
    results = []
    effects = {"evergreen_breath": "regeneration", "iron_wall_art": "thorns",
               "blood_moon_skill": "vampirism", "golden_wind_record": "vampirism",
               "hunyuan_qigong": "thorns", "biyun_xinfa": "burst_heal", "xiantian_qigong": "crisis_defense"}
    for internal in config("neigong"):
        for seed in range(60):
            a, b = fighter(internal["name"], spd=75, eva=0), fighter("试招对手", spd=65, eva=0)
            a.update(neigong=deepcopy(internal), qinggong=deepcopy(config("qinggong")[0]))
            b["neigong"] = {"name": "试招内功", "passives": []}
            data = fixture(a, b, seed=seed, actions=24)
            event = next((e for e in data["events"] if e.get("sourceSkill", {}).get("id") == internal["id"] and
                          (e.get("cause") or e.get("status")) == effects[internal["id"]]), None)
            if event:
                results.append({"id": internal["id"], "time": event["time"], "battle": data})
                break
        else:
            raise AssertionError(f"Missing internal skill: {internal['id']}")
    for step in config("qinggong"):
        a, b = fighter(step["name"], spd=30, eva=100), fighter("试招对手", spd=100, eva=100)
        a.update(qinggong=deepcopy(step), neigong={"name": "试招内功", "passives": []})
        b["neigong"] = {"name": "试招内功", "passives": []}
        data = fixture(a, b, actions=6)
        event = next(e for e in data["events"] if e["type"] == "dodge" and e["target"] == "a")
        results.append({"id": step["id"], "time": event["time"], "battle": data})
    return results


if __name__ == "__main__":
    import sys
    if "--fixtures" in sys.argv:
        out = Path(__file__).parent / "output" / "playwright" / "skill-fixtures.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        data = skill_fixtures()
        out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print(f"Generated {len(data)} internal/lightness skill fixtures")
    else:
        unittest.main()
