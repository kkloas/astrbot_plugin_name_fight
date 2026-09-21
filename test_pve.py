from __future__ import annotations

import itertools
import random
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from database import FighterRepository
from engine import CombatEngine
from pve import PveService


class ClosingRepository(FighterRepository):
    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()


class ScriptedEngine:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def battle_with_events(self, fighter_a, fighter_b):
        self.calls.append((deepcopy(fighter_a), deepcopy(fighter_b)))
        outcome = self.outcomes.pop(0)
        a_hp = int(fighter_a.get("current_hp", fighter_a["stats"]["hp"]))
        b_hp = int(fighter_b.get("current_hp", fighter_b["stats"]["hp"]))
        fighter_a["temporary_status"] = "bleeding"
        fighter_b["temporary_status"] = "stunned"
        if outcome == "a":
            a_after, b_after, winner = max(1, a_hp - 10), 0, fighter_a["name"]
        elif outcome == "b":
            a_after, b_after, winner = 0, max(1, b_hp - 10), fighter_b["name"]
        else:
            a_after, b_after, winner = 0, 0, None
        return {
            "winner": winner,
            "state": {"fighter_a_hp": a_after, "fighter_b_hp": b_after},
            "events": [{"type": "battle_end", "time": 1}],
            "logs": [],
        }


class PveRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="name-fight-pve-")
        self.repo = ClosingRepository(Path(self.temp.name) / "fighters.db")
        self.user_id = "pve-user"

    def tearDown(self):
        self.temp.cleanup()

    def create_team(self):
        for name in ("历练甲", "历练乙", "历练丙"):
            self.repo.create_fighter_for_user(self.user_id, name)
        return self.repo.set_pve_team(self.user_id, [1, 2, 3], now=1000)

    def test_energy_recovery_and_team_validation(self):
        profile = self.repo.get_pve_profile(self.user_id, now=1000)
        self.assertEqual(profile["energy"], 100)
        with self.assertRaisesRegex(ValueError, "三个不重复"):
            self.repo.set_pve_team(self.user_id, [1, 1, 2], now=1000)
        self.create_team()
        with self.assertRaisesRegex(ValueError, "空位"):
            self.repo.set_pve_team(self.user_id, [1, 2, 4], now=1000)
        loss = self.repo.settle_pve_attempt(
            self.user_id, "1-1", 10, False, 0,
            {"points": 20, "items": []}, {"points": 5, "items": []}, now=1000,
        )
        self.assertEqual(loss["profile"]["energy"], 90)
        recovered = self.repo.get_pve_profile(self.user_id, now=1360)
        self.assertEqual(recovered["energy"], 91)
        capped = self.repo.get_pve_profile(self.user_id, now=100000)
        self.assertEqual(capped["energy"], 100)

    def test_energy_item_is_atomic_caps_at_maximum_and_preserves_recovery_progress(self):
        self.repo.get_pve_profile(self.user_id, now=1000)
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE pve_profiles SET energy = 50, energy_updated_at = 1000 WHERE user_id = ?",
                (self.user_id,),
            )
            connection.execute(
                "INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, 'energy_pill', 2)",
                (self.user_id,),
            )
            connection.commit()

        first = self.repo.use_pve_energy_item(self.user_id, "energy_pill", now=1100)
        self.assertEqual(first["restored"], 30)
        self.assertEqual(first["profile"]["energy"], 80)
        self.assertEqual(first["remaining"], 1)
        self.assertEqual(self.repo.get_pve_profile(self.user_id, now=1360)["energy"], 81)

        second = self.repo.use_pve_energy_item(self.user_id, "energy_pill", now=1360)
        self.assertEqual(second["restored"], 19)
        self.assertEqual(second["profile"]["energy"], 100)
        self.assertEqual(second["remaining"], 0)
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE user_items SET quantity = 1 WHERE user_id = ? AND item_id = 'energy_pill'",
                (self.user_id,),
            )
            connection.commit()
        with self.assertRaisesRegex(ValueError, "体力已满"):
            self.repo.use_pve_energy_item(self.user_id, "energy_pill", now=1361)
        bag = {item["item_id"]: item for item in self.repo.get_user_items(self.user_id)}
        self.assertEqual(bag["energy_pill"]["quantity"], 1)

    def test_first_clear_best_stars_and_chapter_reward_are_unique(self):
        self.create_team()
        first = self.repo.settle_pve_attempt(
            self.user_id, "1-1", 10, True, 1,
            {"points": 20, "items": [{"item_id": "star_exp_pill_s", "quantity": 1}]},
            {"points": 5, "items": []}, now=1000,
        )
        self.assertTrue(first["first_clear"])
        self.assertEqual(first["reward"]["points"], 20)
        second = self.repo.settle_pve_attempt(
            self.user_id, "1-1", 10, True, 3,
            {"points": 20, "items": []}, {"points": 5, "items": []}, now=1001,
        )
        self.assertFalse(second["first_clear"])
        self.assertEqual(second["best_stars"], 3)
        self.assertEqual(second["clear_count"], 2)
        self.assertEqual(second["reward"]["points"], 5)
        claimed = self.repo.claim_pve_chapter_reward(
            self.user_id, "chapter_1", ["1-1"], 3,
            {"points": 50, "items": [{"item_id": "martial_token_basic", "quantity": 1}]}, now=1002,
        )
        self.assertEqual(claimed["reward"]["points"], 50)
        with self.assertRaisesRegex(ValueError, "已经领取"):
            self.repo.claim_pve_chapter_reward(
                self.user_id, "chapter_1", ["1-1"], 3,
                {"points": 50, "items": []}, now=1003,
            )

    def test_invalid_reward_rolls_back_energy_and_progress(self):
        self.create_team()
        with self.assertRaisesRegex(ValueError, "未知的 PVE 奖励道具"):
            self.repo.settle_pve_attempt(
                self.user_id, "1-1", 10, True, 3,
                {"points": 20, "items": [{"item_id": "missing_item", "quantity": 1}]},
                {"points": 5, "items": []}, now=1000,
            )
        self.assertEqual(self.repo.get_pve_profile(self.user_id, now=1000)["energy"], 100)
        self.assertEqual(self.repo.get_pve_stage_progress(self.user_id), [])


class PveServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="name-fight-pve-service-")
        self.repo = ClosingRepository(Path(self.temp.name) / "fighters.db")
        self.service = PveService(self.repo, CombatEngine())
        self.user_id = "web-local-user"
        for name in ("青锋客", "抱月人", "听雪生"):
            self.repo.create_fighter_for_user(self.user_id, name)
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE fighters SET hp = 900, atk = 180, def = 150, spd = 120, crt = 50, eva = 45"
            )
            connection.commit()
        self.service.set_team(self.user_id, [1, 2, 3])

    def tearDown(self):
        self.temp.cleanup()

    def test_config_unlocks_and_npcs_are_not_persisted(self):
        state = self.service.get_state(self.user_id)
        stages = [stage for chapter in state["chapters"] for stage in chapter["stages"]]
        self.assertEqual(len(stages), 18)
        self.assertTrue(stages[0]["unlocked"])
        self.assertFalse(stages[1]["unlocked"])
        with self.assertRaisesRegex(ValueError, "尚未解锁"):
            self.service.challenge(self.user_id, "1-2")
        self.assertEqual(self.service.get_state(self.user_id)["profile"]["energy"], 100)
        before_names = {fighter["name"] for fighter in self.repo.get_user_fighters(self.user_id)}
        with patch("random.random", return_value=0.99):
            result = self.service.challenge(self.user_id, "1-1")
        self.assertTrue(result["victory"])
        self.assertTrue(result["firstClear"])
        self.assertEqual(result["profile"]["energy"], 90)
        self.assertGreaterEqual(len(result["duels"]), 3)
        after = self.service.get_state(self.user_id)
        self.assertTrue(after["chapters"][0]["stages"][1]["unlocked"])
        with self.repo._connect() as connection:
            persisted_names = {str(row["name"]) for row in connection.execute("SELECT name FROM fighters").fetchall()}
            score_count = int(connection.execute("SELECT COUNT(*) FROM fighter_scores").fetchone()[0])
        self.assertEqual(persisted_names, before_names)
        self.assertEqual(score_count, 0)
        with self.repo._connect() as connection:
            connection.execute("UPDATE pve_profiles SET energy = 0 WHERE user_id = ?", (self.user_id,))
            connection.commit()
        with self.assertRaisesRegex(ValueError, "体力不足"):
            self.service.challenge(self.user_id, "1-2")

    def test_relay_carries_hp_resets_temporary_state_and_keeps_max_hp(self):
        scripted = ScriptedEngine(("a", "a", "a"))
        self.service.engine = scripted
        stage = self.service.stage_map["1-1"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        result = self.service._team_battle(team, enemies, stage)
        maximum_hp = int(team[0]["stats"]["hp"])
        self.assertTrue(result["victory"])
        self.assertEqual(len(result["duels"]), 3)
        self.assertEqual([call[0]["current_hp"] for call in scripted.calls], [maximum_hp, maximum_hp - 10, maximum_hp - 20])
        self.assertTrue(all(call[0]["stats"]["hp"] == maximum_hp for call in scripted.calls))
        self.assertTrue(all("temporary_status" not in fighter for call in scripted.calls for fighter in call))

    def test_relay_draws_eliminate_both_sides_and_five_duels_is_the_maximum(self):
        stage = self.service.stage_map["1-1"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        draw_engine = ScriptedEngine(("draw", "draw", "draw"))
        self.service.engine = draw_engine
        draw = self.service._team_battle(team, enemies, stage)
        self.assertFalse(draw["victory"])
        self.assertEqual(draw["stars"], 0)
        self.assertEqual(len(draw["duels"]), 3)
        relay_engine = ScriptedEngine(("a", "b", "a", "b", "a"))
        self.service.engine = relay_engine
        relay = self.service._team_battle(team, enemies, stage)
        self.assertTrue(relay["victory"])
        self.assertEqual(relay["stars"], 1)
        self.assertEqual(len(relay["duels"]), 5)

    def test_recommended_star_teams_meet_fixed_seed_win_rate_targets(self):
        allowed_ratings = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0)
        templates = [self.repo.generate_preview_fighter(name) for name in ("平衡甲", "平衡乙", "平衡丙")]
        expected_ranges = {"normal": (0.70, 0.80), "elite": (0.55, 0.65), "boss": (0.45, 0.60)}

        for stage_index, stage_id in enumerate(self.service.stage_order):
            stage = self.service.stage_map[stage_id]
            recommended = float(stage["recommended_stars"])
            ratings = min(
                itertools.combinations_with_replacement(allowed_ratings, 3),
                key=lambda values: (abs(sum(values) / 3 - recommended), max(values) - min(values)),
            )
            team = []
            for template, rating in zip(templates, ratings):
                fighter = dict(template)
                fighter["stats"] = self.repo._recalculate_final_stats(
                    dict(template["raw_stats"]),
                    rating,
                    1 if rating >= 6.0 else 0,
                    template["martial_art"],
                    template["neigong"],
                    template["qinggong"],
                )
                fighter["star_rating"] = rating
                team.append(fighter)
            enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
            wins = 0
            trials = 100
            for trial in range(trials):
                random.seed(20260921 + stage_index * 1000 + trial)
                wins += int(self.service._team_battle(team, enemies, stage)["victory"])
            win_rate = wins / trials
            low, high = expected_ranges[str(stage["kind"])]
            self.assertGreaterEqual(win_rate, low, stage_id)
            self.assertLessEqual(win_rate, high, stage_id)


if __name__ == "__main__":
    unittest.main()
