"""Upgrade regressions using temporary saves, including live WAL snapshots."""

import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import database
from database import FighterRepository


class StorageMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old = self.root / "data/name_fight_data/fighters.db"
        self.new = self.root / "data/plugin_data/astrbot_plugin_name_fight/fighters.db"
        self.source = FighterRepository(self.old)
        self.source.create_fighter_for_user("u1", "Migration Hero")
        self.source.grant_points("u1", 1000)
        self.source.buy_item("u1", "star_exp_pill_s", 2)
        self.avatar = self.old.parent / "avatars/nested/hero.img"
        self.avatar.parent.mkdir(parents=True)
        self.avatar.write_bytes(b"avatar-fixture")
        self.source.set_fighter_avatar_path("u1", "Migration Hero", str(self.avatar))
        self.addCleanup(patch.stopall)
        patch("database._default_data_dir", return_value=self.new.parent).start()
        patch("database._legacy_db_paths", return_value=[self.old]).start()

    def test_backup_preserves_wal_wallet_inventory_and_avatar_on_repeat_start(self):
        with sqlite3.connect(self.old) as writer:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("PRAGMA wal_autocheckpoint=0")
            writer.execute("UPDATE user_wallets SET points = 1234 WHERE user_id = 'u1'")
            writer.commit()
            self.assertTrue(Path(str(self.old) + "-wal").is_file())
            migrated = FighterRepository()
            self.assertEqual(migrated.get_user_points("u1"), 1234)
            self.assertEqual(
                migrated.get_user_items("u1"), self.source.get_user_items("u1")
            )
            saved = migrated.get_user_fighter_by_name("u1", "Migration Hero")
            new_avatar = Path(saved["avatar_path"])
            self.assertTrue(new_avatar.is_relative_to(self.new.parent / "avatars"))
            self.assertEqual(new_avatar.read_bytes(), self.avatar.read_bytes())
            self.assertTrue(self.old.is_file())
            self.assertTrue(self.avatar.is_file())
            migrated.grant_points("u1", 7)
            restarted = FighterRepository()
            self.assertEqual(restarted.get_user_points("u1"), 1241)
            self.assertEqual(
                restarted.get_user_fighter_by_name("u1", "Migration Hero")[
                    "avatar_path"
                ],
                str(new_avatar),
            )
            self.assertEqual(len(list((self.new.parent / "avatars").iterdir())), 1)

    def test_existing_new_save_is_not_overwritten(self):
        current = FighterRepository(self.new)
        current.create_fighter_for_user("u2", "New Hero")
        current.grant_points("u2", 222)
        restored = FighterRepository()
        self.assertEqual(restored.get_user_points("u2"), 222)
        self.assertIsNone(restored.get_user_fighter_by_name("u1", "Migration Hero"))
        self.assertFalse((self.new.parent / "avatars").exists())

    def test_copy_failure_leaves_no_database_and_can_retry(self):
        with patch("database.shutil.copy2", side_effect=OSError("copy failed")):
            with self.assertRaisesRegex(OSError, "copy failed"):
                FighterRepository()
        self.assertFalse(self.new.exists())
        self.assertFalse(list(self.new.parent.glob(".migration-*")))
        self.assertTrue(self.avatar.exists())
        self.assertEqual(FighterRepository().get_user_points("u1"), 910)

    def test_publish_failure_cleans_copied_avatars_and_can_retry(self):
        with patch("database.os.link", side_effect=OSError("publish failed")):
            with self.assertRaisesRegex(OSError, "publish failed"):
                FighterRepository()
        self.assertFalse(self.new.exists())
        self.assertEqual(list((self.new.parent / "avatars").iterdir()), [])
        self.assertFalse(list(self.new.parent.glob(".migration-*")))
        self.assertEqual(FighterRepository().get_user_points("u1"), 910)

    def test_concurrent_start_migrates_only_once(self):
        with ThreadPoolExecutor(max_workers=2) as workers:
            repos = list(workers.map(lambda _: FighterRepository(), range(2)))
        self.assertEqual([repo.get_user_points("u1") for repo in repos], [910, 910])
        self.assertEqual(len(list((self.new.parent / "avatars").iterdir())), 1)

    def test_explicit_path_does_not_import_legacy_players(self):
        custom = FighterRepository(self.root / "custom/fighters.db")
        self.assertIsNone(custom.get_user_fighter_by_name("u1", "Migration Hero"))
        self.assertEqual(custom.get_user_points("u1"), 0)

    def test_plugin_local_legacy_save_is_supported(self):
        with patch(
            "database._legacy_db_paths",
            return_value=[self.root / "absent.db", self.old],
        ):
            self.assertEqual(FighterRepository().get_user_points("u1"), 910)

    def test_framework_default_path_and_legacy_search_order(self):
        module = ModuleType("astrbot.core.utils.astrbot_path")
        module.get_astrbot_data_path = lambda: str(self.root / "data")
        patch.stopall()
        with patch.dict(sys.modules, {module.__name__: module}):
            self.assertEqual(database._default_db_path(), self.new)
            self.assertEqual(database._legacy_db_paths()[0], self.old)


if __name__ == "__main__":
    unittest.main()
