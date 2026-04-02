# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import re
import time
from copy import deepcopy
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

try:
    from .database import FighterRepository, MAX_FIGHTERS_PER_USER
    from .engine import CombatEngine
    from .text_resources import (
        HELP_LINES,
        battle_overview_line,
        compact_battle_logs,
        fighter_summary_lines,
        join_lines,
        leaderboard_message,
        team3_leaderboard_message,
        pending_replace_message,
        roster_message,
    )
except ImportError:
    from database import FighterRepository, MAX_FIGHTERS_PER_USER
    from engine import CombatEngine
    from text_resources import (
        HELP_LINES,
        battle_overview_line,
        compact_battle_logs,
        fighter_summary_lines,
        join_lines,
        leaderboard_message,
        team3_leaderboard_message,
        pending_replace_message,
        roster_message,
    )

PENDING_CREATE_TIMEOUT = 60.0
CHALLENGE_TIMEOUT = 120.0


def _safe_call(obj: Any, name: str) -> Any:
    method = getattr(obj, name, None)
    if callable(method):
        try:
            return method()
        except Exception:
            return None
    return None


def _dig_value(root: Any, keys: tuple[str, ...], depth: int = 0, seen: set[int] | None = None) -> Any:
    if root is None or depth > 3:
        return None
    if seen is None:
        seen = set()
    root_id = id(root)
    if root_id in seen:
        return None
    seen.add(root_id)
    if isinstance(root, dict):
        for key in keys:
            value = root.get(key)
            if value not in (None, ''):
                return value
        for value in root.values():
            found = _dig_value(value, keys, depth + 1, seen)
            if found not in (None, ''):
                return found
        return None
    for key in keys:
        value = getattr(root, key, None)
        if value not in (None, ''):
            return value
    for name in ('sender', 'message_obj', 'raw_message', 'platform_event', 'message_event', 'session', 'author'):
        value = getattr(root, name, None)
        found = _dig_value(value, keys, depth + 1, seen)
        if found not in (None, ''):
            return found
    return None


def _extract_numeric_tail(value: Any) -> str | None:
    if value in (None, ''):
        return None
    matches = re.findall(r'\d{5,}', str(value))
    return matches[-1] if matches else None


def extract_user_id(event: AstrMessageEvent) -> str:
    direct_keys = ('sender_id', 'user_id', 'from_user_id', 'qq', 'uid', 'userId', 'senderId')
    for root in (
        event,
        getattr(event, 'sender', None),
        _safe_call(event, 'get_sender'),
        _safe_call(event, 'get_platform_event'),
        _safe_call(event, 'get_message_obj'),
        getattr(event, 'message_obj', None),
        getattr(event, 'raw_message', None),
    ):
        value = _dig_value(root, direct_keys)
        if value not in (None, ''):
            return str(value)
    for name in ('get_sender_id', 'get_user_id'):
        value = _safe_call(event, name)
        if value not in (None, ''):
            return str(value)
    for attr in ('session_id', 'sid', 'conversation_id', 'session', 'unified_msg_origin'):
        numeric = _extract_numeric_tail(getattr(event, attr, None))
        if numeric is not None:
            return numeric
    raise RuntimeError('\u65e0\u6cd5\u8bc6\u522b\u5f53\u524d\u7528\u6237ID')


def extract_user_label(event: AstrMessageEvent) -> str:
    label_keys = ('sender_name', 'nickname', 'user_name', 'card', 'name', 'remark')
    for root in (
        event,
        getattr(event, 'sender', None),
        _safe_call(event, 'get_sender'),
        _safe_call(event, 'get_platform_event'),
        _safe_call(event, 'get_message_obj'),
        getattr(event, 'message_obj', None),
        getattr(event, 'raw_message', None),
    ):
        value = _dig_value(root, label_keys)
        if value not in (None, ''):
            return str(value)
    return extract_user_id(event)


def extract_group_id(event: AstrMessageEvent) -> str:
    group_keys = ('group_id', 'room_id', 'channel_id', 'groupId')
    for root in (
        event,
        getattr(event, 'message_obj', None),
        getattr(event, 'raw_message', None),
        _safe_call(event, 'get_platform_event'),
        _safe_call(event, 'get_message_obj'),
    ):
        value = _dig_value(root, group_keys)
        if value not in (None, ''):
            return str(value)
    for attr in ('session_id', 'sid', 'conversation_id', 'session', 'unified_msg_origin'):
        numeric = _extract_numeric_tail(getattr(event, attr, None))
        if numeric is not None:
            return numeric
    return 'default_group'


def _walk_nested(root: Any, depth: int = 0, seen: set[int] | None = None):
    if root is None or depth > 6:
        return
    if seen is None:
        seen = set()
    root_id = id(root)
    if root_id in seen:
        return
    seen.add(root_id)
    yield root
    if isinstance(root, dict):
        for value in root.values():
            yield from _walk_nested(value, depth + 1, seen)
        return
    if isinstance(root, (list, tuple, set)):
        for value in root:
            yield from _walk_nested(value, depth + 1, seen)
        return
    for name in ('message', 'messages', 'message_obj', 'raw_message', 'data', 'segments', 'content'):
        value = getattr(root, name, None)
        if value is not None:
            yield from _walk_nested(value, depth + 1, seen)


def extract_mentioned_user_id(event: AstrMessageEvent) -> str | None:
    roots = (
        event,
        getattr(event, 'message_obj', None),
        getattr(event, 'raw_message', None),
        _safe_call(event, 'get_platform_event'),
        _safe_call(event, 'get_message_obj'),
    )
    for root in roots:
        for node in _walk_nested(root):
            if isinstance(node, dict) and str(node.get('type', '')).lower() == 'at':
                data = node.get('data', {}) if isinstance(node.get('data', {}), dict) else {}
                value = data.get('qq') or data.get('user_id') or data.get('id') or data.get('target')
                numeric = _extract_numeric_tail(value) or (str(value) if value not in (None, '') else None)
                if numeric:
                    return numeric
    message_text = str(getattr(event, 'message_str', '') or '')
    match = re.search(r'\[CQ:at,qq=(\d{5,})\]', message_text)
    if match:
        return match.group(1)
    return None


@register('astrbot_plugin_name_fight', 'Codex', '\u6587\u5b57\u683c\u6597\u5f15\u64ce', '1.2.1')
class Main(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context)
        self.config = config or {}
        self.repo = FighterRepository()
        self.engine = CombatEngine()
        self.broadcast_delay = float(self.config.get('broadcast_delay', 1.6))
        self.is_battling = False
        self.pending_challenges: dict[str, dict[str, Any]] = {}
        self.pending_creations: dict[str, dict[str, Any]] = {}
        self.pending_team3_challenges: dict[str, dict[str, Any]] = {}
        logger.info('[name_fight] plugin loaded')

    def _consume_pending_creation(self, user_id: str) -> dict[str, Any] | None:
        pending = self.pending_creations.get(user_id)
        if pending is None:
            return None
        if pending['expires_at'] < time.monotonic():
            self.pending_creations.pop(user_id, None)
            return None
        return pending

    async def _require_user_id(self, event: AstrMessageEvent) -> str | None:
        try:
            return extract_user_id(event)
        except RuntimeError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return None

    async def _require_group_id(self, event: AstrMessageEvent) -> str | None:
        try:
            group_id = extract_group_id(event)
            self._remember_group_user_label(event, group_id)
            return group_id
        except RuntimeError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return None


    def _remember_group_user_label(self, event: AstrMessageEvent, group_id: str) -> None:
        try:
            user_id = extract_user_id(event)
            label = extract_user_label(event)
        except RuntimeError:
            return
        self.repo.set_group_user_label(group_id, user_id, label)

    def _challenge_key(self, group_id: str, defender_user_id: str) -> str:
        return f'{group_id}:{defender_user_id}'

    def _cleanup_expired_challenges(self) -> None:
        now = time.monotonic()
        expired_keys = [key for key, challenge in self.pending_challenges.items() if challenge.get('expires_at', 0.0) < now]
        for key in expired_keys:
            self.pending_challenges.pop(key, None)
        expired_team3_keys = [key for key, challenge in self.pending_team3_challenges.items() if challenge.get('expires_at', 0.0) < now]
        for key in expired_team3_keys:
            self.pending_team3_challenges.pop(key, None)

    def _consume_pending_challenge(self, group_id: str, defender_user_id: str) -> dict[str, Any] | None:
        self._cleanup_expired_challenges()
        return self.pending_challenges.pop(self._challenge_key(group_id, defender_user_id), None)

    def _consume_pending_team3_challenge(self, group_id: str, defender_user_id: str) -> dict[str, Any] | None:
        self._cleanup_expired_challenges()
        return self.pending_team3_challenges.pop(self._challenge_key(group_id, defender_user_id), None)

    def _format_team3_names(self, fighters: list[dict[str, Any]]) -> str:
        return ' / '.join(fighter['name'] for fighter in fighters)

    def _build_team3_status_lines(self, user_id: str) -> list[str]:
        roster = self.repo.get_user_fighters(user_id)
        lines = ['【3v3 阵容】']
        if len(roster) < MAX_FIGHTERS_PER_USER:
            lines.append(f'你当前只有 {len(roster)}/{MAX_FIGHTERS_PER_USER} 个角色，暂时无法参加 3v3。')
            for fighter in roster:
                lines.append(f'{fighter["slot_index"]}号位: {fighter["name"]} | {fighter["martial_art"]["name"]}')
            lines.append('请先补满 3 个角色后，再使用 /teamorder 调整顺序。')
            return lines
        fighters_by_slot = {int(fighter['slot_index']): fighter for fighter in roster}
        order = self.repo.get_user_team3_order(user_id)
        lines.append(f'当前顺序: {order[0]} -> {order[1]} -> {order[2]}')
        for slot in range(1, MAX_FIGHTERS_PER_USER + 1):
            fighter = fighters_by_slot.get(slot)
            if fighter is None:
                lines.append(f'{slot}号位: 空缺')
            else:
                lines.append(f'{slot}号位: {fighter["name"]} | {fighter["martial_art"]["name"]}')
        team = [fighters_by_slot[slot] for slot in order if slot in fighters_by_slot]
        lines.append(f'出战阵容: {self._format_team3_names(team)}')
        return lines

    def _get_ready_team3_fighters(self, user_id: str) -> list[dict[str, Any]]:
        team = self.repo.get_user_team3_fighters(user_id)
        if len(team) < MAX_FIGHTERS_PER_USER:
            raise ValueError('你当前角色未满 3 个，暂时无法参加 3v3。')
        return team

    def _clone_fighter_with_hp(self, fighter: dict[str, Any], hp: int) -> dict[str, Any]:
        clone = deepcopy(fighter)
        clone['stats'] = dict(clone['stats'])
        clone['stats']['hp'] = max(1, int(hp))
        return clone

    def _is_turn_log_line(self, line: str) -> bool:
        return line.startswith('【第') and '手】' in line

    def _chunk_team3_battle_logs(self, duel_no: int, compacted_logs: list[str], chunk_size: int = 5) -> list[str]:
        if not compacted_logs:
            return []
        intro_lines: list[str] = []
        turn_lines: list[str] = []
        outcome_lines: list[str] = []
        for line in compacted_logs:
            if self._is_turn_log_line(line):
                turn_lines.append(line)
            elif turn_lines:
                outcome_lines.append(line)
            else:
                intro_lines.append(line)

        lines = list(intro_lines)
        if turn_lines:
            for start_index in range(0, len(turn_lines), chunk_size):
                end_index = start_index + chunk_size
                lines.extend(turn_lines[start_index:end_index])
        lines.extend(outcome_lines)
        return lines

    def _battle_team3_with_result(
        self,
        attacker_label: str,
        attacker_team: list[dict[str, Any]],
        defender_label: str,
        defender_team: list[dict[str, Any]],
    ) -> tuple[list[str], str | None]:
        lines = [
            f'【3v3阵容】{attacker_label}: {self._format_team3_names(attacker_team)} | {defender_label}: {self._format_team3_names(defender_team)}'
        ]
        attacker_index = 0
        defender_index = 0
        attacker_hp = int(attacker_team[0]['stats']['hp'])
        defender_hp = int(defender_team[0]['stats']['hp'])
        duel_no = 1

        while attacker_index < len(attacker_team) and defender_index < len(defender_team):
            attacker_fighter = self._clone_fighter_with_hp(attacker_team[attacker_index], attacker_hp)
            defender_fighter = self._clone_fighter_with_hp(defender_team[defender_index], defender_hp)
            logs, winner_name, state = self.engine.battle_with_state(attacker_fighter, defender_fighter)
            attacker_name = attacker_team[attacker_index]['name']
            defender_name = defender_team[defender_index]['name']
            lines.append(f'【第{duel_no}阵】{attacker_label}·{attacker_name} vs {defender_label}·{defender_name}')
            lines.append(battle_overview_line(attacker_fighter, defender_fighter))
            lines.extend(self._chunk_team3_battle_logs(duel_no, compact_battle_logs(logs)))

            if winner_name == attacker_name:
                attacker_hp = int(state['fighter_a_hp'])
                lines.append(
                    f'【第{duel_no}阵结果】{attacker_name} 击败 {defender_name}，剩余 '
                    f'{attacker_hp}/{state["fighter_a_max_hp"]} 气血。'
                )
                defender_index += 1
                if defender_index < len(defender_team):
                    defender_hp = int(defender_team[defender_index]['stats']['hp'])
                    next_name = defender_team[defender_index]['name']
                    lines.append(f'【阵间承接】{attacker_name} 继续出战，迎战 {next_name}。')
            elif winner_name == defender_name:
                defender_hp = int(state['fighter_b_hp'])
                lines.append(
                    f'【第{duel_no}阵结果】{defender_name} 击败 {attacker_name}，剩余 '
                    f'{defender_hp}/{state["fighter_b_max_hp"]} 气血。'
                )
                attacker_index += 1
                if attacker_index < len(attacker_team):
                    attacker_hp = int(attacker_team[attacker_index]['stats']['hp'])
                    next_name = attacker_team[attacker_index]['name']
                    lines.append(f'【阵间承接】{defender_name} 继续出战，迎战 {next_name}。')
            else:
                lines.append(f'【第{duel_no}阵结果】{attacker_name} 与 {defender_name} 同归于尽，双方各折一阵。')
                attacker_index += 1
                defender_index += 1
                if attacker_index < len(attacker_team):
                    attacker_hp = int(attacker_team[attacker_index]['stats']['hp'])
                if defender_index < len(defender_team):
                    defender_hp = int(defender_team[defender_index]['stats']['hp'])
            duel_no += 1

        if attacker_index >= len(attacker_team) and defender_index >= len(defender_team):
            lines.append('【3v3结果】双方三阵全灭，本场以平局告终。')
            return lines, None
        if defender_index >= len(defender_team):
            lines.append(f'【3v3结果】{attacker_label} 三阵连战胜出。')
            return lines, 'attacker'
        lines.append(f'【3v3结果】{defender_label} 三阵连战胜出。')
        return lines, 'defender'

    async def _start_team3_battle(
        self,
        event: AstrMessageEvent,
        group_id: str,
        attacker_user_id: str,
        attacker_label: str,
        attacker_team: list[dict[str, Any]],
        defender_user_id: str,
        defender_label: str,
        defender_team: list[dict[str, Any]],
        opener: str,
    ) -> None:
        if self.is_battling:
            await event.send(event.plain_result('当前已有对决正在播报，请稍后再试。'))
            event.stop_event()
            return
        self.is_battling = True
        try:
            await event.send(event.plain_result(opener))
            await asyncio.sleep(self.broadcast_delay)
            lines, winner_side = self._battle_team3_with_result(attacker_label, attacker_team, defender_label, defender_team)
            await self._send_lines(event, lines)
            winner_user_id = None
            if winner_side == 'attacker':
                winner_user_id = attacker_user_id
            elif winner_side == 'defender':
                winner_user_id = defender_user_id
            rating_change = self.repo.record_group_team3_battle(
                group_id,
                attacker_user_id,
                attacker_label,
                defender_user_id,
                defender_label,
                winner_user_id,
            )
            await asyncio.sleep(self.broadcast_delay)
            await event.send(event.plain_result(
                f'本场 3v3 巅峰分变动: '
                f'{rating_change["attacker"]["name"]} {rating_change["attacker"]["delta"]:+.2f} '
                f'({rating_change["attacker"]["before"]:.2f} -> {rating_change["attacker"]["after"]:.2f}) | '
                f'{rating_change["defender"]["name"]} {rating_change["defender"]["delta"]:+.2f} '
                f'({rating_change["defender"]["before"]:.2f} -> {rating_change["defender"]["after"]:.2f})'
            ))
        finally:
            self.is_battling = False
            event.stop_event()

    async def _send_text_safe(self, event: AstrMessageEvent, text: str) -> bool:
        try:
            await event.send(event.plain_result(text))
            return True
        except Exception as exc:
            logger.warning(f'[name_fight] send text failed, retry once: {exc!r}')
            await asyncio.sleep(min(0.5, self.broadcast_delay))
            try:
                await event.send(event.plain_result(text))
                return True
            except Exception as retry_exc:
                logger.warning(f'[name_fight] send text dropped after retry: {retry_exc!r}')
                return False

    async def _send_lines(self, event: AstrMessageEvent, lines: list[str]) -> None:
        for index, line in enumerate(lines):
            sent = await self._send_text_safe(event, line)
            if not sent:
                continue
            if index + 1 < len(lines):
                await asyncio.sleep(self.broadcast_delay)

    async def _start_battle(self, event: AstrMessageEvent, group_id: str, attacker: dict[str, Any], defender: dict[str, Any], opener: str) -> None:
        if self.is_battling:
            await event.send(event.plain_result('\u5f53\u524d\u5df2\u6709\u5bf9\u51b3\u6b63\u5728\u64ad\u62a5\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002'))
            event.stop_event()
            return
        self.is_battling = True
        try:
            await event.send(event.plain_result(opener))
            await asyncio.sleep(self.broadcast_delay)
            await event.send(event.plain_result(battle_overview_line(attacker, defender)))
            await asyncio.sleep(self.broadcast_delay)
            logs, winner_name = self.engine.battle_with_result(attacker, defender)
            await self._send_lines(event, compact_battle_logs(logs))
            rating_change = self.repo.record_group_battle(group_id, attacker['name'], defender['name'], winner_name)
            attacker_change = rating_change['attacker']
            defender_change = rating_change['defender']
            await asyncio.sleep(self.broadcast_delay)
            await event.send(event.plain_result(
                f'\u672c\u573a\u5dc5\u5cf0\u5206\u53d8\u52a8: '
                f'{attacker_change["name"]} {attacker_change["delta"]:+.2f} '
                f'({attacker_change["before"]:.2f} -> {attacker_change["after"]:.2f}) | '
                f'{defender_change["name"]} {defender_change["delta"]:+.2f} '
                f'({defender_change["before"]:.2f} -> {defender_change["after"]:.2f})'
            ))
        finally:
            self.is_battling = False
            event.stop_event()

    @filter.command('fhelp')
    async def help_command(self, event: AstrMessageEvent):
        await event.send(event.plain_result(join_lines(HELP_LINES)))
        event.stop_event()

    @filter.command('create')
    async def create_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip():
            await event.send(event.plain_result('\u7528\u6cd5: /create \u89d2\u8272\u540d'))
            event.stop_event()
            return
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        fighter_name = parts[1].strip()
        self.pending_creations.pop(user_id, None)
        roster = self.repo.get_user_fighters(user_id)
        if len(roster) >= MAX_FIGHTERS_PER_USER:
            try:
                fighter = self.repo.generate_preview_fighter(fighter_name)
            except ValueError as exc:
                await event.send(event.plain_result(str(exc)))
                event.stop_event()
                return
            self.pending_creations[user_id] = {
                'fighter': fighter,
                'expires_at': time.monotonic() + PENDING_CREATE_TIMEOUT,
            }
            lines = fighter_summary_lines(fighter, True)
            lines.append(pending_replace_message(fighter_name, roster, int(PENDING_CREATE_TIMEOUT)))
            await self._send_text_safe(event, join_lines(lines))
            event.stop_event()
            return
        try:
            fighter = self.repo.create_fighter_for_user(user_id, fighter_name)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        await self._send_text_safe(event, join_lines(fighter_summary_lines(fighter, True)))
        event.stop_event()

    @filter.command('choose')
    async def choose_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip().isdigit():
            await event.send(event.plain_result('\u7528\u6cd5: /choose \u5e8f\u53f7'))
            event.stop_event()
            return
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        pending = self._consume_pending_creation(user_id)
        if pending is None:
            await event.send(event.plain_result('\u4f60\u5f53\u524d\u6ca1\u6709\u5f85\u786e\u8ba4\u7684\u5019\u9009\u89d2\u8272\u3002'))
            event.stop_event()
            return
        slot_index = int(parts[1].strip())
        if slot_index < 1 or slot_index > MAX_FIGHTERS_PER_USER:
            await event.send(event.plain_result(f'\u5e8f\u53f7\u8303\u56f4\u53ea\u80fd\u5728 1 \u5230 {MAX_FIGHTERS_PER_USER} \u4e4b\u95f4\u3002'))
            event.stop_event()
            return
        try:
            old_name, fighter = self.repo.replace_fighter_for_user(user_id, slot_index, prepared_fighter=pending['fighter'])
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        self.pending_creations.pop(user_id, None)
        lines = [
            f'\u3010\u89d2\u8272\u66f4\u66ff\u3011\u5df2\u7528\u3010{fighter["name"]}\u3011\u9876\u66ff\u3010{old_name}\u3011\u5165\u5217\uff0c\u5e76\u81ea\u52a8\u8bbe\u4e3a\u5f53\u524d\u51fa\u6218\u89d2\u8272\u3002',
            *fighter_summary_lines(fighter, False),
        ]
        await self._send_text_safe(event, join_lines(lines))
        event.stop_event()

    @filter.command('roster')
    async def roster_command(self, event: AstrMessageEvent):
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        fighters = self.repo.get_user_fighters(user_id)
        await event.send(event.plain_result(roster_message(fighters, MAX_FIGHTERS_PER_USER)))
        event.stop_event()

    @filter.command('use')
    async def use_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip():
            await event.send(event.plain_result('\u7528\u6cd5: /use \u89d2\u8272\u540d'))
            event.stop_event()
            return
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        fighter_name = parts[1].strip()
        try:
            fighter = self.repo.set_active_fighter(user_id, fighter_name)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        await event.send(event.plain_result(f'\u5f53\u524d\u51fa\u6218\u89d2\u8272\u5df2\u5207\u6362\u4e3a\u3010{fighter["name"]}\u3011\u3002'))
        event.stop_event()

    @filter.command('profile')
    async def profile_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        if len(parts) == 1:
            fighters = self.repo.get_user_fighters(user_id)
            await event.send(event.plain_result(roster_message(fighters, MAX_FIGHTERS_PER_USER)))
            event.stop_event()
            return
        fighter_name = parts[1].strip()
        fighter = self.repo.get_fighter_by_name(fighter_name)
        if fighter is None or not self.repo.user_owns_fighter(user_id, fighter_name):
            await event.send(event.plain_result('\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272\u3002'))
            event.stop_event()
            return
        await self._send_text_safe(event, join_lines(fighter_summary_lines(fighter, False)))
        event.stop_event()

    @filter.command('c', alias={'challenge'})
    async def challenge_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip():
            await event.send(event.plain_result('\u7528\u6cd5: /c \u76ee\u6807\u89d2\u8272\u540d'))
            event.stop_event()
            return
        challenger_user_id = await self._require_user_id(event)
        if challenger_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenger_label = extract_user_label(event)
        challenger = self.repo.get_active_fighter(challenger_user_id)
        if challenger is None:
            await event.send(event.plain_result('\u4f60\u8fd8\u6ca1\u6709\u53ef\u51fa\u6218\u89d2\u8272\uff0c\u8bf7\u5148\u521b\u5efa\u5e76\u9009\u62e9\u89d2\u8272\u3002'))
            event.stop_event()
            return
        target_name = parts[1].strip()
        defender = self.repo.get_fighter_by_name(target_name)
        if defender is None:
            await event.send(event.plain_result('\u76ee\u6807\u89d2\u8272\u4e0d\u5b58\u5728\uff0c\u65e0\u6cd5\u53d1\u8d77\u6311\u6218\u3002'))
            event.stop_event()
            return
        defender_user_id = self.repo.get_owner_user_id_by_fighter_name(target_name)
        if defender_user_id is None:
            await event.send(event.plain_result('\u76ee\u6807\u89d2\u8272\u672a\u7ed1\u5b9a\u62e5\u6709\u8005\uff0c\u6682\u65f6\u65e0\u6cd5\u6311\u6218\u3002'))
            event.stop_event()
            return
        if defender_user_id == challenger_user_id:
            await event.send(event.plain_result('\u4e0d\u80fd\u6311\u6218\u81ea\u5df1\u7684\u89d2\u8272\u3002'))
            event.stop_event()
            return
        self._cleanup_expired_challenges()
        challenge_key = self._challenge_key(group_id, defender_user_id)
        self.pending_challenges[challenge_key] = {
            'group_id': group_id,
            'challenger_user_id': challenger_user_id,
            'challenger_label': challenger_label,
            'challenger_fighter_name': challenger['name'],
            'defender_fighter_name': defender['name'],
            'expires_at': time.monotonic() + CHALLENGE_TIMEOUT,
        }
        await event.send(event.plain_result(
            f'\u6311\u6218\u5df2\u53d1\u51fa\u3002\u3010{challenger["name"]}\u3011\u5411\u3010{defender["name"]}\u3011\u4e0b\u4e86\u6218\u4e66\u3002\u8bf7\u5bf9\u65b9\u4f7f\u7528 /a \u63a5\u6218\uff0c\u6216\u7528 /r \u62d2\u7edd\u3002'
        ))
        event.stop_event()

    @filter.command('fc')
    async def force_challenge_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip():
            await event.send(event.plain_result('\u7528\u6cd5: /fc \u76ee\u6807\u89d2\u8272\u540d'))
            event.stop_event()
            return
        challenger_user_id = await self._require_user_id(event)
        if challenger_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenger_label = extract_user_label(event)
        challenger = self.repo.get_active_fighter(challenger_user_id)
        if challenger is None:
            await event.send(event.plain_result('\u4f60\u8fd8\u6ca1\u6709\u53ef\u51fa\u6218\u89d2\u8272\uff0c\u8bf7\u5148\u521b\u5efa\u5e76\u9009\u62e9\u89d2\u8272\u3002'))
            event.stop_event()
            return
        target_name = parts[1].strip()
        defender = self.repo.get_fighter_by_name(target_name)
        if defender is None:
            await event.send(event.plain_result('\u76ee\u6807\u89d2\u8272\u4e0d\u5b58\u5728\uff0c\u65e0\u6cd5\u53d1\u8d77\u6311\u6218\u3002'))
            event.stop_event()
            return
        defender_user_id = self.repo.get_owner_user_id_by_fighter_name(target_name)
        if defender_user_id is None:
            await event.send(event.plain_result('\u76ee\u6807\u89d2\u8272\u672a\u7ed1\u5b9a\u62e5\u6709\u8005\uff0c\u6682\u65f6\u65e0\u6cd5\u6311\u6218\u3002'))
            event.stop_event()
            return
        if defender_user_id == challenger_user_id:
            await event.send(event.plain_result('\u4e0d\u80fd\u6311\u6218\u81ea\u5df1\u7684\u89d2\u8272\u3002'))
            event.stop_event()
            return
        opener = f'\u3010\u5bf9\u51b3\u5f00\u59cb\u3011{challenger_label} \u5f3a\u884c\u5411\u3010{defender["name"]}\u3011\u53d1\u8d77\u4e86\u6311\u6218\u3002'
        await self._start_battle(event, group_id, challenger, defender, opener)

    @filter.command('fc3')
    async def force_team3_challenge_command(self, event: AstrMessageEvent):
        challenger_user_id = await self._require_user_id(event)
        if challenger_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenger_label = extract_user_label(event)
        target_user_id = extract_mentioned_user_id(event)
        if target_user_id is None:
            await event.send(event.plain_result('\u7528\u6cd5: /fc3 @\u76ee\u6807\u73a9\u5bb6'))
            event.stop_event()
            return
        if target_user_id == challenger_user_id:
            await event.send(event.plain_result('\u4e0d\u80fd\u5411\u81ea\u5df1\u53d1\u8d77 3v3 \u5f3a\u5236\u5bf9\u51b3\u3002'))
            event.stop_event()
            return
        try:
            challenger_team = self._get_ready_team3_fighters(challenger_user_id)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        try:
            defender_team = self._get_ready_team3_fighters(target_user_id)
        except ValueError:
            await event.send(event.plain_result('\u76ee\u6807\u73a9\u5bb6\u5f53\u524d\u672a\u51d1\u9f50 3 \u4e2a\u89d2\u8272\uff0c\u6682\u65f6\u65e0\u6cd5\u53c2\u52a0 3v3\u3002'))
            event.stop_event()
            return
        opener = f'\u30103v3 \u5bf9\u51b3\u5f00\u59cb\u3011{challenger_label} \u5f3a\u884c\u5411\u5bf9\u65b9\u53d1\u8d77\u4e86 3v3 \u8fde\u6218\u3002'
        await self._start_team3_battle(
            event,
            group_id,
            challenger_user_id,
            challenger_label,
            challenger_team,
            target_user_id,
            self.repo.get_group_user_label(group_id, target_user_id) or f'QQ:{target_user_id}',
            defender_team,
            opener,
        )

    @filter.command('a', alias={'accept'})
    async def accept_command(self, event: AstrMessageEvent):
        defender_user_id = await self._require_user_id(event)
        if defender_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenge = self._consume_pending_challenge(group_id, defender_user_id)
        if challenge is None:
            await event.send(event.plain_result('\u5f53\u524d\u6ca1\u6709\u7b49\u5f85\u4f60\u56de\u5e94\u7684\u6311\u6218\u3002'))
            event.stop_event()
            return
        attacker = self.repo.get_fighter_by_name(challenge['challenger_fighter_name'])
        defender = self.repo.get_fighter_by_name(challenge['defender_fighter_name'])
        if attacker is None or defender is None:
            await event.send(event.plain_result('\u6311\u6218\u53cc\u65b9\u7684\u89d2\u8272\u4fe1\u606f\u4e0d\u5b8c\u6574\uff0c\u672c\u6b21\u6311\u6218\u5df2\u4f5c\u5e9f\u3002'))
            event.stop_event()
            return
        opener = f'\u3010\u5bf9\u51b3\u5f00\u59cb\u3011{challenge["challenger_label"]} \u5411\u3010{defender["name"]}\u3011\u53d1\u8d77\u7684\u6311\u6218\u5df2\u88ab\u63a5\u53d7\u3002'
        await self._start_battle(event, group_id, attacker, defender, opener)

    @filter.command('r', alias={'reject'})
    async def reject_command(self, event: AstrMessageEvent):
        defender_user_id = await self._require_user_id(event)
        if defender_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenge = self._consume_pending_challenge(group_id, defender_user_id)
        if challenge is None:
            await event.send(event.plain_result('\u5f53\u524d\u6ca1\u6709\u7b49\u5f85\u4f60\u62d2\u7edd\u7684\u6311\u6218\u3002'))
            event.stop_event()
            return
        await event.send(event.plain_result(
            f'\u3010\u6311\u6218\u4f5c\u5e9f\u3011\u4f60\u62d2\u7edd\u4e86\u3010{challenge["challenger_fighter_name"]}\u3011\u53d1\u8d77\u7684\u6311\u6218\u3002'
        ))
        event.stop_event()

    @filter.command('team3')
    async def team3_command(self, event: AstrMessageEvent):
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        await self._send_text_safe(event, join_lines(self._build_team3_status_lines(user_id)))
        event.stop_event()

    @filter.command('teamorder')
    async def teamorder_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split()
        if len(parts) != 4:
            await event.send(event.plain_result('用法: /teamorder 2 1 3'))
            event.stop_event()
            return
        try:
            order = [int(parts[1]), int(parts[2]), int(parts[3])]
        except ValueError:
            await event.send(event.plain_result('用法: /teamorder 2 1 3'))
            event.stop_event()
            return
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        roster = self.repo.get_user_fighters(user_id)
        if len(roster) < MAX_FIGHTERS_PER_USER:
            await event.send(event.plain_result('你当前角色未满 3 个，暂时无法设置 3v3 出战顺序。'))
            event.stop_event()
            return
        try:
            normalized = self.repo.set_user_team3_order(user_id, order)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        await event.send(event.plain_result(f'3v3 出战顺序已调整为: {normalized[0]} -> {normalized[1]} -> {normalized[2]}'))
        event.stop_event()

    @filter.command('t3')
    async def team3_challenge_command(self, event: AstrMessageEvent):
        challenger_user_id = await self._require_user_id(event)
        if challenger_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenger_label = extract_user_label(event)
        target_user_id = extract_mentioned_user_id(event)
        if target_user_id is None:
            await event.send(event.plain_result('用法: /t3 @目标玩家'))
            event.stop_event()
            return
        if target_user_id == challenger_user_id:
            await event.send(event.plain_result('不能向自己发起 3v3 挑战。'))
            event.stop_event()
            return
        try:
            challenger_team = self._get_ready_team3_fighters(challenger_user_id)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        try:
            defender_team = self._get_ready_team3_fighters(target_user_id)
        except ValueError:
            await event.send(event.plain_result('目标玩家当前未凑齐 3 个角色，暂时无法参加 3v3。'))
            event.stop_event()
            return
        challenge_key = self._challenge_key(group_id, target_user_id)
        self.pending_team3_challenges[challenge_key] = {
            'group_id': group_id,
            'challenger_user_id': challenger_user_id,
            'challenger_label': challenger_label,
            'expires_at': time.monotonic() + CHALLENGE_TIMEOUT,
        }
        await event.send(event.plain_result(
            f'【3v3挑战】{challenger_label} 已发起 3v3 连战挑战，请对方使用 /a3 接战，或用 /r3 拒绝。\n'
            f'挑战方阵容: {self._format_team3_names(challenger_team)}\n'
            f'应战方阵容: {self._format_team3_names(defender_team)}'
        ))
        event.stop_event()

    @filter.command('a3')
    async def team3_accept_command(self, event: AstrMessageEvent):
        defender_user_id = await self._require_user_id(event)
        if defender_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenge = self._consume_pending_team3_challenge(group_id, defender_user_id)
        if challenge is None:
            await event.send(event.plain_result('当前没有等待你回应的 3v3 挑战。'))
            event.stop_event()
            return
        attacker_label = str(challenge['challenger_label'])
        defender_label = extract_user_label(event)
        try:
            attacker_team = self._get_ready_team3_fighters(str(challenge['challenger_user_id']))
            defender_team = self._get_ready_team3_fighters(defender_user_id)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        opener = f'【3v3 对决开始】{attacker_label} 发起的 3v3 连战已被接受。'
        await self._start_team3_battle(
            event,
            group_id,
            str(challenge['challenger_user_id']),
            attacker_label,
            attacker_team,
            defender_user_id,
            defender_label,
            defender_team,
            opener,
        )

    @filter.command('r3')
    async def team3_reject_command(self, event: AstrMessageEvent):
        defender_user_id = await self._require_user_id(event)
        if defender_user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        challenge = self._consume_pending_team3_challenge(group_id, defender_user_id)
        if challenge is None:
            await event.send(event.plain_result('当前没有等待你拒绝的 3v3 挑战。'))
            event.stop_event()
            return
        await event.send(event.plain_result(f'【3v3挑战作废】你拒绝了 {challenge["challenger_label"]} 发起的 3v3 挑战。'))
        event.stop_event()

    @filter.command('rank3')
    async def team3_rank_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        entries = self.repo.get_group_team3_leaderboard(group_id, limit=10)
        await event.send(event.plain_result(team3_leaderboard_message(entries)))
        event.stop_event()

    @filter.command('rank')
    async def rank_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        entries = self.repo.get_group_leaderboard(group_id, limit=10)
        await event.send(event.plain_result(leaderboard_message(entries)))
        event.stop_event()

    @filter.regex(r'(?:[/!??])(?:fhelp|create|choose|roster|use|profile|c|challenge|fc|fc3|a|accept|r|reject|rank|team3|teamorder|t3|a3|r3|rank3)(?:\s|$)', priority=-10)
    async def regex_fallback(self, event: AstrMessageEvent):
        event.stop_event()
