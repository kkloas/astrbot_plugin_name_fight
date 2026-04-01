from __future__ import annotations

import sys
import time

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

PROMPT = 'QQ> '
DELAY = 1.6 if sys.stdin.isatty() else 0.0
PENDING_CREATE_TIMEOUT = 60.0


def print_with_delay(lines: list[str], delay: float = DELAY) -> None:
    for index, line in enumerate(lines):
        print(line)
        if index + 1 < len(lines):
            time.sleep(delay)


def print_help() -> None:
    print(join_lines(HELP_LINES + ['/devfight 名字A 名字B', '/login 用户ID', '/help', '/exit']))


def require_login(current_user: str | None) -> bool:
    if current_user is None:
        print('请先用 /login 用户ID 进入当前账号。')
        return False
    return True


def run_battle(repo: FighterRepository, engine: CombatEngine, attacker: dict, defender: dict) -> None:
    print('【对决开始】本场挑战已被接受。')
    time.sleep(DELAY)
    print(battle_overview_line(attacker, defender))
    time.sleep(DELAY)
    logs, winner_name = engine.battle_with_result(attacker, defender)
    print_with_delay(compact_battle_logs(logs))
    repo.record_group_battle('sim_group', attacker['name'], defender['name'], winner_name)
    print('【对决结束】本场记录已写入排行榜。')


def main() -> None:
    print('=== QQ群文字格斗模拟器 ===')
    print('输入 /help 查看可用指令。')
    repo = FighterRepository()
    engine = CombatEngine()
    current_user: str | None = None
    pending_challenges: dict[str, dict[str, str]] = {}
    pending_creations: dict[str, dict] = {}

    while True:
        try:
            raw = input(PROMPT).strip()
        except EOFError:
            print()
            break
        if not raw:
            continue
        if raw in ('/exit', 'exit', 'quit'):
            break
        if raw in ('/help', '/fhelp'):
            print_help()
            continue
        if raw.startswith('/login '):
            current_user = raw.split(maxsplit=1)[1].strip()
            print(f'当前已切换到用户【{current_user}】。')
            continue
        if raw == '/roster':
            if not require_login(current_user):
                continue
            print(roster_message(repo.get_user_fighters(current_user), MAX_FIGHTERS_PER_USER))
            continue
        if raw.startswith('/use '):
            if not require_login(current_user):
                continue
            name = raw.split(maxsplit=1)[1].strip()
            try:
                fighter = repo.set_active_fighter(current_user, name)
                print(f'当前出战角色已切换为【{fighter["name"]}】。')
            except ValueError as exc:
                print(str(exc))
            continue
        if raw == '/profile':
            if not require_login(current_user):
                continue
            print(roster_message(repo.get_user_fighters(current_user), MAX_FIGHTERS_PER_USER))
            continue
        if raw.startswith('/profile '):
            if not require_login(current_user):
                continue
            name = raw.split(maxsplit=1)[1].strip()
            fighter = repo.get_fighter_by_name(name)
            owned = repo.get_user_fighter_by_name(current_user, name)
            if fighter is None or owned is None:
                print('你名下没有这个角色。')
            else:
                print(join_lines(fighter_summary_lines(fighter, False)))
            continue
        if raw.startswith('/create '):
            if not require_login(current_user):
                continue
            new_name = raw.split(maxsplit=1)[1].strip()
            pending_creations.pop(current_user, None)
            roster = repo.get_user_fighters(current_user)
            if len(roster) >= MAX_FIGHTERS_PER_USER:
                try:
                    fighter = repo.generate_preview_fighter(new_name)
                except ValueError as exc:
                    print(str(exc))
                    continue
                pending_creations[current_user] = {
                    'fighter': fighter,
                    'expires_at': time.monotonic() + PENDING_CREATE_TIMEOUT,
                }
                print(join_lines(fighter_summary_lines(fighter, True) + [pending_replace_message(new_name, roster, int(PENDING_CREATE_TIMEOUT))]))
            else:
                try:
                    fighter = repo.create_fighter_for_user(current_user, new_name)
                    print(join_lines(fighter_summary_lines(fighter, True)))
                except ValueError as exc:
                    print(str(exc))
            continue
        if raw.startswith('/choose '):
            if not require_login(current_user):
                continue
            part = raw.split(maxsplit=1)[1].strip()
            if not part.isdigit():
                print('用法: /choose 序号')
                continue
            pending = pending_creations.get(current_user)
            if pending is None or pending['expires_at'] < time.monotonic():
                pending_creations.pop(current_user, None)
                print('你当前没有待确认的候选角色。')
                continue
            slot_index = int(part)
            try:
                old_name, fighter = repo.replace_fighter_for_user(current_user, slot_index, prepared_fighter=pending['fighter'])
                pending_creations.pop(current_user, None)
                print(join_lines([
                    f'【角色更替】已由【{fighter["name"]}】顶替【{old_name}】入列，并自动设为当前出战角色。',
                    *fighter_summary_lines(fighter, False),
                ]))
            except ValueError as exc:
                print(str(exc))
            continue
        if raw.startswith('/c ') or raw.startswith('/challenge '):
            if not require_login(current_user):
                continue
            target = raw.split(maxsplit=1)[1].strip()
            challenger = repo.get_active_fighter(current_user)
            if challenger is None:
                print('你还没有可出战角色，请先创建并选择角色。')
                continue
            defender = repo.get_fighter_by_name(target)
            if defender is None:
                print('目标角色不存在，无法发起挑战。')
                continue
            owner_id = repo.get_owner_user_id_by_fighter_name(target)
            if owner_id is None:
                print('目标角色未绑定拥有者，暂时无法挑战。')
                continue
            if owner_id == current_user:
                print('不能挑战自己的角色。')
                continue
            pending_challenges[owner_id] = {
                'challenger_user_id': current_user,
                'challenger_label': current_user,
                'challenger_fighter_name': challenger['name'],
                'defender_fighter_name': defender['name'],
            }
            print(f'挑战已发出。【{challenger["name"]}】向【{defender["name"]}】下了战书。请对方使用 /a 接战，或用 /r 拒绝。')
            continue
        if raw.startswith('/fc '):
            if not require_login(current_user):
                continue
            target = raw.split(maxsplit=1)[1].strip()
            challenger = repo.get_active_fighter(current_user)
            if challenger is None:
                print('你还没有可出战角色，请先创建并选择角色。')
                continue
            defender = repo.get_fighter_by_name(target)
            if defender is None:
                print('目标角色不存在，无法发起挑战。')
                continue
            owner_id = repo.get_owner_user_id_by_fighter_name(target)
            if owner_id == current_user:
                print('不能挑战自己的角色。')
                continue
            run_battle(repo, engine, challenger, defender)
            continue
        if raw == '/a':
            if not require_login(current_user):
                continue
            challenge = pending_challenges.pop(current_user, None)
            if challenge is None:
                print('当前没有等待你回应的挑战。')
                continue
            attacker = repo.get_fighter_by_name(challenge['challenger_fighter_name'])
            defender = repo.get_fighter_by_name(challenge['defender_fighter_name'])
            if attacker is None or defender is None:
                print('挑战双方的角色信息不完整，本次挑战已作废。')
                continue
            run_battle(repo, engine, attacker, defender)
            continue
        if raw == '/r':
            if not require_login(current_user):
                continue
            challenge = pending_challenges.pop(current_user, None)
            if challenge is None:
                print('当前没有等待你拒绝的挑战。')
                continue
            print(f'【挑战作废】你拒绝了【{challenge["challenger_fighter_name"]}】发起的挑战。')
            continue
        if raw == '/rank':
            print(leaderboard_message(repo.get_group_leaderboard('sim_group', limit=10)))
            continue
        if raw.startswith('/devfight '):
            parts = raw.split()
            if len(parts) != 3:
                print('用法: /devfight 名字A 名字B')
                continue
            left = repo.get_fighter_by_name(parts[1])
            if left is None:
                left = repo.generate_preview_fighter(parts[1])
            right = repo.get_fighter_by_name(parts[2])
            if right is None:
                right = repo.generate_preview_fighter(parts[2])
            run_battle(repo, engine, left, right)
            continue
        print('无法识别的指令。输入 /help 查看帮助。')


if __name__ == '__main__':
    main()
