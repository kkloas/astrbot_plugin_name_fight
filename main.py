# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import hashlib
import os
import re
import shutil
import time
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import urlopen

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

try:
    from .database import BATTLE_POINT_REWARDS, FighterRepository, MAX_FIGHTERS_PER_USER, TEAM3_TEAM_SIZE
    from .engine import CombatEngine
    from .text_resources import (
        GUIDE_LINES,
        HELP_LINES,
        bag_message,
        battle_overview_line,
        breakthrough_message,
        compact_battle_logs,
        feed_result_message,
        fighter_summary_lines,
        join_lines,
        leaderboard_message,
        loadout_reroll_message,
        martial_choice_message,
        martial_reroll_message,
        pending_replace_message,
        roster_message,
        shop_message,
        team3_leaderboard_message,
        wallet_message,
        boss_fight_result_message,
        boss_rank_message,
        boss_settlement_message,
        boss_status_message,
    )
except ImportError:
    from database import BATTLE_POINT_REWARDS, FighterRepository, MAX_FIGHTERS_PER_USER, TEAM3_TEAM_SIZE
    from engine import CombatEngine
    from text_resources import (
        GUIDE_LINES,
        HELP_LINES,
        bag_message,
        battle_overview_line,
        breakthrough_message,
        compact_battle_logs,
        feed_result_message,
        fighter_summary_lines,
        join_lines,
        leaderboard_message,
        loadout_reroll_message,
        martial_choice_message,
        martial_reroll_message,
        pending_replace_message,
        roster_message,
        shop_message,
        team3_leaderboard_message,
        wallet_message,
        boss_fight_result_message,
        boss_rank_message,
        boss_settlement_message,
        boss_status_message,
    )

PENDING_CREATE_TIMEOUT = 60.0
CHALLENGE_TIMEOUT = 120.0
MARTIAL_CHOICE_TIMEOUT = 120.0
AVATAR_UPLOAD_TIMEOUT = 180.0
WORLD_BOSS_DAILY_LIMIT = 3
WORLD_BOSS_NAME = '\u7fa4\u9f99\u4e4b\u9996'
WORLD_BOSS_PHASE1 = {
    'name': '\u7fa4\u9f99\u4e4b\u9996\u00b7\u7834\u9635\u524d\u950b',
    'stats': {'hp': 1800, 'atk': 150, 'def': 90, 'spd': 100.0, 'crt': 10.0, 'eva': 8.0},
    'martial_art_id': 'sword_huashan',
    'neigong_id': 'shenzhao_jing',
    'qinggong_id': 'lightning_flash',
}
WORLD_BOSS_PHASE2 = {
    'name': '\u7fa4\u9f99\u4e4b\u9996\u00b7\u771f\u8eab',
    'stats': {'hp': 19000, 'atk': 170, 'def': 170, 'spd': 115.0, 'crt': 12.0, 'eva': 10.0},
    'martial_art_id': 'sword_huashan',
    'neigong_id': 'shenzhao_jing',
    'qinggong_id': 'lightning_flash',
}


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


def _image_ref_from_mapping(data: dict[str, Any]) -> str | None:
    for key in ('file_path', 'path', 'local_path', 'url', 'file_url', 'src', 'file', 'image'):
        value = data.get(key)
        if value not in (None, ''):
            return str(value)
    return None


def extract_first_image_ref(event: AstrMessageEvent) -> str | None:
    roots = (
        event,
        getattr(event, 'message_obj', None),
        getattr(event, 'raw_message', None),
        _safe_call(event, 'get_platform_event'),
        _safe_call(event, 'get_message_obj'),
    )
    for root in roots:
        for node in _walk_nested(root):
            if isinstance(node, dict):
                node_type = str(node.get('type', '')).lower()
                data = node.get('data', {}) if isinstance(node.get('data', {}), dict) else {}
                if node_type == 'image':
                    ref = _image_ref_from_mapping(data) or _image_ref_from_mapping(node)
                    if ref:
                        return ref
                ref = _image_ref_from_mapping(node)
                if ref:
                    return ref
                continue
            node_type = str(getattr(node, 'type', '')).lower()
            if node_type != 'image':
                continue
            data = getattr(node, 'data', None)
            if isinstance(data, dict):
                ref = _image_ref_from_mapping(data)
                if ref:
                    return ref
            for attr in ('file_path', 'path', 'local_path', 'url', 'file_url', 'src', 'file', 'image'):
                value = getattr(node, attr, None)
                if value not in (None, ''):
                    return str(value)
    message_text = str(getattr(event, 'message_str', '') or '')
    match = re.search(r'\[CQ:image,([^\]]+)\]', message_text)
    if not match:
        return None
    payload = match.group(1)
    parts: dict[str, str] = {}
    for item in payload.split(','):
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        parts[key.strip()] = value.strip()
    return parts.get('url') or parts.get('file')


@register('astrbot_plugin_name_fight', 'Codex', '\u6587\u5b57\u683c\u6597\u5f15\u64ce', '1.4.0')
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
        self.pending_martial_choices: dict[str, dict[str, Any]] = {}
        self.pending_avatar_uploads: dict[str, dict[str, Any]] = {}
        self._daily_settlement_task: asyncio.Task | None = None
        self._ensure_daily_settlement_task()
        logger.info('[name_fight] plugin loaded')

    def _ensure_daily_settlement_task(self) -> None:
        task = self._daily_settlement_task
        if task is not None and not task.done():
            return
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return
        self._daily_settlement_task = loop.create_task(self._daily_settlement_loop())

    async def _daily_settlement_loop(self) -> None:
        while True:
            now = datetime.now()
            next_midnight = datetime.combine((now + timedelta(days=1)).date(), datetime.min.time())
            wait_seconds = max(1.0, (next_midnight - now).total_seconds())
            try:
                await asyncio.sleep(wait_seconds)
                day_key = (date.today() - timedelta(days=1)).isoformat()
                await self._run_daily_settlements(day_key)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(f'[name_fight] daily settlement failed: {exc!r}')
                await asyncio.sleep(5.0)

    async def _run_daily_settlements(self, day_key: str) -> None:
        total_rewards = 0
        for board in ('1v1', '3v3'):
            for group_id in self.repo.get_tracked_group_ids(board):
                try:
                    result = self.repo.settle_daily_leaderboard(group_id, board, day_key)
                except ValueError:
                    continue
                total_rewards += len(result.get('rewards', []))
        logger.info(f'[name_fight] daily settlements finished: day={day_key}, rewards={total_rewards}')

    def _consume_pending_creation(self, user_id: str) -> dict[str, Any] | None:
        pending = self.pending_creations.get(user_id)
        if pending is None:
            return None
        if pending['expires_at'] < time.monotonic():
            self.pending_creations.pop(user_id, None)
            return None
        return pending

    def _consume_pending_martial_choice(self, user_id: str) -> dict[str, Any] | None:
        pending = self.pending_martial_choices.get(user_id)
        if pending is None:
            return None
        if pending['expires_at'] < time.monotonic():
            self.pending_martial_choices.pop(user_id, None)
            return None
        return pending


    def _consume_pending_avatar_upload(self, user_id: str, *, consume: bool = True) -> dict[str, Any] | None:
        pending = self.pending_avatar_uploads.get(user_id)
        if pending is None:
            return None
        if pending['expires_at'] < time.monotonic():
            self.pending_avatar_uploads.pop(user_id, None)
            return None
        if consume:
            return self.pending_avatar_uploads.pop(user_id, None)
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
            self._ensure_daily_settlement_task()
            return group_id
        except RuntimeError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return None

    def _boss_admin_ids(self) -> set[str]:
        configured = self.config.get('boss_admin_user_ids', [])
        if isinstance(configured, str):
            return {item.strip() for item in configured.split(',') if item.strip()}
        if isinstance(configured, (list, tuple, set)):
            return {str(item).strip() for item in configured if str(item).strip()}
        return set()

    def _is_boss_admin(self, event: AstrMessageEvent, user_id: str) -> bool:
        configured = self._boss_admin_ids()
        if configured:
            return user_id in configured
        admin_flags = ('is_admin', 'admin', 'is_owner', 'owner')
        roots = (
            event,
            getattr(event, 'sender', None),
            getattr(event, 'message_obj', None),
            getattr(event, 'raw_message', None),
            _safe_call(event, 'get_platform_event'),
            _safe_call(event, 'get_message_obj'),
        )
        for root in roots:
            for flag in admin_flags:
                value = _dig_value(root, (flag,))
                if isinstance(value, bool) and value:
                    return True
                if str(value).strip().lower() in {'1', 'true', 'admin', 'owner'}:
                    return True
            role = _dig_value(root, ('role', 'sender_role', 'permission'))
            if str(role).strip().lower() in {'admin', 'owner', 'group_admin', 'group_owner'}:
                return True
        return True

    async def _require_boss_admin(self, event: AstrMessageEvent, user_id: str) -> bool:
        if self._is_boss_admin(event, user_id):
            return True
        await event.send(event.plain_result('\u53ea\u6709\u7ba1\u7406\u5458\u53ef\u4ee5\u64cd\u4f5c\u4e16\u754cBOSS\u547d\u4ee4\u3002'))
        event.stop_event()
        return False

    def _build_world_boss_payload(self, template: dict[str, Any]) -> dict[str, Any]:
        martial_art_id = str(template['martial_art_id'])
        neigong_id = str(template['neigong_id'])
        qinggong_id = str(template['qinggong_id'])
        return {
            'name': str(template['name']),
            'stats': dict(template['stats']),
            'martial_art_id': martial_art_id,
            'neigong_id': neigong_id,
            'qinggong_id': qinggong_id,
            'martial_art': deepcopy(self.repo.martial_arts_map[martial_art_id]),
            'neigong': deepcopy(self.repo.neigong_map[neigong_id]),
            'qinggong': deepcopy(self.repo.qinggong_map[qinggong_id]),
        }

    def _build_default_world_boss(self) -> tuple[str, dict[str, Any], dict[str, Any]]:
        phase1 = self._build_world_boss_payload(WORLD_BOSS_PHASE1)
        phase2 = self._build_world_boss_payload(WORLD_BOSS_PHASE2)
        return WORLD_BOSS_NAME, phase1, phase2

    def _build_world_boss_fighter(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            'name': str(payload['name']),
            'stats': dict(payload['stats']),
            'martial_art': deepcopy(payload['martial_art']),
            'neigong': deepcopy(payload['neigong']),
            'qinggong': deepcopy(payload['qinggong']),
        }

    def _alive_team_state(self, team_state: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [entry for entry in team_state if int(entry.get('hp', 0)) > 0]

    def _team_state_total_hp(self, team_state: list[dict[str, Any]]) -> int:
        return sum(max(0, int(entry.get('hp', 0))) for entry in team_state)

    def _avatar_dir(self) -> Path:
        avatar_dir = Path(self.repo.db_path).parent / 'avatars'
        avatar_dir.mkdir(parents=True, exist_ok=True)
        return avatar_dir

    def _avatar_target_path(self, fighter_name: str) -> Path:
        digest = hashlib.sha256(fighter_name.strip().casefold().encode('utf-8')).hexdigest()[:24]
        return self._avatar_dir() / f'{digest}.img'

    def _resolve_local_image_path(self, image_ref: str) -> Path | None:
        parsed = urlparse(str(image_ref))
        if parsed.scheme in ('http', 'https'):
            return None
        candidate = str(image_ref)
        if parsed.scheme == 'file':
            candidate = unquote(parsed.path or '')
            if re.match(r'^/[A-Za-z]:/', candidate):
                candidate = candidate[1:]
            elif parsed.netloc:
                candidate = f'//{parsed.netloc}{candidate}'
        candidate = candidate.strip().strip('"')
        if not candidate:
            return None
        path = Path(candidate)
        return path if path.exists() else None

    def _write_avatar_image(self, image_ref: str, target_path: Path) -> None:
        local_path = self._resolve_local_image_path(image_ref)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if local_path is not None:
            shutil.copyfile(local_path, target_path)
            return
        parsed = urlparse(str(image_ref))
        if parsed.scheme not in ('http', 'https'):
            raise ValueError('\u672a\u68c0\u6d4b\u5230\u53ef\u8bfb\u53d6\u7684\u56fe\u7247\uff0c\u8bf7\u628a\u56fe\u7247\u548c\u6307\u4ee4\u653e\u5728\u540c\u4e00\u6761\u6d88\u606f\u91cc\u3002')
        with urlopen(str(image_ref), timeout=15) as response:
            data = response.read()
        if not data:
            raise ValueError('\u56fe\u7247\u4e0b\u8f7d\u5931\u8d25\uff0c\u8bf7\u6362\u4e00\u5f20\u56fe\u7247\u518d\u8bd5\u3002')
        target_path.write_bytes(data)

    def _save_fighter_avatar(self, user_id: str, fighter_name: str, image_ref: str) -> dict[str, Any]:
        fighter = self.repo.get_user_fighter_by_name(user_id, fighter_name)
        if fighter is None:
            raise ValueError('\u4f60\u540d\u4e0b\u6ca1\u6709\u8fd9\u4e2a\u89d2\u8272\u3002')
        target_path = self._avatar_target_path(fighter_name)
        old_path = Path(str(fighter.get('avatar_path') or '')) if fighter.get('avatar_path') else None
        self._write_avatar_image(image_ref, target_path)
        if old_path and old_path != target_path and old_path.exists():
            try:
                old_path.unlink()
            except OSError:
                logger.warning(f'[name_fight] failed to remove old avatar: {old_path}')
        return self.repo.set_fighter_avatar_path(user_id, fighter_name, str(target_path))

    def _remember_group_user_label(self, event: AstrMessageEvent, group_id: str) -> None:
        try:
            user_id = extract_user_id(event)
            label = extract_user_label(event)
        except RuntimeError:
            return
        self.repo.set_group_user_label(group_id, user_id, label)

    def _challenge_key(self, group_id: str, defender_user_id: str) -> str:
        return f'{group_id}:{defender_user_id}'

    def _current_week_key(self) -> str:
        today = date.today()
        iso_year, iso_week, _iso_weekday = today.isocalendar()
        return f'{iso_year}-W{iso_week:02d}'

    def _rank_reward_bonus(self, mode: str, winner_before: float, loser_before: float) -> int:
        diff = loser_before - winner_before
        if mode == '1v1':
            if diff >= 200:
                return 18
            if diff >= 100:
                return 12
            if diff > 0:
                return 6
            return 0
        if diff >= 200:
            return 30
        if diff >= 100:
            return 20
        if diff > 0:
            return 10
        return 0

    def _grant_ranked_battle_points(
        self,
        mode: str,
        rating_change: dict[str, dict[str, float | str]],
        attacker_user_id: str,
        attacker_label: str,
        defender_user_id: str,
        defender_label: str,
        winner_side: str | None,
    ) -> tuple[int, int, int, int, int, int]:
        win_key = f'accepted_{mode}_win'
        loss_key = f'accepted_{mode}_loss'
        attacker_base = BATTLE_POINT_REWARDS[loss_key]
        defender_base = BATTLE_POINT_REWARDS[loss_key]
        attacker_bonus = 0
        defender_bonus = 0
        attacker_before = float(rating_change['attacker']['before'])
        defender_before = float(rating_change['defender']['before'])
        if winner_side == 'attacker':
            attacker_base = BATTLE_POINT_REWARDS[win_key]
            attacker_bonus = self._rank_reward_bonus(mode, attacker_before, defender_before)
        elif winner_side == 'defender':
            defender_base = BATTLE_POINT_REWARDS[win_key]
            defender_bonus = self._rank_reward_bonus(mode, defender_before, attacker_before)
        attacker_gain = attacker_base + attacker_bonus
        defender_gain = defender_base + defender_bonus
        attacker_points = self.repo.grant_points(attacker_user_id, attacker_gain)
        defender_points = self.repo.grant_points(defender_user_id, defender_gain)
        return attacker_points, defender_points, attacker_gain, defender_gain, attacker_bonus, defender_bonus

    def _format_weekly_settlement_lines(self, result: dict[str, Any]) -> list[str]:
        board = '1v1' if result['board_type'] == '1v1' else '3v3'
        lines = [f'\u3010\u5468\u699c\u7ed3\u7b97\u3011{result["week_key"]} {board} \u5956\u52b1\u5df2\u53d1\u653e\u3002']
        rewards = result.get('rewards', [])
        if not rewards:
            lines.append('\u672c\u6b21\u6392\u884c\u699c\u6ca1\u6709\u53ef\u53d1\u5956\u5bf9\u8c61\u3002')
            return lines
        for reward in rewards:
            line = f"\u7b2c{reward['rank']}\u540d {reward['display_name']} +{reward['points']}\u79ef\u5206"
            if reward.get('item_name') and int(reward.get('item_quantity', 0)) > 0:
                line += f" + {reward['item_name']} x{reward['item_quantity']}"
            lines.append(line)
        return lines

    def _format_daily_settlement_lines(self, result: dict[str, Any]) -> list[str]:
        board = '1v1' if result['board_type'] == '1v1' else '3v3'
        lines = [f'\u3010\u65e5\u699c\u7ed3\u7b97\u3011{result["day_key"]} {board} \u5956\u52b1\u5df2\u53d1\u653e\u3002']
        rewards = result.get('rewards', [])
        if not rewards:
            lines.append('\u672c\u6b21\u6392\u884c\u699c\u6ca1\u6709\u53ef\u53d1\u5956\u5bf9\u8c61\u3002')
            return lines
        for reward in rewards:
            lines.append(f"\u7b2c{reward['rank']}\u540d {reward['display_name']} +{reward['points']}\u79ef\u5206")
        return lines


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
        lines = ['【3v3 队伍】']
        fighters_by_slot = {int(fighter['slot_index']): fighter for fighter in roster}
        if len(roster) < TEAM3_TEAM_SIZE:
            lines.append(f'当前角色: {len(roster)}/{TEAM3_TEAM_SIZE}')
            for slot in range(1, MAX_FIGHTERS_PER_USER + 1):
                fighter = fighters_by_slot.get(slot)
                if fighter is None:
                    lines.append(f'{slot}号位: 空')
                else:
                    lines.append(f'{slot}号位: {fighter["name"]} | {fighter["martial_art"]["name"]}')
            lines.append(f'至少需要 {TEAM3_TEAM_SIZE} 名角色才能参加 3v3 对战。')
            return lines
        order = self.repo.get_user_team3_order(user_id)
        lines.append(f'出战顺序: {order[0]} -> {order[1]} -> {order[2]}')
        for slot in range(1, MAX_FIGHTERS_PER_USER + 1):
            fighter = fighters_by_slot.get(slot)
            if fighter is None:
                lines.append(f'{slot}号位: 空')
            else:
                lines.append(f'{slot}号位: {fighter["name"]} | {fighter["martial_art"]["name"]}')
        team = [fighters_by_slot[slot] for slot in order if slot in fighters_by_slot]
        lines.append(f'当前阵容: {self._format_team3_names(team)}')
        return lines

    def _get_ready_team3_fighters(self, user_id: str) -> list[dict[str, Any]]:
        team = self.repo.get_user_team3_fighters(user_id)
        if len(team) < TEAM3_TEAM_SIZE:
            raise ValueError('你当前未凑齐 3 名出战角色，无法参加 3v3。')
        return team

    def _clone_fighter_with_hp(self, fighter: dict[str, Any], hp: int) -> dict[str, Any]:
        clone = deepcopy(fighter)
        clone['stats'] = dict(clone['stats'])
        clone['stats']['hp'] = max(1, int(hp))
        return clone

    def _is_turn_log_line(self, line: str) -> bool:
        return line.startswith('【第') and '回合】' in line

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
            f'【3v3 阵容】{attacker_label}: {self._format_team3_names(attacker_team)} | {defender_label}: {self._format_team3_names(defender_team)}'
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
            lines.append(f'【第{duel_no}场】{attacker_label}·{attacker_name} vs {defender_label}·{defender_name}')
            lines.append(battle_overview_line(attacker_fighter, defender_fighter))
            lines.extend(self._chunk_team3_battle_logs(duel_no, compact_battle_logs(logs)))

            if winner_name == attacker_name:
                attacker_hp = int(state['fighter_a_hp'])
                lines.append(
                    f'【第{duel_no}场结果】{attacker_name} 击败了 {defender_name}，'
                    f'剩余气血 {attacker_hp}/{state["fighter_a_max_hp"]}。'
                )
                defender_index += 1
                if defender_index < len(defender_team):
                    defender_hp = int(defender_team[defender_index]['stats']['hp'])
                    next_name = defender_team[defender_index]['name']
                    lines.append(f'下一位由 {attacker_name} 继续迎战 {next_name}。')
            elif winner_name == defender_name:
                defender_hp = int(state['fighter_b_hp'])
                lines.append(
                    f'【第{duel_no}场结果】{defender_name} 击败了 {attacker_name}，'
                    f'剩余气血 {defender_hp}/{state["fighter_b_max_hp"]}。'
                )
                attacker_index += 1
                if attacker_index < len(attacker_team):
                    attacker_hp = int(attacker_team[attacker_index]['stats']['hp'])
                    next_name = attacker_team[attacker_index]['name']
                    lines.append(f'下一位由 {defender_name} 继续迎战 {next_name}。')
            else:
                lines.append(f'【第{duel_no}场结果】{attacker_name} 与 {defender_name} 同归于尽，双方同时退场。')
                attacker_index += 1
                defender_index += 1
                if attacker_index < len(attacker_team):
                    attacker_hp = int(attacker_team[attacker_index]['stats']['hp'])
                if defender_index < len(defender_team):
                    defender_hp = int(defender_team[defender_index]['stats']['hp'])
            duel_no += 1

        if attacker_index >= len(attacker_team) and defender_index >= len(defender_team):
            lines.append('【3v3 结果】双方三人全部退场，本场以平局收尾。')
            return lines, None
        if defender_index >= len(defender_team):
            lines.append(f'【3v3 结果】{attacker_label} 率先击穿对方全队，获得胜利。')
            return lines, 'attacker'
        lines.append(f'【3v3 结果】{defender_label} 率先击穿对方全队，获得胜利。')
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
        reward_enabled: bool = False,
        elo_scale: float = 1.0,
    ) -> None:
        if self.is_battling:
            await event.send(event.plain_result('\u5f53\u524d\u5df2\u6709\u6218\u6597\u6b63\u5728\u8fdb\u884c, \u8bf7\u7a0d\u540e\u518d\u8bd5\u3002'))
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
                elo_scale=elo_scale,
            )
            await asyncio.sleep(self.broadcast_delay)
            await event.send(event.plain_result(
                f'\u30103v3 \u79ef\u5206\u53d8\u5316\u3011: '
                f'{rating_change["attacker"]["name"]} {rating_change["attacker"]["delta"]:+.2f} '
                f'({rating_change["attacker"]["before"]:.2f} -> {rating_change["attacker"]["after"]:.2f}) | '
                f'{rating_change["defender"]["name"]} {rating_change["defender"]["delta"]:+.2f} '
                f'({rating_change["defender"]["before"]:.2f} -> {rating_change["defender"]["after"]:.2f})'
            ))
            if reward_enabled:
                attacker_points, defender_points, gain_a, gain_d, bonus_a, bonus_d = self._grant_ranked_battle_points(
                    '3v3',
                    rating_change,
                    attacker_user_id,
                    attacker_label,
                    defender_user_id,
                    defender_label,
                    winner_side,
                )
                reward_detail_a = f'\u57fa\u7840{gain_a - bonus_a}' + (f' + \u6311\u6218\u5956\u52b1{bonus_a}' if bonus_a else '')
                reward_detail_d = f'\u57fa\u7840{gain_d - bonus_d}' + (f' + \u6311\u6218\u5956\u52b1{bonus_d}' if bonus_d else '')
                await asyncio.sleep(self.broadcast_delay)
                await event.send(event.plain_result(
                    f'\u3010\u79ef\u5206\u5956\u52b1\u3011{attacker_label} +{gain_a} ({reward_detail_a}\uff0c\u73b0\u6709 {attacker_points}) | '
                    f'{defender_label} +{gain_d} ({reward_detail_d}\uff0c\u73b0\u6709 {defender_points})'
                ))
        finally:
            self.is_battling = False
            event.stop_event()

    def _battle_team_against_boss_phase(
        self,
        phase_title: str,
        team_state: list[dict[str, Any]],
        boss_payload: dict[str, Any],
        boss_hp: int | None = None,
    ) -> dict[str, Any]:
        boss = self._build_world_boss_fighter(boss_payload)
        if boss_hp is not None:
            boss['stats']['hp'] = max(1, int(boss_hp))
        boss_name = str(boss['name'])
        current_boss_hp = int(boss['stats']['hp'])
        lines = [f'\u3010{phase_title}\u3011{boss_name} \u767b\u573a\u3002']
        duel_no = 1
        while current_boss_hp > 0:
            alive_entries = self._alive_team_state(team_state)
            if not alive_entries:
                break
            fighter_entry = alive_entries[0]
            fighter = fighter_entry['fighter']
            fighter_name = str(fighter['name'])
            attacker = self._clone_fighter_with_hp(fighter, int(fighter_entry['hp']))
            defender = self._clone_fighter_with_hp(boss, current_boss_hp)
            _logs, winner_name, state = self.engine.battle_with_state(attacker, defender)
            current_boss_hp = int(state['fighter_b_hp'])
            fighter_entry['hp'] = max(0, int(state['fighter_a_hp']))
            if winner_name == fighter_name:
                lines.append(
                    f'\u3010{phase_title}\u7b2c{duel_no}\u9635\u3011{fighter_name} \u538b\u5236\u4e86 {boss_name}\uff0c'
                    f'\u81ea\u8eab\u5269\u4f59 {fighter_entry["hp"]}/{state["fighter_a_max_hp"]}\uff0c'
                    f'Boss \u5269\u4f59 {current_boss_hp}/{state["fighter_b_max_hp"]}\u3002'
                )
            elif winner_name == boss_name:
                fighter_entry['hp'] = 0
                lines.append(
                    f'\u3010{phase_title}\u7b2c{duel_no}\u9635\u3011{boss_name} \u51fb\u9000\u4e86 {fighter_name}\uff0c'
                    f'Boss \u5269\u4f59 {current_boss_hp}/{state["fighter_b_max_hp"]}\u3002'
                )
            else:
                fighter_entry['hp'] = 0
                lines.append(
                    f'\u3010{phase_title}\u7b2c{duel_no}\u9635\u3011{fighter_name} \u4e0e {boss_name} \u540c\u5f52\u4e8e\u5c3d\uff0c'
                    f'Boss \u5269\u4f59 {current_boss_hp}/{state["fighter_b_max_hp"]}\u3002'
                )
            duel_no += 1
        return {
            'lines': lines,
            'boss_name': boss_name,
            'boss_max_hp': int(boss['stats']['hp']),
            'boss_remaining_hp': max(0, current_boss_hp),
            'team_state': team_state,
            'cleared': current_boss_hp <= 0,
            'alive_count': len(self._alive_team_state(team_state)),
            'alive_total_hp': self._team_state_total_hp(team_state),
        }

    async def _start_world_boss_fight(
        self,
        event: AstrMessageEvent,
        group_id: str,
        user_id: str,
        display_name: str,
        team: list[dict[str, Any]],
        activity: dict[str, Any],
        attempt_info: dict[str, int],
    ) -> None:
        if self.is_battling:
            await event.send(event.plain_result('\u5f53\u524d\u5df2\u6709\u6218\u6597\u6b63\u5728\u8fdb\u884c, \u8bf7\u7a0d\u540e\u518d\u8bd5\u3002'))
            event.stop_event()
            return
        self.is_battling = True
        try:
            team_state = [{'fighter': deepcopy(fighter), 'hp': int(fighter['stats']['hp'])} for fighter in team]
            phase1_result = self._battle_team_against_boss_phase('\u4e00\u9636\u6bb5', team_state, activity['phase1_payload'])
            await self._send_lines(event, phase1_result['lines'])
            result_payload: dict[str, Any] = {
                'boss_name': activity['boss_name'],
                'phase1_cleared': bool(phase1_result['cleared']),
                'entered_phase2': False,
                'phase2_damage': 0,
                'phase2_current_hp': int(activity['phase2_current_hp']),
                'phase2_max_hp': int(activity['phase2_max_hp']),
                'total_damage': 0,
                'remaining_attempts': int(attempt_info['remaining_attempts']),
                'daily_limit': int(attempt_info['daily_limit']),
                'is_killed': False,
            }
            if not phase1_result['cleared']:
                await asyncio.sleep(self.broadcast_delay)
                await event.send(event.plain_result(boss_fight_result_message(result_payload)))
                event.stop_event()
                return
            if not self._alive_team_state(team_state):
                await asyncio.sleep(self.broadcast_delay)
                await event.send(event.plain_result(boss_fight_result_message(result_payload)))
                event.stop_event()
                return
            phase2_result = self._battle_team_against_boss_phase(
                '\u4e8c\u9636\u6bb5',
                team_state,
                activity['phase2_payload'],
                boss_hp=int(activity['phase2_max_hp']),
            )
            await asyncio.sleep(self.broadcast_delay)
            await self._send_lines(event, phase2_result['lines'])
            raw_phase2_damage = max(0, int(activity['phase2_max_hp']) - int(phase2_result['boss_remaining_hp']))
            damage_result = self.repo.apply_group_boss_phase2_damage(activity['boss_id'], group_id, raw_phase2_damage)
            total_damage = 0
            if int(damage_result['applied_damage']) > 0:
                contribution = self.repo.record_group_boss_damage(
                    activity['boss_id'],
                    group_id,
                    user_id,
                    display_name,
                    int(damage_result['applied_damage']),
                )
                total_damage = int(contribution['total_damage'])
            result_payload.update(
                {
                    'entered_phase2': True,
                    'phase2_damage': int(damage_result['applied_damage']),
                    'phase2_current_hp': int(damage_result['after_hp']),
                    'phase2_max_hp': int(activity['phase2_max_hp']),
                    'total_damage': total_damage,
                    'is_killed': bool(damage_result['is_killed']),
                }
            )
            await asyncio.sleep(self.broadcast_delay)
            await event.send(event.plain_result(boss_fight_result_message(result_payload)))
            if damage_result['is_killed']:
                settlement = self.repo.settle_group_boss(group_id, activity['boss_id'])
                await asyncio.sleep(self.broadcast_delay)
                await event.send(event.plain_result(boss_settlement_message(settlement)))
        finally:
            self.is_battling = False
            event.stop_event()

    async def _try_consume_avatar_upload(self, event: AstrMessageEvent) -> bool:
        user_id = await self._require_user_id(event)
        if user_id is None:
            return True
        pending = self._consume_pending_avatar_upload(user_id, consume=False)
        if pending is None:
            return False
        image_ref = extract_first_image_ref(event)
        if not image_ref:
            return False
        pending = self._consume_pending_avatar_upload(user_id, consume=True)
        if pending is None:
            return False
        try:
            fighter = self._save_fighter_avatar(user_id, pending['fighter_name'], image_ref)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return True
        except Exception as exc:
            logger.warning(f'[name_fight] save avatar failed: {exc!r}')
            await event.send(event.plain_result('头像保存失败，请换一张图片再试。'))
            event.stop_event()
            return True
        await self._send_fighter_summary_safe(
            event,
            fighter,
            False,
            prefix_lines=[f'【头像已更新】{fighter["name"]} 的头像已保存；再次设置会覆盖旧图片。'],
        )
        event.stop_event()
        return True

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

    async def _send_fighter_summary_safe(self, event: AstrMessageEvent, fighter: dict, created: bool = False, prefix_lines: list[str] | None = None, suffix_lines: list[str] | None = None) -> None:
        import os
        
        rating_raw = float(fighter.get('star_rating', 3.0))
        breakthrough = int(fighter.get('breakthrough_stage', 0) or 0)
        
        # 5 鏄熷強浠ヤ笂瑙掕壊锛氬彂鍥剧墖 + 鍓嶅悗闄勫甫鏂囧瓧
        if rating_raw >= 5.0 or breakthrough > 0:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            image_path = None
            try:
                from .render_profile import render_star_card
                image_path = render_star_card(fighter, data_dir)
            except Exception as e:
                logger.error(f"[name_fight] render star card failed: {e}")
                
            if image_path and os.path.exists(image_path):
                try:
                    from astrbot.api.message_components import Image
                    # 鍏堝彂鍓嶇紑鏂囧瓧锛堝鏋滄湁锛?
                    if prefix_lines:
                        await self._send_text_safe(event, join_lines(prefix_lines))
                    # 鍙戝浘鐗?
                    res = event.make_result()
                    res.chain.append(Image.fromFileSystem(image_path))
                    await event.send(res)
                    # 鍐嶅彂鍚庣紑鏂囧瓧锛堝鏋滄湁锛屾瘮濡傞€夎鑹叉彁绀猴級
                    if suffix_lines:
                        await self._send_text_safe(event, join_lines(suffix_lines))
                    return
                except Exception as e:
                    logger.warning(f"[name_fight] Failed to send image, fallback to text: {e}")
        
        # 4 鏄熷強浠ヤ笅 鎴?鍥剧墖鍙戦€佸け璐ワ細鍥為€€绾枃瀛?
        lines = list(prefix_lines) if prefix_lines else []
        lines.extend(fighter_summary_lines(fighter, created))
        if suffix_lines:
            lines.extend(suffix_lines)
        await self._send_text_safe(event, join_lines(lines))

    async def _start_battle(
        self,
        event: AstrMessageEvent,
        group_id: str,
        attacker: dict[str, Any],
        defender: dict[str, Any],
        opener: str,
        reward_users: tuple[str, str] | None = None,
        reward_labels: tuple[str, str] | None = None,
        elo_scale: float = 1.0,
    ) -> None:
        if self.is_battling:
            await event.send(event.plain_result('\u5f53\u524d\u5df2\u6709\u6218\u6597\u6b63\u5728\u8fdb\u884c, \u8bf7\u7a0d\u540e\u518d\u8bd5\u3002'))
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
            rating_change = self.repo.record_group_battle(
                group_id,
                attacker['name'],
                defender['name'],
                winner_name,
                elo_scale=elo_scale,
            )
            attacker_change = rating_change['attacker']
            defender_change = rating_change['defender']
            await asyncio.sleep(self.broadcast_delay)
            await event.send(event.plain_result(
                f'\u3010\u79ef\u5206\u53d8\u5316\u3011: '
                f'{attacker_change["name"]} {attacker_change["delta"]:+.2f} '
                f'({attacker_change["before"]:.2f} -> {attacker_change["after"]:.2f}) | '
                f'{defender_change["name"]} {defender_change["delta"]:+.2f} '
                f'({defender_change["before"]:.2f} -> {defender_change["after"]:.2f})'
            ))
            if reward_users is not None:
                attacker_user_id, defender_user_id = reward_users
                attacker_label, defender_label = reward_labels or (attacker['name'], defender['name'])
                winner_side = None
                if winner_name == attacker['name']:
                    winner_side = 'attacker'
                elif winner_name == defender['name']:
                    winner_side = 'defender'
                attacker_points, defender_points, gain_a, gain_d, bonus_a, bonus_d = self._grant_ranked_battle_points(
                    '1v1',
                    rating_change,
                    attacker_user_id,
                    attacker_label,
                    defender_user_id,
                    defender_label,
                    winner_side,
                )
                reward_detail_a = f'\u57fa\u7840{gain_a - bonus_a}' + (f' + \u6311\u6218\u5956\u52b1{bonus_a}' if bonus_a else '')
                reward_detail_d = f'\u57fa\u7840{gain_d - bonus_d}' + (f' + \u6311\u6218\u5956\u52b1{bonus_d}' if bonus_d else '')
                await asyncio.sleep(self.broadcast_delay)
                await event.send(event.plain_result(
                    f'\u3010\u79ef\u5206\u5956\u52b1\u3011{attacker_label} +{gain_a} ({reward_detail_a}\uff0c\u73b0\u6709 {attacker_points}) | '
                    f'{defender_label} +{gain_d} ({reward_detail_d}\uff0c\u73b0\u6709 {defender_points})'
                ))
        finally:
            self.is_battling = False
            event.stop_event()

    @filter.command('fhelp', alias={'帮助'})
    async def help_command(self, event: AstrMessageEvent):
        await event.send(event.plain_result(join_lines(HELP_LINES)))
        event.stop_event()


    @filter.command('fguide', alias={'教程'})
    async def guide_command(self, event: AstrMessageEvent):
        await event.send(event.plain_result(join_lines(GUIDE_LINES)))
        event.stop_event()

    @filter.command('create', alias={'\u521b\u5efa\u89d2\u8272'})
    async def create_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip():
            await event.send(event.plain_result('\u7528\u6cd5: /\u521b\u5efa\u89d2\u8272 \u89d2\u8272\u540d'))
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
            await self._send_fighter_summary_safe(
                event, fighter, True, 
                suffix_lines=[pending_replace_message(fighter_name, roster, int(PENDING_CREATE_TIMEOUT))]
            )
            event.stop_event()
            return
        try:
            fighter = self.repo.create_fighter_for_user(user_id, fighter_name)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        await self._send_fighter_summary_safe(event, fighter, True)
        event.stop_event()

    @filter.command('choose', alias={'\u9009\u62e9\u89d2\u8272'})
    async def choose_command(self, event: AstrMessageEvent):
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip().isdigit():
            await event.send(event.plain_result('\u7528\u6cd5: /\u9009\u62e9\u89d2\u8272 \u5e8f\u53f7'))
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
        prefix = f'\u3010\u89d2\u8272\u66f4\u66ff\u3011\u5df2\u7528\u3010{fighter["name"]}\u3011\u9876\u66ff\u3010{old_name}\u3011\u5165\u5217\uff0c\u5e76\u81ea\u52a8\u8bbe\u4e3a\u5f53\u524d\u51fa\u6218\u89d2\u8272\u3002'
        await self._send_fighter_summary_safe(event, fighter, False, prefix_lines=[prefix])
        event.stop_event()

    @filter.command('bossopen')
    async def boss_open_command(self, event: AstrMessageEvent):
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        if not await self._require_boss_admin(event, user_id):
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        boss_name, phase1_payload, phase2_payload = self._build_default_world_boss()
        try:
            activity = self.repo.open_group_boss(group_id, boss_name, phase1_payload, phase2_payload, user_id)
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        status_text = boss_status_message(activity, [], WORLD_BOSS_DAILY_LIMIT, WORLD_BOSS_DAILY_LIMIT)
        await event.send(event.plain_result(f'\u3010\u4e16\u754cBOSS\u5f00\u542f\u3011{boss_name} \u5df2\u964d\u4e34\u3002\n{status_text}'))
        event.stop_event()

    @filter.command('boss')
    async def boss_status_command(self, event: AstrMessageEvent):
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        activity = self.repo.get_active_group_boss(group_id)
        if activity is None:
            await event.send(event.plain_result('\u3010\u4e16\u754cBOSS\u3011\u5f53\u524d\u7fa4\u8fd8\u6ca1\u6709\u6b63\u5728\u8fdb\u884c\u7684\u4e16\u754cBOSS\u6d3b\u52a8\u3002'))
            event.stop_event()
            return
        used_attempts = self.repo.get_group_boss_attempt_usage(activity['boss_id'], group_id, user_id, date.today().isoformat())
        remaining_attempts = max(0, WORLD_BOSS_DAILY_LIMIT - int(used_attempts))
        entries = self.repo.get_group_boss_rank(group_id, activity['boss_id'], limit=5)
        await event.send(event.plain_result(boss_status_message(activity, entries, remaining_attempts, WORLD_BOSS_DAILY_LIMIT)))
        event.stop_event()

    @filter.command('bossfight')
    async def boss_fight_command(self, event: AstrMessageEvent):
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        activity = self.repo.get_active_group_boss(group_id)
        if activity is None:
            await event.send(event.plain_result('\u5f53\u524d\u7fa4\u6ca1\u6709\u6b63\u5728\u8fdb\u884c\u7684\u4e16\u754cBOSS\u6d3b\u52a8\u3002'))
            event.stop_event()
            return
        try:
            team = self._get_ready_team3_fighters(user_id)
            attempt_info = self.repo.consume_group_boss_attempt(
                activity['boss_id'],
                group_id,
                user_id,
                date.today().isoformat(),
                WORLD_BOSS_DAILY_LIMIT,
            )
        except ValueError as exc:
            await event.send(event.plain_result(str(exc)))
            event.stop_event()
            return
        await self._start_world_boss_fight(
            event,
            group_id,
            user_id,
            extract_user_label(event),
            team,
            activity,
            attempt_info,
        )

    @filter.command('bossrank')
    async def boss_rank_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        activity = self.repo.get_active_group_boss(group_id)
        if activity is None:
            activity = self.repo.get_latest_group_boss(group_id)
        if activity is None:
            await event.send(event.plain_result('\u3010\u4e16\u754cBOSS\u8d21\u732e\u699c\u3011\u5f53\u524d\u7fa4\u8fd8\u6ca1\u6709\u4e16\u754cBOSS\u6d3b\u52a8\u8bb0\u5f55\u3002'))
            event.stop_event()
            return
        entries = self.repo.get_group_boss_rank(group_id, activity['boss_id'], limit=10)
        await event.send(event.plain_result(boss_rank_message(entries)))
        event.stop_event()

    @filter.command('bossclose')
    async def boss_close_command(self, event: AstrMessageEvent):
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        if not await self._require_boss_admin(event, user_id):
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        activity = self.repo.get_active_group_boss(group_id)
        if activity is None:
            await event.send(event.plain_result('\u5f53\u524d\u7fa4\u6ca1\u6709\u53ef\u5173\u95ed\u7684\u4e16\u754cBOSS\u6d3b\u52a8\u3002'))
            event.stop_event()
            return
        updated = self.repo.close_group_boss(group_id, activity['boss_id'])
        await event.send(event.plain_result(boss_settlement_message(None, closed_without_kill=updated['status'] != 'settled')))
        event.stop_event()

    @filter.command('bosssettle')
    async def boss_settle_command(self, event: AstrMessageEvent):
        user_id = await self._require_user_id(event)
        if user_id is None:
            return
        if not await self._require_boss_admin(event, user_id):
            return
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        activity = self.repo.get_latest_group_boss(group_id)
        if activity is None:
            await event.send(event.plain_result('\u5f53\u524d\u7fa4\u8fd8\u6ca1\u6709\u4e16\u754cBOSS\u7ed3\u7b97\u8bb0\u5f55\u3002'))
            event.stop_event()
            return
        settlement = self.repo.get_group_boss_settlement(group_id, activity['boss_id'])
        if settlement is None:
            if activity['status'] == 'killed':
                settlement = self.repo.settle_group_boss(group_id, activity['boss_id'])
            elif activity['status'] == 'active':
                await event.send(event.plain_result('\u5f53\u524d\u4e16\u754cBOSS\u5c1a\u672a\u51fb\u6740, \u8bf7\u5148\u7ee7\u7eed\u6311\u6218\u6216\u4f7f\u7528 /bossclose \u7ed3\u675f\u6d3b\u52a8\u3002'))
                event.stop_event()
                return
            else:
                await event.send(event.plain_result(boss_settlement_message(None, closed_without_kill=True)))
                event.stop_event()
                return
        await event.send(event.plain_result(boss_settlement_message(settlement)))
        event.stop_event()

    @filter.command('rank3', alias={'三排榜'})
    async def team3_rank_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        entries = self.repo.get_group_team3_leaderboard(group_id, limit=10)
        await event.send(event.plain_result(team3_leaderboard_message(entries)))
        event.stop_event()

    @filter.command('rank', alias={'\u6392\u4f4d\u699c'})
    async def rank_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        entries = self.repo.get_group_leaderboard(group_id, limit=10)
        await event.send(event.plain_result(leaderboard_message(entries)))
        event.stop_event()

    
    @filter.command('daysettle', alias={'\u65e5\u699c\u7ed3\u7b97'})
    async def daily_settle_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split()
        mode = 'all'
        day_key = (date.today() - timedelta(days=1)).isoformat()
        if len(parts) >= 2:
            candidate = parts[1].strip().lower()
            if candidate in ('all', '1v1', '3v3'):
                mode = candidate
            else:
                day_key = parts[1].strip()
        if len(parts) >= 3:
            day_key = parts[2].strip()
        try:
            datetime.strptime(day_key, '%Y-%m-%d')
        except ValueError:
            await event.send(event.plain_result('\u7528\u6cd5: /\u65e5\u699c\u7ed3\u7b97 [1v1|3v3|all] [YYYY-MM-DD]'))
            event.stop_event()
            return
        boards = ['1v1', '3v3'] if mode == 'all' else [mode]
        lines: list[str] = []
        for board in boards:
            try:
                result = self.repo.settle_daily_leaderboard(group_id, board, day_key)
            except ValueError as exc:
                lines.append(f'\u3010\u5468\u699c\u7ed3\u7b97\u3011{board}: {exc}')
                continue
            lines.extend(self._format_daily_settlement_lines(result))
        if not lines:
            lines.append('\u672c\u6b21\u6392\u884c\u699c\u6ca1\u6709\u53ef\u53d1\u5956\u5bf9\u8c61\u3002')
        await self._send_text_safe(event, join_lines(lines))
        event.stop_event()

    @filter.command('weeksettle', alias={'weeklysettle', '\u5468\u699c\u7ed3\u7b97'})
    async def weekly_settle_command(self, event: AstrMessageEvent):
        group_id = await self._require_group_id(event)
        if group_id is None:
            return
        text = str(getattr(event, 'message_str', '') or '').strip()
        parts = text.split(maxsplit=1)
        mode = parts[1].strip().lower() if len(parts) == 2 and parts[1].strip() else 'all'
        if mode not in ('all', '1v1', '3v3'):
            await event.send(event.plain_result('用法: /周榜结算 [1v1|3v3|all]'))
            event.stop_event()
            return
        boards = ['1v1', '3v3'] if mode == 'all' else [mode]
        week_key = self._current_week_key()
        lines: list[str] = []
        for board in boards:
            try:
                result = self.repo.settle_weekly_leaderboard(group_id, board, week_key)
            except ValueError as exc:
                lines.append(f'\u3010\u5468\u699c\u7ed3\u7b97\u3011{board}: {exc}')
                continue
            lines.extend(self._format_weekly_settlement_lines(result))
        if not lines:
            lines.append('\u672c\u6b21\u6392\u884c\u699c\u6ca1\u6709\u53ef\u53d1\u5956\u5bf9\u8c61\u3002')
        await self._send_text_safe(event, join_lines(lines))
        event.stop_event()

    @filter.regex(r'.*', priority=-100)
    async def avatar_upload_fallback(self, event: AstrMessageEvent):
        if await self._try_consume_avatar_upload(event):
            return

    @filter.regex(r'(?:[/!?\uFF1F])(?:fhelp|\u5e2e\u52a9|fguide|\u6559\u7a0b|create|\u521b\u5efa\u89d2\u8272|choose|\u9009\u62e9\u89d2\u8272|roster|\u89d2\u8272\u5217\u8868|use|\u5207\u6362\u89d2\u8272|profile|\u89d2\u8272\u8be6\u60c5|textprofile|\u6587\u5b57\u6863\u6848|avatar|\u8bbe\u7f6e\u5934\u50cf|signin|\u7b7e\u5230|wallet|\u79ef\u5206|gift|\u8d60\u9001|bag|\u80cc\u5305|shop|\u5546\u5e97|buy|\u8d2d\u4e70|feed|\u5582\u517b|break|\u7a81\u7834|randommartial|\u968f\u673a\u6362\u6b66\u5b66|\u6d17\u9ad3\u7b26|swapneigong|\u6362\u5185\u529f|swapqinggong|\u6362\u8f7b\u529f|swapmartial|\u6362\u6b66\u529f|secttoken|\u6362\u5b97\u4ee4|reroll|\u6d17\u6b66\u5b66|reroll3|\u9ad8\u7ea7\u6d17\u6b66\u5b66|\u81ea\u9009\u6362\u6b66\u5b66|rerollneigong3|\u9ad8\u7ea7\u6d17\u5185\u529f|\u81ea\u9009\u6362\u5185\u529f|rerollqinggong3|\u9ad8\u7ea7\u6d17\u8f7b\u529f|\u81ea\u9009\u6362\u8f7b\u529f|choicecroll|\u5929\u673a\u6b8b\u5377\u81ea\u9009|\u5929\u673a\u6b8b\u5377|pick|\u9009\u62e9\u6b66\u5b66|c|challenge|\u6392\u4f4d\u6311\u6218|fc|\u6311\u6218|fc3|\u6311\u62183|a|accept|\u63a5\u53d7|r|reject|\u62d2\u7edd|rank|\u6392\u4f4d\u699c|team3|\u4e09\u4eba\u961f\u4f0d|teamorder|\u961f\u4f0d\u987a\u5e8f|t3|\u6392\u4f4d\u6311\u62183|a3|\u63a5\u53d73|r3|\u62d2\u7edd3|rank3|\u4e09\u6392\u699c|bossopen|boss|bossfight|bossrank|bossclose|bosssettle|daysettle|\u65e5\u699c\u7ed3\u7b97|weeksettle|weeklysettle|\u5468\u699c\u7ed3\u7b97)(?:\s|$)', priority=-10)
    async def regex_fallback(self, event: AstrMessageEvent):
        event.stop_event()


