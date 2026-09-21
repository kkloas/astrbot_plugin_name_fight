"""Visual event contracts and deterministic fixtures, without player data."""
import json
import random
import unittest
from copy import deepcopy
from itertools import product
from pathlib import Path

from engine import CombatEngine
import test_battle_events as replay_tests
from test_battle_events import fighter

ROOT = Path(__file__).parent


def config(name):
    return json.loads((ROOT / "configs" / f"{name}.json").read_text(encoding="utf-8"))


def payload(f):
    return {"name": f["name"], "stats": f["stats"], **{
        key: {k: f[source].get(k) for k in ("id", "name", "type")}
        for key, source in (("martialArt", "martial_art"), ("neigong", "neigong"), ("qinggong", "qinggong"))
    }}


def fixture(a, b, seed=14, actions=8):
    random.seed(seed)
    result = CombatEngine(max_actions=actions).battle_with_events(a, b)
    return {**result, "attacker": payload(a), "defender": payload(b), "rating": {}, "displayLogs": result["logs"]}


def move_fixtures():
    result = []
    for art in config("martial_arts"):
        for index, move in enumerate(art["moves"]):
            a, b = fighter(art["name"], spd=100, crt=0, eva=0), fighter("试炼对手", spd=1, crt=0, eva=0)
            a["martial_art"] = deepcopy(art)
            a["martial_art"]["moves"] = [deepcopy(move)]
            a["neigong"] = deepcopy(config("neigong")[0])
            a["qinggong"] = deepcopy(config("qinggong")[index % 7])
            b["neigong"] = deepcopy(config("neigong")[1])
            b["martial_art"] = deepcopy(config("martial_arts")[1])
            b["qinggong"] = deepcopy(config("qinggong")[4])
            data = fixture(a, b, actions=1)
            result.append({"id": f"{art['id']}-{index}", "battle": data})
    return result


def effect_fixtures():
    wanted = {"regeneration", "vampirism", "thorns", "burst_heal", "crisis_defense",
              "battle_start_first_strike", "low_hp_extra_action", "disarmed", "stunned",
              "slowed", "weakened", "armor_broken", "bleeding"}
    results = {}
    arts, internals, steps = config("martial_arts"), config("neigong"), config("qinggong")
    for seed in range(300):
        a, b = fighter("试招甲", spd=75), fighter("试招乙", spd=65)
        for offset, f in enumerate((a, b)):
            f.update(martial_art=deepcopy(arts[(seed+offset) % len(arts)]),
                     neigong=deepcopy(internals[(seed+offset) % len(internals)]),
                     qinggong=deepcopy(steps[(seed*3+offset) % len(steps)]))
        data = fixture(a, b, seed=seed, actions=40)
        for event in data["events"]:
            effect = event.get("effect") or event.get("cause") or event.get("status")
            if effect in wanted and effect not in results:
                results[effect] = {"id": effect, "time": event["time"], "battle": data}
        if wanted <= results.keys():
            return list(results.values())
    raise AssertionError(f"Uncovered effects: {wanted - results.keys()}")


class VisualContractTests(unittest.TestCase):
    def test_every_move_has_identity_and_one_real_strike(self):
        fixtures = move_fixtures()
        self.assertEqual(len(fixtures), sum(len(a["moves"]) for a in config("martial_arts")))
        for item in fixtures:
            result = item["battle"]
            attack = next(e for e in result["events"] if e["type"] == "attack")
            self.assertEqual(attack["martialArtId"], result["attacker"]["martialArt"]["id"])
            self.assertEqual(attack["weaponType"], result["attacker"]["martialArt"]["type"])
            self.assertEqual(sum(e.get("cause") == "strike" for e in result["events"]), 1)

    def test_all_loadout_combinations_keep_text_rules(self):
        # Full 11 x 7 x 7 loadout product; also detects accidental RNG in event emission.
        for seed, (art, internal, step) in enumerate(product(config("martial_arts"), config("neigong"), config("qinggong"))):
            a, b = fighter("甲"), fighter("乙")
            a.update(martial_art=art, neigong=internal, qinggong=step)
            random.seed(seed)
            expected = CombatEngine().battle_with_state(a,b)
            rng = random.getstate()
            random.seed(seed)
            result = CombatEngine().battle_with_events(a,b)
            self.assertEqual(expected, (result["logs"],result["winner"],result["state"]))
            self.assertEqual(rng, random.getstate())
            replay_tests.BattleEventsTests().assert_consistent(a,b,result)

    def test_special_triggers_and_weapon_snapshots(self):
        for item in effect_fixtures():
            events = item["battle"]["events"]
            triggers = [e for e in events if e.get("effect") == item["id"]]
            if item["id"] in {"battle_start_first_strike", "low_hp_extra_action"}:
                self.assertTrue(triggers)
                self.assertEqual(len(triggers), len({e["actor"] for e in triggers}))
                self.assertTrue(all(e["sourceSkill"]["category"] == "qinggong" for e in triggers))
            if item["id"] == "disarmed":
                disarm = next(e for e in events if e.get("status") == "disarmed")
                end = next(e for e in events if e["type"] == "turn_end" and e["time"] > disarm["time"])
                self.assertFalse(end["weaponsReady"][disarm["target"]])
                pickup = next((e for e in events if e["type"] == "turn_skip" and e.get("reason") == "disarmed" and e["actor"] == disarm["target"]), None)
                if pickup:
                    end = next(e for e in events if e["type"] == "turn_end" and e["action"] == pickup["action"])
                    self.assertTrue(end["weaponsReady"][pickup["actor"]])


if __name__ == "__main__":
    import sys
    if "--fixtures" in sys.argv:
        out = ROOT / "output" / "playwright"
        out.mkdir(parents=True, exist_ok=True)
        data = {"moves": move_fixtures(), "effects": effect_fixtures()}
        (out / "martial-fixtures.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print(f"Generated {len(data['moves'])} moves and {len(data['effects'])} effects")
    else:
        unittest.main()
