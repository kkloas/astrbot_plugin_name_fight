"""Check real delivery control flow without player state or network sends."""

import ast
import asyncio
import hashlib
import logging
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aiocqhttp.exceptions import ActionFailed, NetworkError

from battle_delivery import (
    BATTLE_SEND_TIMEOUT_SECONDS,
    QQ_GIF_TIMEOUT_MS,
    BattleDeliveryState,
    send_qq_battle_image,
)


def load_method(name, **overrides):
    tree = ast.parse(
        Path(__file__).with_name("main.py").read_text(encoding="utf-8-sig")
    )
    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == name
    )
    namespace = {
        "Any": Any,
        "AstrMessageEvent": object,
        "asyncio": asyncio,
        "time": time,
        "Path": Path,
        "logger": logging.getLogger(__name__),
        "BattleDeliveryState": BattleDeliveryState,
        "BATTLE_SEND_TIMEOUT_SECONDS": BATTLE_SEND_TIMEOUT_SECONDS,
        **overrides,
    }
    exec(  # noqa: S102 - Compile only a trusted local method without plugin startup.
        compile(ast.Module(body=[node], type_ignores=[]), "main.py", "exec"), namespace
    )
    return namespace[name]


class SettlementDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_boss_unknown_stops_later_gifs_and_keeps_final_settlement(self):
        event = Mock()
        event.message_obj.message_id = "fixture"
        event.stop_event = Mock()
        bot = Mock()
        bot._battling_groups = set()
        bot._require_user_id = AsyncMock(return_value="u")
        bot._require_group_id = AsyncMock(return_value="g")
        bot.repo.get_active_group_boss.return_value = {"boss_id": "boss"}
        duel = {
            "phase": 1,
            "boss": {"label": "boss"},
            "index": 1,
            "attacker": {"name": "A"},
            "defender": {"name": "B"},
            "fighter_a": {},
            "fighter_b": {},
            "result": {},
            "logs": ["log"],
        }
        bot.world_boss.challenge.return_value = {
            "boss_name": "boss",
            "duels": [duel, duel, duel],
            "settlement": {"fixture": True},
        }
        bot._send_text_safe = AsyncMock()
        bot._send_lines = AsyncMock()
        bot._send_battle_animation_safe = AsyncMock(
            return_value=BattleDeliveryState.UNKNOWN
        )
        method = load_method(
            "_run_world_boss",
            hashlib=hashlib,
            extract_user_label=lambda _: "A",
            boss_fight_result_message=lambda _: "final result",
            boss_settlement_message=lambda _: "final settlement",
        )
        await method(bot, event)
        bot.world_boss.challenge.assert_called_once()
        bot._send_battle_animation_safe.assert_awaited_once()
        bot._send_lines.assert_not_awaited()
        texts = [call.args[1] for call in bot._send_text_safe.await_args_list]
        self.assertEqual(texts.count("final result"), 1)
        self.assertEqual(texts.count("final settlement"), 1)
        self.assertEqual(bot._battling_groups, set())
        event.stop_event.assert_called_once()

    async def test_single_and_team_settle_once_for_every_delivery_outcome(self):
        rating = {
            side: {"name": side, "delta": 1, "before": 100, "after": 101}
            for side in ("attacker", "defender")
        }
        for outcome in BattleDeliveryState:
            for team in (False, True):
                with self.subTest(outcome=outcome, team=team):
                    event = Mock()
                    event.send = AsyncMock()
                    event.plain_result = str
                    bot = Mock()
                    bot._battling_groups = set()
                    bot.broadcast_delay = 0
                    bot.repo.record_group_battle.return_value = rating
                    bot.repo.record_group_team3_battle.return_value = rating
                    bot.engine.battle_with_events.return_value = {
                        "logs": ["fixture log"],
                        "winner": "A",
                    }
                    bot._battle_team3_with_result.return_value = (
                        ["fixture log"],
                        "attacker",
                        [{"fixture": True}],
                    )
                    bot._send_battle_animation_safe = AsyncMock(return_value=outcome)
                    bot._send_battle_sequence_safe = AsyncMock(return_value=outcome)
                    bot._send_lines = AsyncMock()
                    bot._send_text_safe = AsyncMock()
                    if team:
                        method = load_method("_start_team3_battle")
                        await method(
                            bot, event, "g", "u1", "A", [], "u2", "B", [], "start"
                        )
                        bot.repo.record_group_team3_battle.assert_called_once_with(
                            "g", "u1", "A", "u2", "B", "u1", elo_scale=1.0
                        )
                        bot.repo.record_group_battle.assert_not_called()
                    else:
                        method = load_method(
                            "_start_battle",
                            compact_battle_logs=list,
                            battle_overview_line=lambda *_: "overview",
                        )
                        await method(
                            bot, event, "g", {"name": "A"}, {"name": "B"}, "start"
                        )
                        bot.repo.record_group_battle.assert_called_once_with(
                            "g", "A", "B", "A", elo_scale=1.0
                        )
                        bot.repo.record_group_team3_battle.assert_not_called()
                    self.assertEqual(
                        bot._send_lines.await_count,
                        int(outcome is BattleDeliveryState.FAILED),
                    )
                    self.assertEqual(
                        bot._send_text_safe.await_count,
                        int(outcome is BattleDeliveryState.UNKNOWN),
                    )
                    bot._grant_ranked_battle_points.assert_not_called()
                    self.assertEqual(bot._battling_groups, set())
                    event.stop_event.assert_called_once()


class BattleDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_base64_and_recipient_with_request_scoped_timeout(self):
        for group, user, action, key in [
            ("", "123456", "send_private_msg", "user_id"),
            ("987654", "123456", "send_group_msg", "group_id"),
        ]:
            with self.subTest(action=action):
                bot = type("Bot", (), {})()
                bot.call_action = AsyncMock(return_value={"message_id": -7})
                result = await send_qq_battle_image(
                    bot, group_id=group, user_id=user, image_base64="R0lGODlh"
                )
                self.assertIs(result, BattleDeliveryState.CONFIRMED)
                bot.call_action.assert_awaited_once_with(
                    action,
                    **{
                        key: int(group or user),
                        "message": [
                            {"type": "image", "data": {"file": "base64://R0lGODlh"}}
                        ],
                        "timeout": 120000,
                    },
                )

    async def test_delayed_ack_is_awaited_without_second_submission(self):
        started, release = asyncio.Event(), asyncio.Event()
        bot = type("Bot", (), {})()

        async def call(*args, **kwargs):
            started.set()
            await release.wait()
            return {"message_id": 17}

        bot.call_action = AsyncMock(side_effect=call)
        task = asyncio.create_task(
            send_qq_battle_image(
                bot, group_id="", user_id="123456", image_base64="test"
            )
        )
        await asyncio.wait_for(started.wait(), 1)
        self.assertFalse(task.done())
        release.set()
        self.assertIs(await task, BattleDeliveryState.CONFIRMED)
        bot.call_action.assert_awaited_once()

    async def test_timeout_or_lost_response_is_unknown_without_retry(self):
        errors = [
            ActionFailed(
                {
                    "retcode": 1200,
                    "message": "Timeout: NTEvent serviceAndMethod:NodeIKernelMsgService/sendMsg",
                }
            ),
            NetworkError("WebSocket API call timeout"),
            TimeoutError(),
            RuntimeError("lost response"),
        ]
        for error in errors:
            with self.subTest(error=type(error).__name__):
                bot = type("Bot", (), {})()
                bot.call_action = AsyncMock(side_effect=error)
                self.assertIs(
                    await send_qq_battle_image(
                        bot, group_id="", user_id="123456", image_base64="test"
                    ),
                    BattleDeliveryState.UNKNOWN,
                )
                bot.call_action.assert_awaited_once()

    async def test_explicit_qq_rejection_allows_fallback(self):
        bot = type("Bot", (), {})()
        bot.call_action = AsyncMock(
            side_effect=ActionFailed(
                {
                    "retcode": 1200,
                    "message": "EventChecker Failed: rich media transfer failed",
                }
            )
        )
        self.assertIs(
            await send_qq_battle_image(
                bot, group_id="", user_id="123456", image_base64="test"
            ),
            BattleDeliveryState.FAILED,
        )
        bot.call_action.assert_awaited_once()

    async def test_missing_confirmation_id_remains_unknown(self):
        for response in [None, {}, {"message_id": 0}, {"message_id": True}]:
            bot = type("Bot", (), {})()
            bot.call_action = AsyncMock(return_value=response)
            self.assertIs(
                await send_qq_battle_image(
                    bot, group_id="", user_id="123456", image_base64="test"
                ),
                BattleDeliveryState.UNKNOWN,
            )

    async def test_invalid_recipient_is_rejected_before_dispatch(self):
        bot = type("Bot", (), {})()
        bot.call_action = AsyncMock()
        with self.assertRaises(ValueError):
            await send_qq_battle_image(
                bot, group_id="", user_id="not-numeric", image_base64="test"
            )
        bot.call_action.assert_not_awaited()

    async def test_cancellation_is_not_converted_to_fallback(self):
        bot = type("Bot", (), {})()
        bot.call_action = AsyncMock(side_effect=asyncio.CancelledError)
        with self.assertRaises(asyncio.CancelledError):
            await send_qq_battle_image(
                bot, group_id="", user_id="123456", image_base64="test"
            )


class RenderDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_qq_dispatch_occurs_once_even_if_confirmed_metrics_fail(self):
        for outcome, metrics_error in [
            (BattleDeliveryState.CONFIRMED, None),
            (BattleDeliveryState.CONFIRMED, RuntimeError("fixture metrics failure")),
            (BattleDeliveryState.FAILED, None),
            (BattleDeliveryState.UNKNOWN, None),
        ]:
            with self.subTest(outcome=outcome, metrics_error=metrics_error):
                image = Mock()
                image.convert_to_base64 = AsyncMock(return_value="fixture")
                components = Mock()
                components.Image.fromFileSystem.return_value = image
                base_event = Mock()
                base_event.send = AsyncMock(side_effect=metrics_error)
                dispatch = AsyncMock(return_value=outcome)
                event = Mock()
                event.get_platform_name.return_value = "aiocqhttp"
                event.get_group_id.return_value = ""
                event.get_sender_id.return_value = "123456"
                event.make_result.return_value.chain = []
                bot = Mock()
                bot._send_image_path_safe = AsyncMock()
                method = load_method(
                    "_send_battle_image_path_safe",
                    AstrMessageEvent=base_event,
                    send_qq_battle_image=dispatch,
                )
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / "fixture.gif"
                    path.write_bytes(b"GIF89a")
                    with patch.dict(
                        sys.modules, {"astrbot.api.message_components": components}
                    ):
                        self.assertIs(await method(bot, event, str(path)), outcome)
                dispatch.assert_awaited_once_with(
                    event.bot, group_id="", user_id="123456", image_base64="fixture"
                )
                self.assertEqual(
                    base_event.send.await_count,
                    int(outcome is BattleDeliveryState.CONFIRMED),
                )
                bot._send_image_path_safe.assert_not_awaited()

    async def run_render(self, outcome=None, error=None):
        method = load_method("_render_and_send_battle")
        bot = type("Bot", (), {})()
        bot._render_slots = asyncio.Semaphore(2)
        bot._send_battle_image_path_safe = AsyncMock(
            return_value=outcome, side_effect=error
        )
        bot._send_text_safe = AsyncMock(return_value=True)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.gif"
            path.write_bytes(b"GIF89a")
            result = await method(bot, object(), lambda: str(path))
            self.assertFalse(path.exists())
        return bot, result

    async def test_confirmed_send_has_no_pending_notice(self):
        bot, outcome = await self.run_render(BattleDeliveryState.CONFIRMED)
        self.assertIs(outcome, BattleDeliveryState.CONFIRMED)
        bot._send_text_safe.assert_not_awaited()
        bot._send_battle_image_path_safe.assert_awaited_once()

    async def test_unknown_send_emits_one_notice_and_preserves_uncertainty(self):
        bot, outcome = await self.run_render(BattleDeliveryState.UNKNOWN)
        self.assertIs(outcome, BattleDeliveryState.UNKNOWN)
        bot._send_text_safe.assert_awaited_once()
        bot._send_battle_image_path_safe.assert_awaited_once()

    async def test_outer_timeout_does_not_turn_into_definite_failure(self):
        bot, outcome = await self.run_render(error=TimeoutError())
        self.assertIs(outcome, BattleDeliveryState.UNKNOWN)
        bot._send_text_safe.assert_awaited_once()

    async def test_definite_rejection_remains_failed(self):
        bot, outcome = await self.run_render(BattleDeliveryState.FAILED)
        self.assertIs(outcome, BattleDeliveryState.FAILED)
        bot._send_text_safe.assert_not_awaited()

    async def test_renderer_failure_never_submits_image(self):
        bot = type("Bot", (), {})()
        bot._render_slots = asyncio.Semaphore(2)
        bot._send_battle_image_path_safe = AsyncMock()
        bot._send_text_safe = AsyncMock()

        def broken():
            raise RuntimeError("fixture render failure")

        result = await load_method("_render_and_send_battle")(bot, object(), broken)
        self.assertIs(result, BattleDeliveryState.FAILED)
        bot._send_battle_image_path_safe.assert_not_awaited()

    def test_timeout_order_fits_existing_180_second_adapter_budget(self):
        self.assertLess(QQ_GIF_TIMEOUT_MS / 1000, BATTLE_SEND_TIMEOUT_SECONDS)
        self.assertLess(BATTLE_SEND_TIMEOUT_SECONDS, 180)
