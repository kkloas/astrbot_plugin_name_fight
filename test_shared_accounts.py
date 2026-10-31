"""Use independent processes to exercise the same Bot/Web player database."""

import multiprocessing
import tempfile
import unittest
from pathlib import Path

from database import FighterRepository


def run_shared_action(path, action, start, results):
    try:
        repo = FighterRepository(Path(path))
        start.wait(10)
        if action == "signin":
            repo.claim_daily_signin("10000001", "2026-09-28")
        elif action == "feed":
            repo.feed_fighter_star_exp("10000001", "Shared hero", "star_exp_pill_s")
        elif action == "points":
            for _ in range(20):
                repo.grant_points("10000001", 1)
        elif action == "reward":
            repo.claim_pve_chapter_reward(
                "10000001", "chapter_1", ["1-1"], 3, {"points": 25, "items": []}
            )
        elif action == "switch":
            repo.append_pve_switch("10000001", "shared-attempt", 0, 1)
        results.put("ok")
    except ValueError:
        results.put("rejected")
    except Exception as exc:
        results.put(type(exc).__name__ + ": " + str(exc))


class SharedAccountConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "fighters.db"
        self.repo = FighterRepository(self.path)
        self.repo.create_fighter_for_user("10000001", "Shared hero")

    def tearDown(self):
        self.temp.cleanup()

    def race(self, action):
        context = multiprocessing.get_context("spawn")
        start, results = context.Event(), context.Queue()
        processes = [
            context.Process(
                target=run_shared_action, args=(str(self.path), action, start, results)
            )
            for _ in range(2)
        ]
        for process in processes:
            process.start()
        start.set()
        outcomes = [results.get(timeout=20) for _ in processes]
        for process in processes:
            process.join(10)
            if process.is_alive():
                process.terminate()
                self.fail("Account operation deadlocked")
            self.assertEqual(process.exitcode, 0)
        results.close()
        return sorted(outcomes)

    def test_signin_and_points_do_not_duplicate_or_overwrite(self):
        self.assertEqual(self.race("signin"), ["ok", "rejected"])
        self.assertEqual(self.repo.get_user_points("10000001"), 50)
        self.assertEqual(self.race("points"), ["ok", "ok"])
        self.assertEqual(self.repo.get_user_points("10000001"), 90)

    def test_last_item_is_consumed_once(self):
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE fighters SET star_rating = 1.0, star_exp = 0 WHERE name = 'Shared hero'"
            )
            connection.execute(
                "INSERT INTO user_items VALUES ('10000001', 'star_exp_pill_s', 1)"
            )
        self.assertEqual(self.race("feed"), ["ok", "rejected"])
        self.assertEqual(self.repo.get_user_items("10000001"), [])
        self.assertEqual(
            self.repo.get_user_fighter_by_name("10000001", "Shared hero")["star_exp"],
            50,
        )

    def test_chapter_reward_and_switch_are_committed_once(self):
        with self.repo._connect() as connection:
            connection.execute(
                "INSERT INTO pve_stage_progress VALUES ('10000001', '1-1', 3, 1, 1, 1)"
            )
        self.assertEqual(self.race("reward"), ["ok", "rejected"])
        self.assertEqual(self.repo.get_user_points("10000001"), 25)
        self.repo.create_pve_session(
            "10000001", "shared-attempt", "3-1", "tactic", 1, [], [], 10
        )
        self.assertEqual(self.race("switch"), ["ok", "rejected"])
        self.assertEqual(self.repo.get_pve_session("10000001")["decisions"], [1])
