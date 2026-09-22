"""Two additive martial arts: acquisition, real effects and replay contracts."""
import json
import random
import subprocess
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from database import FighterRepository
from engine import CombatEngine
from test_battle_events import BattleEventsTests, fighter

ROOT = Path(__file__).parent
NEW_IDS = {"sword_danyu", "blade_jingchao"}


class NewMartialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arts = json.loads((ROOT / "configs/martial_arts.json").read_text(encoding="utf-8"))
        cls.new = [art for art in cls.arts if art["id"] in NEW_IDS]
        cls.repo = FighterRepository.__new__(FighterRepository)
        cls.repo.martial_arts = cls.arts
        for key in ("neigong", "qinggong"):
            setattr(cls.repo, key, json.loads((ROOT / "configs" / f"{key}.json").read_text(encoding="utf-8")))

    def test_config_matches_release_baseline(self):
        previous = json.loads(subprocess.check_output(
            ["git", "show", "2229cda:configs/martial_arts.json"], cwd=ROOT).decode("utf-8"))
        self.assertEqual(self.arts, previous)
        self.assertEqual(len(self.arts), 18)
        self.assertEqual(len({a["id"] for a in self.arts}), len(self.arts))

    def test_generation_and_reroll_pools(self):
        seen = set()
        for i in range(500):
            created = self.repo._build_generated_fighter(f"new_art_fixture_{i}")
            seen.add(created["martial_art_id"])
        self.assertTrue(NEW_IDS <= seen)
        for art in self.new:
            old = next(a for a in self.arts if a["type"] == art["type"] and a["id"] not in NEW_IDS)
            for mode in ("basic", "choice", "type"):
                self.assertIn(art, self.repo._martial_pool_by_mode(old, mode))
                self.assertNotIn(art, self.repo._martial_pool_by_mode(art, mode))

    def test_all_moves_one_hit_and_text_parity(self):
        checker = BattleEventsTests()
        for art in self.new:
            self.assertEqual(len(art["moves"]), 8)
            for move in art["moves"]:
                a, b = fighter("A", spd=100, eva=0, crt=0), fighter("B", spd=1, eva=0, crt=0)
                a["martial_art"] = {**deepcopy(art), "moves": [deepcopy(move)]}
                for f in (a, b):
                    f["neigong"] = {"name": "neutral", "passives": []}
                random.seed(53)
                text = CombatEngine(max_actions=1).battle_with_state(a, b)
                random.seed(53)
                result = CombatEngine(max_actions=1).battle_with_events(a, b)
                self.assertEqual(text, (result["logs"], result["winner"], result["state"]))
                self.assertEqual(sum(e.get("cause") == "strike" for e in result["events"]), 1)
                self.assertTrue(any(move["name"] in line for line in result["logs"]))
                self.assertFalse(any("{body_part}" in line for line in result["logs"]))
                checker.assert_consistent(a, b, result)

    def test_status_is_probabilistic_and_has_correct_magnitude(self):
        for art, status, multiplier, value in [
            (self.new[0], "slowed", "spd_multiplier", .85),
            (self.new[1], "armor_broken", "def_multiplier", .8),
        ]:
            move = next(m for m in art["moves"] if m["effects"])
            self.assertEqual(move["effects"], [{"type": status, "chance": .25, "duration": 2, multiplier: value}])
            a = {"stats": {"atk": 80}, "states": [], "name": "A", "martial_art": art}
            b = {"stats": {"spd": 60}, "states": [], "name": "B"}
            with patch("engine.random.random", return_value=.5):
                CombatEngine()._apply_move_effects(a, b, move, "chest")
            self.assertEqual(b["states"], [])
            with patch("engine.random.random", return_value=.1):
                CombatEngine()._apply_move_effects(a, b, move, "chest")
            self.assertEqual(b["states"][0][multiplier], value)
            self.assertEqual(b["states"][0]["duration"], 2)


if __name__ == "__main__":
    unittest.main()
