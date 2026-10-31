import concurrent.futures
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import FighterRepository


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = FighterRepository(Path(self.temp.name) / "fighters.db")
        self.repo.create_fighter_for_user("u1", "结算测试甲")
        self.repo.create_fighter_for_user("u2", "结算测试乙")
        self.repo.record_group_battle("g", "结算测试甲", "结算测试乙", "结算测试甲")

    def tearDown(self):
        self.temp.cleanup()

    def test_concurrent_daily_settlements_pay_once(self):
        def settle():
            try:
                return self.repo.settle_daily_leaderboard("g", "1v1", "2026-10-27")
            except ValueError:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: settle(), range(2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        result = next(result for result in results if result is not None)
        for reward in result["rewards"]:
            self.assertEqual(
                self.repo.get_user_points(reward["user_id"]), reward["points"]
            )

    def test_weekly_failure_rolls_back_points_items_and_marker(self):
        with patch.object(
            self.repo, "_change_item_quantity", side_effect=RuntimeError("interrupted")
        ):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                self.repo.settle_weekly_leaderboard("g", "1v1", "2026-W44")
        self.assertEqual(self.repo.get_user_points("u1"), 0)
        self.assertEqual(self.repo.get_user_points("u2"), 0)
        self.assertFalse(self.repo.has_weekly_settlement("g", "1v1", "2026-W44"))
        result = self.repo.settle_weekly_leaderboard("g", "1v1", "2026-W44")
        self.assertEqual(result["rewards"][0]["points"], 500)
        self.assertEqual(self.repo.get_user_points("u1"), 500)
        self.assertEqual(self.repo.get_user_items("u1")[0]["quantity"], 1)

    def test_saved_snapshot_survives_restart_and_uses_original_rank(self):
        self.repo.save_daily_settlement_snapshot("g", "1v1", "2026-10-27")
        snapshot = self.repo.get_pending_daily_settlement_snapshots()[0]
        self.repo.record_group_battle("g", "结算测试乙", "结算测试甲", "结算测试乙")
        repo = FighterRepository(self.repo.db_path)
        snapshot = repo.get_pending_daily_settlement_snapshots()[0]
        result = repo.settle_daily_leaderboard(
            "g", "1v1", "2026-10-27", entries=snapshot["entries"]
        )
        self.assertEqual(result["rewards"][0]["user_id"], "u1")
        self.assertEqual(repo.get_user_points("u1"), 90)
        self.assertEqual(repo.get_pending_daily_settlement_snapshots(), [])


if __name__ == "__main__":
    unittest.main()
