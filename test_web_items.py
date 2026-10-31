from __future__ import annotations

import tempfile
import sqlite3
import unittest
from contextlib import contextmanager
from pathlib import Path

from database import FighterRepository


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


class WebItemFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="name-fight-items-")
        self.path = Path(self.temp.name) / "fighters.db"
        self.repo = ClosingRepository(self.path)
        self.user_id = "web-item-test"
        self.fighter = self.repo.create_fighter_for_user(self.user_id, "道具测试角色")
        with self.repo._connect() as connection:
            connection.execute(
                "INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, ?)",
                (self.user_id, "martial_token_choice", 2),
            )
            connection.commit()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_choice_persists_and_only_generated_option_can_be_applied(self) -> None:
        old_id = self.fighter["martial_art"]["id"]
        pending = self.repo.create_web_loadout_choice(self.user_id, self.fighter["name"], "martial_art")
        self.assertEqual(len(pending["options"]), 3)
        self.assertEqual(self.repo.get_user_items(self.user_id)[0]["quantity"], 1)
        reopened = ClosingRepository(self.path).get_web_loadout_choice(self.user_id)
        self.assertEqual([item["id"] for item in reopened["options"]], [item["id"] for item in pending["options"]])
        with self.assertRaisesRegex(ValueError, "只能选择本次生成"):
            self.repo.apply_web_loadout_choice(self.user_id, self.fighter["name"], "martial_art", "forged")
        self.assertEqual(self.repo.get_user_fighter_by_name(self.user_id, self.fighter["name"])["martial_art"]["id"], old_id)
        chosen = pending["options"][0]["id"]
        self.repo.apply_web_loadout_choice(self.user_id, self.fighter["name"], "martial_art", chosen)
        self.assertEqual(self.repo.get_user_fighter_by_name(self.user_id, self.fighter["name"])["martial_art"]["id"], chosen)
        self.assertIsNone(self.repo.get_web_loadout_choice(self.user_id))
        with self.assertRaises(ValueError):
            self.repo.apply_web_loadout_choice(self.user_id, self.fighter["name"], "martial_art", chosen)

    def test_pending_blocks_repeat_use_and_abandon_does_not_refund(self) -> None:
        self.repo.create_web_loadout_choice(self.user_id, self.fighter["name"], "neigong")
        with self.assertRaisesRegex(ValueError, "先完成或放弃"):
            self.repo.create_web_loadout_choice(self.user_id, self.fighter["name"], "qinggong")
        self.assertEqual(self.repo.get_user_items(self.user_id)[0]["quantity"], 1)
        self.repo.abandon_web_loadout_choice(self.user_id)
        self.assertIsNone(self.repo.get_web_loadout_choice(self.user_id))
        self.assertEqual(self.repo.get_user_items(self.user_id)[0]["quantity"], 1)

    def test_invalid_category_and_changed_loadout_do_not_consume_extra_item(self) -> None:
        with self.assertRaises(ValueError):
            self.repo.create_web_loadout_choice(self.user_id, self.fighter["name"], "invalid")
        self.assertEqual(self.repo.get_user_items(self.user_id)[0]["quantity"], 2)
        pending = self.repo.create_web_loadout_choice(self.user_id, self.fighter["name"], "qinggong")
        with self.repo._connect() as connection:
            alternate = next(item["id"] for item in self.repo.qinggong if item["id"] != pending["old_entry"]["id"])
            connection.execute("UPDATE fighters SET qinggong_id = ? WHERE name = ?", (alternate, self.fighter["name"]))
            connection.commit()
        with self.assertRaisesRegex(ValueError, "功法已变化"):
            self.repo.apply_web_loadout_choice(
                self.user_id, self.fighter["name"], "qinggong", pending["options"][0]["id"]
            )
        self.assertIsNotNone(self.repo.get_web_loadout_choice(self.user_id))

    def test_summon_preview_persists_without_consuming_and_confirm_consumes_once(self) -> None:
        with self.repo._connect() as connection:
            connection.execute(
                "INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, ?)",
                (self.user_id, "special_summon_token", 1),
            )
            connection.commit()
        preview = self.repo.create_web_summon_preview(self.user_id, "新召唤角色")
        self.assertIn(preview["star_rating"], (5.0, 6.0))
        self.assertEqual(ClosingRepository(self.path).get_web_summon_preview(self.user_id)["name"], "新召唤角色")
        self.assertEqual(next(item["quantity"] for item in self.repo.get_user_items(self.user_id) if item["item_id"] == "special_summon_token"), 1)
        with self.assertRaisesRegex(ValueError, "已有的召唤预览"):
            self.repo.create_web_summon_preview(self.user_id, "另一个角色")
        replaced, fighter = self.repo.commit_web_summon_preview(self.user_id)
        self.assertIsNone(replaced)
        self.assertEqual(fighter["name"], "新召唤角色")
        self.assertIsNone(self.repo.get_web_summon_preview(self.user_id))
        self.assertFalse(any(item["item_id"] == "special_summon_token" for item in self.repo.get_user_items(self.user_id)))
        with self.assertRaisesRegex(ValueError, "没有待确认"):
            self.repo.commit_web_summon_preview(self.user_id)

    def test_summon_full_roster_requires_valid_replacement(self) -> None:
        with self.repo._connect() as connection:
            connection.execute(
                "INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, ?)",
                (self.user_id, "special_summon_token", 1),
            )
            connection.commit()
        for index in range(2, 6):
            self.repo.create_fighter_for_user(self.user_id, f"旧角色{index}")
        self.repo.create_web_summon_preview(self.user_id, "待替换角色")
        with self.assertRaisesRegex(ValueError, "请选择要替换"):
            self.repo.commit_web_summon_preview(self.user_id)
        self.assertEqual(len(self.repo.get_user_fighters(self.user_id)), 5)
        self.assertIsNotNone(self.repo.get_web_summon_preview(self.user_id))
        self.assertEqual(next(item["quantity"] for item in self.repo.get_user_items(self.user_id) if item["item_id"] == "special_summon_token"), 1)
        replaced, fighter = self.repo.commit_web_summon_preview(self.user_id, 1)
        self.assertEqual(replaced, self.fighter["name"])
        self.assertEqual(fighter["name"], "待替换角色")
        self.assertEqual(fighter["slot_index"], 1)
        self.assertTrue(fighter["is_active"])
        self.assertIsNone(self.repo.get_fighter_by_name(self.fighter["name"]))


if __name__ == "__main__":
    unittest.main()
