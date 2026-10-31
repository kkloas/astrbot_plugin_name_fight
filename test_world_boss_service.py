"""World boss cross-client transactions, replay identity and stage carryover."""

import random
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from unittest.mock import patch

from database import FighterRepository
from engine import CombatEngine
from world_boss import WorldBossService, default_boss


class FixedEngine:
    def battle_with_events(self, a, b):
        start_a, start_b = a["current_hp"], b["current_hp"]
        first = b["boss_key"].endswith("phase1")
        hp_a = max(1, start_a - 10) if first else 0
        hp_b = 0 if first else max(0, start_b - 70)
        winner = a["name"] if hp_b == 0 else b["name"]
        return {
            "winner": winner,
            "logs": ["test duel"],
            "events": [
                {
                    "type": "attack",
                    "actor": "b",
                    "target": "a",
                    "moveIndex": 0,
                    "move": b["martial_art"]["moves"][0]["name"],
                    "time": 1900,
                },
                {"type": "battle_end", "time": 3800},
            ],
            "state": {
                "fighter_a_hp": hp_a,
                "fighter_b_hp": hp_b,
                "fighter_a_max_hp": a["stats"]["hp"],
                "fighter_b_max_hp": b["stats"]["hp"],
            },
        }


class WorldBossServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = FighterRepository(Path(self.temp.name) / "test.db")
        for user in ("u1", "u2"):
            for i in range(3):
                self.repo.create_fighter_for_user(user, f"{user}-fighter-{i}")
        name, a, b = default_boss(self.repo)
        b["stats"]["hp"] = 1000
        self.activity = self.repo.open_group_boss("g", name, a, b, "admin")
        self.service = WorldBossService(self.repo, FixedEngine)

    def challenge(self, user="u1", key="request_0001", **kwargs):
        return self.service.challenge(
            "g", user, user, key, self.activity["boss_id"], **kwargs
        )

    def usage(self, user="u1"):
        return self.repo.get_group_boss_attempt_usage(
            self.activity["boss_id"], "g", user, date.today().isoformat()
        )

    def test_retry_is_same_replay_with_single_charge_and_contribution(self):
        first = self.challenge()
        repeated = self.challenge()
        self.assertEqual(first, repeated)
        self.assertEqual(self.usage(), 1)
        self.assertEqual(first["creditedDamage"], 210)
        self.assertEqual(
            self.repo.get_group_boss_by_id("g", self.activity["boss_id"])[
                "phase2_current_hp"
            ],
            790,
        )
        self.assertEqual(self.service.latest("g", "u1"), first)
        with self.assertRaises(ValueError):
            self.challenge(practice=True)
        self.assertIsNone(self.service.latest("other-group", "u1"))
        self.assertIsNone(self.service.latest("g", "other-user"))

    def test_practice_does_not_change_attempts_contributions_hp_or_wallet(self):
        result = self.challenge(practice=True)
        self.assertEqual(self.usage(), 0)
        self.assertEqual(result["creditedDamage"], 0)
        self.assertEqual(result["phase2_current_hp"], 1000)
        self.assertIsNone(
            self.repo.get_group_boss_contribution(self.activity["boss_id"], "g", "u1")
        )
        self.assertEqual(self.repo.get_user_points("u1"), 0)

    def test_phase_and_player_hp_carryover_keep_original_maximum(self):
        result = self.challenge(practice=True)
        first, second = result["duels"][:2]
        self.assertEqual((first["phase"], second["phase"]), (1, 2))
        self.assertEqual(
            second["attacker"]["currentHp"], first["state"]["fighter_a_hp"]
        )
        self.assertEqual(
            second["attacker"]["stats"]["hp"], first["attacker"]["stats"]["hp"]
        )
        self.assertEqual(
            result["duels"][2]["defender"]["currentHp"], second["state"]["fighter_b_hp"]
        )
        self.assertEqual(result["duels"][2]["defender"]["stats"]["hp"], 1000)
        self.assertTrue(second["boss"]["intro"])
        self.assertFalse(result["duels"][2]["boss"]["intro"])
        event = first["events"][1]
        self.assertNotEqual(event["move"], event["visualMove"])
        self.assertEqual(first["defender"]["bossKey"], "dragon_chief_phase1")

    def test_only_second_phase_practice_uses_full_hp(self):
        self.challenge()
        result = self.challenge(key="practice_0001", practice=True, phase="phase2")
        self.assertEqual(result["duels"][0]["defender"]["currentHp"], 1000)
        self.assertEqual(result["phase2_current_hp"], 790)
        self.assertEqual(self.usage(), 1)
        with self.assertRaises(ValueError):
            self.challenge(key="bad_phase_01", phase="phase2")

    def test_daily_limit_and_bad_team_do_not_charge_extra(self):
        for i in range(3):
            self.challenge(key=f"request_{i:04d}")
        with self.assertRaises(ValueError):
            self.challenge(key="request_9999")
        self.assertEqual(self.usage(), 3)
        with self.assertRaises(ValueError):
            self.challenge(user="u2", key="bad_team_001", slots=[1, 1, 2])
        self.assertEqual(self.usage("u2"), 0)

    def test_parallel_same_request_only_commits_once(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.challenge(), range(4)))
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(self.usage(), 1)
        self.assertEqual(results[0]["total_damage"], 210)

    def test_cross_client_kill_caps_damage_and_settles_once(self):
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE group_boss_activities SET phase2_current_hp = 250"
            )
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(
                    lambda user: self.challenge(user=user, key=f"client_{user}_01"),
                    ("u1", "u2"),
                )
            )
        self.assertEqual(sum(result["creditedDamage"] for result in results), 250)
        ranks = self.repo.get_group_boss_rank("g", self.activity["boss_id"])
        self.assertEqual(sum(row["total_damage"] for row in ranks), 250)
        self.assertEqual(sum(result["is_killed"] for result in results), 1)
        wallets = [self.repo.get_user_points(user) for user in ("u1", "u2")]
        self.assertEqual(sorted(wallets), [1700, 2000])
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(
                pool.map(
                    lambda _: self.repo.settle_group_boss(
                        "g", self.activity["boss_id"]
                    ),
                    range(4),
                )
            )
        self.assertEqual(
            wallets, [self.repo.get_user_points(user) for user in ("u1", "u2")]
        )

    def test_settlement_failure_rolls_back_entire_challenge(self):
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE group_boss_activities SET phase2_current_hp = 50"
            )
        with patch(
            "world_boss.settle_in_transaction",
            side_effect=RuntimeError("injected failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.challenge()
        self.assertEqual(self.usage(), 0)
        self.assertEqual(self.repo.get_active_group_boss("g")["phase2_current_hp"], 50)
        self.assertIsNone(
            self.repo.get_group_boss_contribution(self.activity["boss_id"], "g", "u1")
        )
        self.assertIsNone(self.service.latest("g", "u1"))
        self.assertTrue(self.challenge()["is_killed"])

    def test_all_contributors_receive_participation_rewards(self):
        for index in range(12):
            self.repo.record_group_boss_damage(
                self.activity["boss_id"],
                "g",
                f"contributor-{index}",
                str(index),
                100 - index,
            )
        self.repo.apply_group_boss_phase2_damage(self.activity["boss_id"], "g", 1000)
        result = self.repo.settle_group_boss("g", self.activity["boss_id"])
        self.assertEqual(len(result["participant_rewards"]), 12)
        self.assertEqual(len(result["rank_rewards"]), 10)
        self.assertEqual(self.repo.get_user_points("contributor-11"), 500)

    def test_real_engine_events_reconstruct_final_hp_without_mutating_roster(self):
        original = self.service.team("u1")
        service = WorldBossService(
            self.repo, lambda: CombatEngine(rng=random.Random(42))
        )
        result = service.simulate(original, self.activity, practice=True)
        self.assertEqual(original, self.service.team("u1"))
        for duel in result["duels"]:
            hp = {
                "a": duel["attacker"]["currentHp"],
                "b": duel["defender"]["currentHp"],
            }
            for event in duel["events"]:
                if "hpAfter" in event:
                    self.assertEqual(hp[event["target"]], event["hpBefore"])
                    hp[event["target"]] = event["hpAfter"]
            self.assertEqual(
                hp,
                {
                    "a": duel["state"]["fighter_a_hp"],
                    "b": duel["state"]["fighter_b_hp"],
                },
            )


if __name__ == "__main__":
    unittest.main()
