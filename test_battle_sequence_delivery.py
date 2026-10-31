"""Exercise the Bot's actual delivery method without loading AstrBot or player data."""

import ast
import asyncio
import copy
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from battle_delivery import BattleDeliveryState


def load_delivery_method():
    tree = ast.parse(
        Path(__file__).with_name("main.py").read_text(encoding="utf-8-sig")
    )
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_send_battle_sequence_safe"
    )
    namespace = {
        "Any": Any,
        "AstrMessageEvent": object,
        "compact_battle_logs": list,
        "BattleDeliveryState": BattleDeliveryState,
    }
    exec(  # noqa: S102 - Compile only a trusted local method without plugin startup.
        compile(ast.Module(body=[method], type_ignores=[]), "main.py", "exec"),
        namespace,
    )
    return namespace[method.name]


class DeliveryHarness:
    deliver = load_delivery_method()


class BattleSequenceDeliveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.segments = [
            {
                "fighter_a": {"name": "A", "stats": {"hp": 100 - index * 20}},
                "fighter_b": {"name": f"B{index}", "stats": {"hp": 100}},
                "result": {"logs": [f"bout-{index}"], "events": [index]},
            }
            for index in range(3)
        ]
        self.bot = DeliveryHarness()
        self.bot._send_battle_animation_safe = AsyncMock(
            return_value=BattleDeliveryState.CONFIRMED
        )
        self.bot._send_lines = AsyncMock()
        self.event = type("Event", (), {"plain_result": staticmethod(str)})()
        self.event.send = AsyncMock()

    async def test_next_bout_waits_for_previous_gif_delivery_and_preserves_hp(self):
        original = copy.deepcopy(self.segments)
        started, release = asyncio.Event(), asyncio.Event()
        calls = []

        async def send_animation(event, a, b, result, label):
            calls.append((a, b, result))
            if len(calls) == 1:
                started.set()
                await release.wait()
            return BattleDeliveryState.CONFIRMED

        self.bot._send_battle_animation_safe.side_effect = send_animation
        task = asyncio.create_task(self.bot.deliver(self.event, self.segments))
        await asyncio.wait_for(started.wait(), 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.event.send.await_count, 1)
        release.set()
        self.assertIs(await asyncio.wait_for(task, 1), BattleDeliveryState.CONFIRMED)
        self.assertEqual([a["stats"]["hp"] for a, _, _ in calls], [100, 80, 60])
        self.assertEqual(self.segments, original)
        self.assertEqual(len(calls), 3)
        self.bot._send_lines.assert_not_awaited()

    async def test_failed_middle_bout_falls_back_once_and_continues(self):
        self.bot._send_battle_animation_safe.side_effect = [
            BattleDeliveryState.CONFIRMED,
            BattleDeliveryState.FAILED,
            BattleDeliveryState.CONFIRMED,
        ]
        self.assertIs(
            await self.bot.deliver(self.event, self.segments),
            BattleDeliveryState.CONFIRMED,
        )
        self.assertEqual(self.bot._send_battle_animation_safe.await_count, 3)
        self.bot._send_lines.assert_awaited_once_with(self.event, ["bout-1"])

    async def test_cancellation_stops_remaining_bouts(self):
        self.bot._send_battle_animation_safe.side_effect = asyncio.CancelledError
        with self.assertRaises(asyncio.CancelledError):
            await self.bot.deliver(self.event, self.segments)
        self.assertEqual(self.bot._send_battle_animation_safe.await_count, 1)
        self.bot._send_lines.assert_not_awaited()

    async def test_empty_sequence_uses_caller_fallback(self):
        self.assertIs(
            await self.bot.deliver(self.event, []), BattleDeliveryState.FAILED
        )
        self.event.send.assert_not_awaited()
        self.bot._send_battle_animation_safe.assert_not_awaited()

    async def test_unknown_middle_bout_stops_later_gifs_without_text_replay(self):
        self.bot._send_battle_animation_safe.side_effect = [
            BattleDeliveryState.CONFIRMED,
            BattleDeliveryState.UNKNOWN,
        ]
        self.assertIs(
            await self.bot.deliver(self.event, self.segments),
            BattleDeliveryState.UNKNOWN,
        )
        self.assertEqual(self.bot._send_battle_animation_safe.await_count, 2)
        self.assertEqual(self.event.send.await_count, 2)
        self.bot._send_lines.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
