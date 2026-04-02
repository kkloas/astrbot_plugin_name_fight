# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import re
import time
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


@register('astrbot_plugin_name_fight', 'Codex', '\u6587\u5b57\u683c\u6597\u5f15\u64ce', '1.2.0')
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
            return extract_group_id(event)
        except RuntimeError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return None

    def _challenge_key(self, group_id: str, defender_user_id: str) -> str:
        return f'{group_id}:{defender_user_id}'

    def _cleanup_expired_challenges(self) -> None:
        now = time.monotonic()
        expired_keys = [key for key, challenge in self.pending_challenges.items() if challenge.get('expires_at', 0.0) < now]
        for key in expired_keys:
            self.pending_challenges.pop(key, None)

    def _consume_pending_challenge(self, group_id: str, defender_user_id: str) -> dict[str, Any] | None:
        self._cleanup_expired_challenges()
        return self.pending_challenges.pop(self._challenge_key(group_id, defender_user_id), None)

    async def _send_lines(self, event: AstrMessageEvent, lines: list[str]) -> None:
        for index, line in enumerate(lines):
            try:
                await event.send(event.plain_result(line))
            except Exception as exc:
                logger.warning(f'[name_fight] send failed, retry once: {exc!r}')
                await asyncio.sleep(min(0.5, self.broadcast_delay))
                try:
                    await event.send(event.plain_result(line))
                except Exception as retry_exc:
                    logger.warning(f'[name_fight] send dropped after retry: {retry_exc!r}')
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
            await event.send(event.plain_result(join_lines(lines)))
            event.stop_event()
            return
        try:
            fighter = self.repo.create_fighter_for_user(user_id, fighter_name)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        await event.send(event.plain_result(join_lines(fighter_summary_lines(fighter, True))))
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
        await event.send(event.plain_result(join_lines(lines)))
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
        await event.send(event.plain_result(join_lines(fighter_summary_lines(fighter, False))))
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

    @filter.command('rank')
    async def rank_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        entries = self.repo.get_group_leaderboard(group_id, limit=10)
        await event.send(event.plain_result(leaderboard_message(entries)))
        event.stop_event()

    @filter.regex('(?:[/!\uff01\uff1f])(?:fhelp|create|choose|roster|use|profile|c|challenge|fc|a|accept|r|reject|rank)(?:\\s|$)', priority=-10)
    async def regex_fallback(self, event: AstrMessageEvent):
        event.stop_event()
