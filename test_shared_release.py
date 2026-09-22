"""Shared release contracts, using temporary databases and recorded events only."""
import json
import ast
import random
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from database import FighterRepository
from engine import CombatEngine

ROOT = Path(__file__).parent


class ClosingRepository(FighterRepository):
    @contextmanager
    def _connect(self):
        connection = super()._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()


class SharedReleaseTests(unittest.TestCase):
    def test_bot_repository_calls_exist(self):
        tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8-sig"))
        called = {
            node.func.attr for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "repo"
        }
        self.assertTrue(called)
        self.assertEqual([name for name in sorted(called) if not callable(getattr(FighterRepository, name, None))], [])

    def test_all_three_configs_match_main_baseline(self):
        for name in ("martial_arts", "neigong", "qinggong"):
            expected = json.loads(subprocess.check_output(
                ["git", "show", f"2229cda:configs/{name}.json"], cwd=ROOT))
            actual = json.loads((ROOT / "configs" / f"{name}.json").read_text(encoding="utf-8"))
            self.assertEqual(actual, expected, name)

    def test_new_loadouts_are_generated_without_touching_player_data(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = ClosingRepository(Path(directory) / "test.db")
            seen = {key: set() for key in ("martial_art", "neigong", "qinggong")}
            for i in range(1500):
                fighter = repo.generate_preview_fighter(f"compatibility-{i}")
                for key in seen:
                    seen[key].add(fighter[key]["id"])
            for key, entries in (("martial_art", repo.martial_arts), ("neigong", repo.neigong), ("qinggong", repo.qinggong)):
                self.assertEqual(seen[key], {item["id"] for item in entries})

    def test_text_and_replay_share_rules(self):
        repo = FighterRepository.__new__(FighterRepository)
        for key in ("martial_arts", "neigong", "qinggong"):
            setattr(repo, key, json.loads((ROOT / "configs" / f"{key}.json").read_text(encoding="utf-8")))
        for i in range(30):
            a, b = (repo._build_generated_fighter(f"contract-{i}-{side}") for side in ("a", "b"))
            for fighter in (a, b):
                fighter["martial_art"] = next(x for x in repo.martial_arts if x["id"] == fighter["martial_art_id"])
                fighter["neigong"] = next(x for x in repo.neigong if x["id"] == fighter["neigong_id"])
                fighter["qinggong"] = next(x for x in repo.qinggong if x["id"] == fighter["qinggong_id"])
            random.seed(i)
            text = CombatEngine().battle_with_state(a, b)
            state = random.getstate()
            random.seed(i)
            replay = CombatEngine().battle_with_events(a, b)
            self.assertEqual(text, (replay["logs"], replay["winner"], replay["state"]))
            self.assertEqual(state, random.getstate())


if __name__ == "__main__":
    unittest.main()
