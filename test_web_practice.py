"""Verify administrator practice authorization and isolated battle behavior."""

import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "web" / "backend"))
sys.path.insert(0, str(ROOT / "web" / ".python-packages"))

from fastapi import HTTPException
from database import FighterRepository
from web_auth import WebIdentity

with tempfile.TemporaryDirectory() as import_directory:
    import_path = Path(import_directory) / "import.db"
    sqlite3.connect(import_path).close()
    with patch.dict(os.environ, {"NFIGHT_DB_PATH": str(import_path)}):
        import app as web_app


class PracticeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "practice.db"
        sqlite3.connect(self.path).close()
        self.repo_patch = patch.object(web_app, "repo", FighterRepository(self.path))
        self.repo_patch.start()
        self.env_patch = patch.dict(os.environ, {"NFIGHT_WEB_ADMIN_IDS": "10000001, 10000002"})
        self.env_patch.start()
        self.identity = WebIdentity("10000001", "20000001", "Admin")

    def tearDown(self):
        self.env_patch.stop()
        self.repo_patch.stop()
        self.temp.cleanup()

    def test_admin_whitelist_fails_closed(self):
        self.assertEqual(web_app.require_web_admin(self.identity), self.identity)
        with self.assertRaises(HTTPException) as result:
            web_app.require_web_admin(WebIdentity("10000003", "20000001", "Player"))
        self.assertEqual(result.exception.status_code, 403)
        with patch.dict(os.environ, {"NFIGHT_WEB_ADMIN_IDS": ""}):
            self.assertFalse(web_app.is_web_admin(self.identity))

    def test_practice_routes_require_admin(self):
        paths = {"/api/battles/showcase", "/api/admin/practice/config",
                 "/api/admin/practice/random", "/api/admin/practice/battle"}
        routes = [route for route in web_app.app.routes if getattr(route, "path", None) in paths]
        self.assertEqual({route.path for route in routes}, paths)
        for route in routes:
            self.assertIn(web_app.require_web_admin, [dependency.call for dependency in route.dependant.dependencies])

    def test_random_and_battle_preserve_database_and_requested_stats(self):
        with closing(sqlite3.connect(self.path)) as connection:
            before = list(connection.iterdump())
        fighters = [web_app.practice_random(self.identity) for _ in range(2)]
        def make(fighter, name):
            stats = dict(fighter["stats"], atk=123, spd=52.5)
            return web_app.PracticeFighter(name=name, stats=stats,
                martialArtId=fighter["martialArt"]["id"], neigongId=fighter["neigong"]["id"],
                qinggongId=fighter["qinggong"]["id"])
        result = web_app.practice_battle(web_app.PracticeBattle(
            attacker=make(fighters[0], "Test A"), defender=make(fighters[1], "Test B")), self.identity)
        self.assertEqual(result["attacker"]["stats"]["atk"], 123)
        self.assertEqual(result["attacker"]["stats"]["spd"], 52.5)
        self.assertTrue(result["events"])
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(before, list(connection.iterdump()))


if __name__ == "__main__":
    unittest.main()
