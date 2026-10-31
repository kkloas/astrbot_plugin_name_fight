import ast
import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock


def load_start_battle():
    tree = ast.parse(Path(__file__).with_name("main.py").read_text(encoding="utf-8"))
    node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_start_battle"
    )
    state = SimpleNamespace(FAILED="failed", UNKNOWN="unknown")
    namespace = {
        "Any": Any,
        "AstrMessageEvent": object,
        "asyncio": asyncio,
        "battle_overview_line": lambda *_: "overview",
        "BattleDeliveryState": state,
    }
    exec(
        compile(ast.Module(body=[node], type_ignores=[]), "main.py", "exec"), namespace
    )
    return namespace["_start_battle"]


class GroupBattleTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_group_blocked_and_other_group_can_battle(self):
        started = asyncio.Event()
        release = asyncio.Event()
        calls = []

        async def send_animation(event, *_):
            calls.append(event.group)
            started.set()
            await release.wait()
            return "confirmed"

        bot = Mock()
        bot._battling_groups = set()
        bot.broadcast_delay = 0
        bot._send_battle_animation_safe = send_animation
        bot.engine.battle_with_events.return_value = {"logs": [], "winner": "A"}
        bot.repo.record_group_battle.return_value = {
            "attacker": {"name": "A", "delta": 1, "before": 1, "after": 2},
            "defender": {"name": "B", "delta": -1, "before": 1, "after": 0},
        }

        def event(group):
            obj = Mock(group=group)
            obj.send = AsyncMock()
            obj.plain_result = str
            return obj

        method = load_start_battle()
        args = ({"name": "A"}, {"name": "B"}, "start")
        first = asyncio.create_task(method(bot, event("g1"), "g1", *args))
        await started.wait()
        duplicate = event("g1")
        await method(bot, duplicate, "g1", *args)
        self.assertIn("正在进行", duplicate.send.await_args.args[0])
        second = asyncio.create_task(method(bot, event("g2"), "g2", *args))
        for _ in range(20):
            if len(calls) == 2:
                break
            await asyncio.sleep(0)
        self.assertEqual(calls, ["g1", "g2"])
        release.set()
        await asyncio.gather(first, second)
        self.assertEqual(bot._battling_groups, set())


if __name__ == "__main__":
    unittest.main()
