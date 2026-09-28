# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any


class PendingSwitch(Exception):
    def __init__(self, players: list[dict[str, Any]], enemies: list[dict[str, Any]],
                 duels: list[dict[str, Any]], current: int, reason: str, decision_count: int) -> None:
        self.players = deepcopy(players)
        self.enemies = deepcopy(enemies)
        self.duels = deepcopy(duels)
        self.current = current
        self.reason = reason
        self.decision_count = decision_count


class SwitchDecisions:
    def __init__(self, choices: list[int]) -> None:
        self.choices = choices
        self.cursor = 0

    def choose(self, players: list[dict[str, Any]], enemies: list[dict[str, Any]],
               duels: list[dict[str, Any]], current: int, reason: str) -> int:
        available = [index for index, entry in enumerate(players) if entry["hp"] > 0]
        if current not in available:
            raise ValueError("Current PVE fighter is not alive")
        if len(available) == 1:
            return current
        if self.cursor < len(self.choices):
            choice = self.choices[self.cursor]
            self.cursor += 1
            if type(choice) is not int or choice not in available:
                raise ValueError("请选择一名存活的出战角色")
            return choice
        raise PendingSwitch(players, enemies, duels, current, reason, self.cursor)
