"""Release regressions using disposable saves and trusted event fixtures."""

import ast
import asyncio
import ipaddress
import hashlib
import logging
import sqlite3
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from zoneinfo import ZoneInfo

from PIL import Image

from avatar_storage import PublicResolver, normalize_image, save_avatar, validate_url
from database import FighterRepository
from render_profile import render_star_card
from text_resources import compact_battle_logs

ROOT = Path(__file__).parent
FIXED_NOW = datetime(2026, 10, 13, 12, tzinfo=ZoneInfo("Asia/Shanghai"))
DAY = "2026-10-12"
WEEK = "2026-W41"


def load_bot_functions():
    names = {
        "_safe_call",
        "_boss_admin_ids",
        "_is_boss_admin",
        "_require_boss_admin",
        "_render_and_send_battle",
        "_send_battle_animation_safe",
        "_send_battle_sequence_safe",
        "terminate",
        "daily_settle_command",
        "weekly_settle_command",
        "_start_battle",
        "extract_group_id",
        "extract_user_id",
        "extract_first_image_ref",
        "_image_ref_from_mapping",
        "_avatar_target_path",
        "_save_fighter_avatar",
    }
    nodes = []
    for node in ast.walk(ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in names
        ):
            node.decorator_list = []
            nodes.append(node)
    namespace = {
        "__package__": None,
        "Any": Any,
        "hashlib": hashlib,
        "AstrMessageEvent": object,
        "asyncio": asyncio,
        "Path": Path,
        "time": time,
        "logger": logging.getLogger("test"),
        "datetime": datetime,
        "timedelta": timedelta,
        "ZoneInfo": ZoneInfo,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "main.py", "exec"), namespace)
    return namespace


BOT = load_bot_functions()


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "fighters.db"
        self.repo = FighterRepository(self.path)
        for user, name in [("u1", "Hero A"), ("u2", "Hero B")]:
            self.repo.create_fighter_for_user(user, name)
        self.repo.record_group_battle("g1", "Hero A", "Hero B", "Hero A")
        self.clock = patch("database.datetime")
        self.clock.start().now.return_value = FIXED_NOW

    def tearDown(self):
        self.clock.stop()
        self.temp.cleanup()

    def test_arbitrary_dates_and_current_week_are_rejected(self):
        for day in ["2026-10-13", "2026-10-11", "2099-01-01"]:
            with self.assertRaises(ValueError):
                self.repo.settle_daily_leaderboard("g1", "1v1", day)
        with self.assertRaises(ValueError):
            self.repo.settle_weekly_leaderboard("g1", "1v1", "2026-W42")
        self.assertEqual(self.repo.get_user_points("u1"), 0)

    def test_daily_and_weekly_concurrency_pay_once(self):
        for method, key, total in [
            ("settle_daily_leaderboard", DAY, 90),
            ("settle_weekly_leaderboard", WEEK, 590),
        ]:
            barrier = threading.Barrier(2)
            repos = [FighterRepository(self.path), FighterRepository(self.path)]

            def run(repo, method=method, key=key, barrier=barrier):
                barrier.wait(timeout=5)
                try:
                    getattr(repo, method)("g1", "1v1", key)
                    return "paid"
                except ValueError:
                    return "duplicate"

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(run, repos))
            self.assertEqual(sorted(results), ["duplicate", "paid"])
            self.assertEqual(self.repo.get_user_points("u1"), total)
        items = self.repo.get_user_items("u1")
        self.assertEqual(items[0]["quantity"], 1)

    def test_reward_write_failure_rolls_back_wallets_and_items(self):
        for method, table, key in [
            ("settle_daily_leaderboard", "daily_settlements", DAY),
            ("settle_weekly_leaderboard", "weekly_settlements", WEEK),
        ]:
            with self.repo._connect() as connection:
                connection.execute(
                    f"CREATE TRIGGER fail BEFORE INSERT ON {table} BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
                )
            with self.assertRaises(sqlite3.IntegrityError):
                getattr(self.repo, method)("g1", "1v1", key)
            self.assertEqual(self.repo.get_user_points("u1"), 0)
            self.assertEqual(self.repo.get_user_points("u2"), 0)
            self.assertEqual(self.repo.get_user_items("u1"), [])
            with self.repo._connect() as connection:
                connection.execute("DROP TRIGGER fail")
            getattr(self.repo, method)("g1", "1v1", key)
            with self.repo._connect() as connection:
                connection.execute(f"DELETE FROM {table}")
                connection.execute("UPDATE user_wallets SET points = 0")
                connection.execute("DELETE FROM user_items")

    def test_closed_boss_failure_rolls_back_and_retry_pays_once(self):
        fighter = self.repo.get_user_fighter_by_name("u1", "Hero A")
        boss = self.repo.open_group_boss("g1", "Boss", fighter, fighter, "admin")
        boss_id = boss["boss_id"]
        with self.repo._connect() as connection:
            connection.execute(
                "INSERT INTO group_boss_contributions (boss_id, group_id, user_id, display_name, total_damage, attempts) VALUES (?, ?, ?, ?, ?, ?)",
                (boss_id, "g1", "u1", "Player", 100, 1),
            )
        self.repo.close_group_boss("g1", boss_id)
        with self.repo._connect() as connection:
            connection.execute(
                "CREATE TRIGGER fail BEFORE INSERT ON group_boss_settlements BEGIN SELECT RAISE(ABORT, 'fail'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.settle_group_boss("g1", boss_id)
        self.assertEqual(self.repo.get_user_points("u1"), 0)
        self.assertEqual(self.repo.get_user_items("u1"), [])
        with self.repo._connect() as connection:
            connection.execute("DROP TRIGGER fail")
        result = self.repo.settle_group_boss("g1", boss_id)
        points = self.repo.get_user_points("u1")
        self.assertEqual(self.repo.settle_group_boss("g1", boss_id), result)
        self.assertEqual(self.repo.get_user_points("u1"), points)


class PermissionTests(unittest.IsolatedAsyncioTestCase):
    def make_bot(self, config=None):
        bot = SimpleNamespace(config=config or {})
        for name in ["_boss_admin_ids", "_is_boss_admin", "_require_boss_admin"]:
            setattr(bot, name, BOT[name].__get__(bot))
        return bot

    def event(self, role="member"):
        event = Mock()
        event.is_admin.return_value = False
        event.get_platform_name.return_value = "aiocqhttp"
        event.get_group_id.return_value = "20000001"
        event.message_obj = SimpleNamespace(
            raw_message={
                "group_id": 20000001,
                "sender": {"user_id": 10000001, "role": role},
            }
        )
        event.send = AsyncMock()
        return event

    async def test_members_unknown_and_forged_sender_are_rejected(self):
        bot = self.make_bot()
        event = self.event()
        self.assertFalse(bot._is_boss_admin(event, "10000001"))
        event.message_obj.raw_message = {}
        self.assertFalse(bot._is_boss_admin(event, "10000001"))
        event = self.event("owner")
        self.assertFalse(bot._is_boss_admin(event, "99999999"))
        for name in ["daily_settle_command", "weekly_settle_command"]:
            bot._require_user_id = AsyncMock(return_value="10000001")
            bot._require_group_id = AsyncMock()
            await BOT[name](bot, self.event())
            bot._require_group_id.assert_not_awaited()

    async def test_trusted_admin_and_explicit_allowlist(self):
        bot = self.make_bot()
        self.assertTrue(bot._is_boss_admin(self.event("admin"), "10000001"))
        event = self.event()
        event.is_admin.return_value = True
        self.assertTrue(bot._is_boss_admin(event, "10000001"))
        bot.config = {"boss_admin_user_ids": ["12345678"]}
        self.assertFalse(bot._is_boss_admin(event, "10000001"))
        self.assertTrue(bot._is_boss_admin(event, "12345678"))

    async def test_message_text_cannot_supply_identity_or_image(self):
        event = self.event()
        event.get_sender_id.return_value = ""
        event.message_str = "[CQ:image,file=/etc/passwd] user_id=10000001"
        event.get_messages.return_value = []
        with self.assertRaises(RuntimeError):
            BOT["extract_user_id"](event)
        self.assertIsNone(BOT["extract_first_image_ref"](event))
        event.get_group_id.return_value = ""
        with self.assertRaises(RuntimeError):
            BOT["extract_group_id"](event)


class GifImportFallbackTests(unittest.IsolatedAsyncioTestCase):
    def make_bot(self, enabled=True):
        return SimpleNamespace(
            config={"enable_gif": enabled}, _render_and_send_battle=AsyncMock()
        )

    async def test_disabled_gif_skips_path_lookup_and_import(self):
        bot = self.make_bot(False)
        path = Mock(side_effect=RuntimeError("must not look up paths"))
        with patch.dict(BOT, {"get_astrbot_temp_path": path}):
            with patch("builtins.__import__") as importer:
                result = await BOT["_send_battle_animation_safe"](
                    bot, object(), {}, {}, {}
                )
        self.assertFalse(result)
        path.assert_not_called()
        importer.assert_not_called()
        bot._render_and_send_battle.assert_not_awaited()

    async def test_single_battle_still_sends_text_and_records_result_after_import_failure(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            repo = FighterRepository(Path(directory) / "fighters.db")
            attacker = repo.create_fighter_for_user("u1", "A")
            defender = repo.create_fighter_for_user("u2", "B")
            bot = self.make_bot()
            bot.repo = repo
            bot.broadcast_delay = 0
            bot._battling_groups = set()
            bot._battle_tasks = set()
            bot._send_lines = AsyncMock()
            bot._grant_ranked_battle_points = Mock(return_value=(20, 8, 20, 8, 0, 0))
            result = {"winner": "A", "logs": ["A wins"]}
            bot.engine = SimpleNamespace(battle_with_events=Mock(return_value=result))
            bot._send_battle_animation_safe = BOT[
                "_send_battle_animation_safe"
            ].__get__(bot)
            event = Mock(send=AsyncMock())
            event.plain_result.side_effect = str
            with patch.dict(
                BOT,
                {
                    "get_astrbot_temp_path": Mock(return_value="temp"),
                    "compact_battle_logs": compact_battle_logs,
                    "battle_overview_line": Mock(return_value="A vs B"),
                },
            ):
                with patch(
                    "builtins.__import__", side_effect=ModuleNotFoundError("websockets")
                ):
                    await BOT["_start_battle"](
                        bot, event, "g1", attacker, defender, "start", ("u1", "u2")
                    )
            bot._send_lines.assert_awaited_once_with(
                event, compact_battle_logs(result["logs"])
            )
            self.assertEqual(repo.get_group_leaderboard("g1")[0]["fighter_name"], "A")
            bot._grant_ranked_battle_points.assert_called_once()
            self.assertIn("积分奖励", event.send.await_args_list[-1].args[0])
            self.assertEqual(bot._battling_groups, set())
            self.assertEqual(bot._battle_tasks, set())
            bot._render_and_send_battle.assert_not_awaited()

    async def test_missing_dependency_and_import_initialization_error_fall_back(self):
        real_import = __import__
        for package in (None, "astrbot_plugin_name_fight"):
            for error in (
                ModuleNotFoundError("websockets"),
                RuntimeError("bad dependency"),
            ):
                with self.subTest(package=package, error=type(error).__name__):
                    bot = self.make_bot()

                    def import_renderer(name, *args, **kwargs):
                        if name == "web_battle_renderer":
                            raise error
                        return real_import(name, *args, **kwargs)

                    with patch.dict(
                        BOT,
                        {
                            "__package__": package,
                            "get_astrbot_temp_path": Mock(return_value="temp"),
                        },
                    ):
                        with patch("builtins.__import__", side_effect=import_renderer):
                            result = await BOT["_send_battle_animation_safe"](
                                bot, object(), {}, {}, {}
                            )
                    self.assertFalse(result)
                    bot._render_and_send_battle.assert_not_awaited()

    async def test_path_lookup_failure_falls_back_before_import(self):
        bot = self.make_bot()
        with patch.dict(
            BOT,
            {"get_astrbot_temp_path": Mock(side_effect=OSError("temp unavailable"))},
        ):
            with patch("builtins.__import__") as importer:
                result = await BOT["_send_battle_animation_safe"](
                    bot, object(), {}, {}, {}
                )
        self.assertFalse(result)
        importer.assert_not_called()
        bot._render_and_send_battle.assert_not_awaited()

    async def test_available_renderer_is_used_in_both_import_modes(self):
        real_import = __import__
        renderer = Mock()
        module = SimpleNamespace(render_battle_animation=renderer)

        def import_renderer(name, *args, **kwargs):
            if name == "web_battle_renderer":
                return module
            return real_import(name, *args, **kwargs)

        for package in (None, "astrbot_plugin_name_fight"):
            bot = self.make_bot()
            bot._render_and_send_battle.return_value = True
            event, attacker, defender, replay = object(), {}, {}, {"logs": []}
            with patch.dict(
                BOT,
                {
                    "__package__": package,
                    "get_astrbot_temp_path": Mock(return_value="temp"),
                },
            ):
                with patch("builtins.__import__", side_effect=import_renderer):
                    self.assertTrue(
                        await BOT["_send_battle_animation_safe"](
                            bot, event, attacker, defender, replay, "title"
                        )
                    )
            bot._render_and_send_battle.assert_awaited_once_with(
                event, renderer, attacker, defender, replay, "temp", "title"
            )

    async def test_team_replay_sends_each_bout_as_text_when_dependency_is_missing(self):
        bot = self.make_bot()
        bot._send_lines = AsyncMock()
        bot._send_battle_animation_safe = BOT["_send_battle_animation_safe"].__get__(
            bot
        )
        event = Mock(send=AsyncMock())
        event.plain_result.side_effect = str
        segments = [
            {
                "fighter_a": {"name": "A"},
                "fighter_b": {"name": "B"},
                "result": {"logs": [text]},
            }
            for text in ("first bout", "second bout")
        ]
        with patch.dict(
            BOT,
            {
                "get_astrbot_temp_path": Mock(return_value="temp"),
                "compact_battle_logs": compact_battle_logs,
            },
        ):
            with patch(
                "builtins.__import__", side_effect=ModuleNotFoundError("websockets")
            ):
                self.assertTrue(
                    await BOT["_send_battle_sequence_safe"](bot, event, segments)
                )
        self.assertEqual(bot._send_lines.await_count, 2)
        self.assertEqual(
            [call.args[1] for call in bot._send_lines.await_args_list],
            [compact_battle_logs(segment["result"]["logs"]) for segment in segments],
        )
        bot._render_and_send_battle.assert_not_awaited()


class ResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_avatar_names_are_account_scoped_and_old_shared_file_survives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = FighterRepository(root / "fighters.db")
            repo.create_fighter_for_user("u1", "Hero")
            repo.create_fighter_for_user("u2", "hero")
            shared = root / "shared.img"
            shared.write_bytes(b"old")
            for user, name in [("u1", "Hero"), ("u2", "hero")]:
                repo.set_fighter_avatar_path(user, name, str(shared))
            bot = SimpleNamespace(
                repo=repo, _avatar_dir=lambda: root, _write_avatar_image=AsyncMock()
            )
            bot._avatar_target_path = BOT["_avatar_target_path"].__get__(bot)
            self.assertNotEqual(
                bot._avatar_target_path("u1", "Hero"),
                bot._avatar_target_path("u2", "hero"),
            )
            self.assertNotEqual(
                bot._avatar_target_path("u1", "Hero"),
                bot._avatar_target_path("u1", "hero"),
            )
            await BOT["_save_fighter_avatar"](bot, "u1", "Hero", "unused")
            self.assertTrue(shared.exists())
            self.assertEqual(
                repo.get_user_fighter_by_name("u2", "hero")["avatar_path"], str(shared)
            )
            await BOT["_save_fighter_avatar"](bot, "u2", "hero", "unused")
            self.assertFalse(shared.exists())

    async def test_avatar_local_limits_and_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / "source.png", root / "avatar.img"
            Image.new("RGB", (2000, 20), "red").save(source)
            await save_avatar(
                str(source), target, allowed_roots=[root], maximum_bytes=10000
            )
            with Image.open(target) as result:
                self.assertEqual(result.format, "JPEG")
                self.assertEqual(result.width, 1024)
            with self.assertRaises(ValueError):
                await save_avatar(
                    str(source), target, allowed_roots=[root], maximum_bytes=1
                )
            with self.assertRaises(ValueError):
                await save_avatar(
                    "/etc/passwd", target, allowed_roots=[root], maximum_bytes=10000
                )
            with self.assertRaises(ValueError):
                normalize_image(b"not an image", target)

    async def test_private_urls_and_mixed_dns_are_rejected(self):
        for url in [
            "http://127.0.0.1/a",
            "http://[::1]/a",
            "http://169.254.169.254/a",
            "http://10.0.0.1/a",
            "http://user:pass@example.com/a",
            "http://example.com:8000/a",
        ]:
            with self.assertRaises(ValueError):
                validate_url(url)
        resolver = PublicResolver()
        with patch(
            "avatar_storage.DefaultResolver.resolve",
            new=AsyncMock(return_value=[{"host": "8.8.8.8"}, {"host": "10.0.0.1"}]),
        ):
            with self.assertRaises(ValueError):
                await resolver.resolve("example.com")
        await resolver.close()
        self.assertTrue(ipaddress.ip_address("8.8.8.8").is_global)

    async def test_render_timeout_holds_slot_and_cleans_late_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "late.gif"
            release = threading.Event()
            bot = SimpleNamespace(
                config={"render_timeout": 5},
                _render_slots=asyncio.Semaphore(1),
                _render_tasks=set(),
                _send_image_path_safe=AsyncMock(return_value=True),
            )

            def renderer():
                release.wait(10)
                output.write_bytes(b"gif")
                return str(output)

            try:
                result = await BOT["_render_and_send_battle"](bot, object(), renderer)
                self.assertFalse(result)
                self.assertTrue(bot._render_slots.locked())
                release.set()
                await asyncio.gather(*bot._render_tasks)
                await asyncio.sleep(0)
                self.assertFalse(output.exists())
                self.assertFalse(bot._render_slots.locked())
                bot._send_image_path_safe.assert_not_awaited()
            finally:
                release.set()

    async def test_terminate_cancels_owned_tasks(self):
        tasks = {asyncio.create_task(asyncio.sleep(30)) for _ in range(2)}
        bot = SimpleNamespace(
            _battle_tasks=tasks,
            _daily_settlement_task=asyncio.create_task(asyncio.sleep(30)),
            _battling_groups={"g1"},
            pending_challenges={},
            pending_team3_challenges={},
            pending_creations={},
            pending_martial_choices={},
            pending_avatar_uploads={},
        )
        await BOT["terminate"](bot)
        self.assertTrue(all(task.cancelled() for task in tasks))
        self.assertTrue(bot._daily_settlement_task.cancelled())
        self.assertEqual(bot._battling_groups, set())

    async def test_two_groups_can_battle_while_same_group_is_rejected(self):
        bot = SimpleNamespace(
            _battling_groups=set(),
            _battle_tasks=set(),
            _daily_settlement_task=None,
            pending_challenges={},
            pending_team3_challenges={},
            pending_creations={},
            pending_martial_choices={},
            pending_avatar_uploads={},
        )
        started = [asyncio.Event(), asyncio.Event()]
        hold = asyncio.Event()
        events = []
        for signal in started:
            event = Mock()
            event.plain_result.side_effect = str

            async def pause(message, signal=signal):
                signal.set()
                await hold.wait()

            event.send = AsyncMock(side_effect=pause)
            events.append(event)
        tasks = [
            asyncio.create_task(
                BOT["_start_battle"](bot, event, group, {}, {}, "start")
            )
            for event, group in zip(events, ["g1", "g2"])
        ]
        try:
            await asyncio.wait_for(
                asyncio.gather(*(event.wait() for event in started)), 1
            )
            self.assertEqual(bot._battling_groups, {"g1", "g2"})
            duplicate = Mock()
            duplicate.send = AsyncMock()
            await BOT["_start_battle"](bot, duplicate, "g1", {}, {}, "start")
            duplicate.send.assert_awaited_once()
            self.assertEqual(bot._battling_groups, {"g1", "g2"})
        finally:
            await BOT["terminate"](bot)
        self.assertTrue(all(task.cancelled() for task in tasks))
        self.assertEqual(bot._battle_tasks, set())

    async def test_open_font_and_external_card_output(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = FighterRepository(Path(directory) / "fighters.db")
            fighter = repo.create_fighter_for_user(
                "u", "中文角色", forced_base_star=5.0
            )
            output = render_star_card(fighter, str(ROOT / "data"), directory)
            self.assertTrue(Path(output).is_relative_to(Path(directory)))
            with Image.open(output) as image:
                self.assertGreater(image.width, 100)


if __name__ == "__main__":
    unittest.main()
