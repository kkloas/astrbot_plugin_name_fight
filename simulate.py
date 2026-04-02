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
    print('\u3010\u5bf9\u51b3\u5f00\u59cb\u3011\u672c\u573a\u6311\u6218\u5df2\u88ab\u63a5\u53d7\u3002')
    time.sleep(DELAY)
    print(battle_overview_line(attacker, defender))
    time.sleep(DELAY)
    logs, winner_name = engine.battle_with_result(attacker, defender)
    print_with_delay(compact_battle_logs(logs))
    repo.record_group_battle('sim_group', attacker['name'], defender['name'], winner_name)
    print('\u3010\u5bf9\u51b3\u7ed3\u675f\u3011\u672c\u573a\u8bb0\u5f55\u5df2\u5199\u5165\u6392\u884c\u699c\u3002')


def clone_fighter_with_hp(fighter: dict, hp: int) -> dict:
    clone = dict(fighter)
    clone['stats'] = dict(clone['stats'])
    clone['stats']['hp'] = max(1, int(hp))
    return clone


def is_turn_log_line(line: str) -> bool:
    return line.startswith('\u3010\u7b2c') and '\u624b\u3011' in line


def chunk_team3_battle_logs(duel_no: int, compacted_logs: list[str], chunk_size: int = 5) -> list[str]:
    if not compacted_logs:
        return []
    intro_lines: list[str] = []
    turn_lines: list[str] = []
    outcome_lines: list[str] = []
    for line in compacted_logs:
        if is_turn_log_line(line):
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

def format_team3_names(team: list[dict]) -> str:
    return ' / '.join(fighter['name'] for fighter in team)


def build_team3_battle_lines(engine: CombatEngine, attacker_label: str, attacker_team: list[dict], defender_label: str, defender_team: list[dict]) -> tuple[list[str], str | None]:
    lines = [f'\u30103v3\u9635\u5bb9\u3011{attacker_label}: {format_team3_names(attacker_team)} | {defender_label}: {format_team3_names(defender_team)}']
    attacker_index = 0
    defender_index = 0
    attacker_hp = int(attacker_team[0]['stats']['hp'])
    defender_hp = int(defender_team[0]['stats']['hp'])
    duel_no = 1

    while attacker_index < len(attacker_team) and defender_index < len(defender_team):
        attacker_fighter = clone_fighter_with_hp(attacker_team[attacker_index], attacker_hp)
        defender_fighter = clone_fighter_with_hp(defender_team[defender_index], defender_hp)
        logs, winner_name, state = engine.battle_with_state(attacker_fighter, defender_fighter)
        attacker_name = attacker_team[attacker_index]['name']
        defender_name = defender_team[defender_index]['name']
        lines.append(f'\u3010\u7b2c{duel_no}\u9635\u3011{attacker_label}\u00b7{attacker_name} vs {defender_label}\u00b7{defender_name}')
        lines.append(battle_overview_line(attacker_fighter, defender_fighter))
        lines.extend(chunk_team3_battle_logs(duel_no, compact_battle_logs(logs)))

        if winner_name == attacker_name:
            attacker_hp = int(state['fighter_a_hp'])
            lines.append(f'\u3010\u7b2c{duel_no}\u9635\u7ed3\u679c\u3011{attacker_name} \u51fb\u8d25 {defender_name}\uff0c\u5269\u4f59 {attacker_hp}/{state["fighter_a_max_hp"]} \u6c14\u8840\u3002')
            defender_index += 1
            if defender_index < len(defender_team):
                defender_hp = int(defender_team[defender_index]['stats']['hp'])
                lines.append(f'\u3010\u9635\u95f4\u627f\u63a5\u3011{attacker_name} \u7ee7\u7eed\u51fa\u6218\uff0c\u8fce\u6218 {defender_team[defender_index]["name"]}\u3002')
        elif winner_name == defender_name:
            defender_hp = int(state['fighter_b_hp'])
            lines.append(f'\u3010\u7b2c{duel_no}\u9635\u7ed3\u679c\u3011{defender_name} \u51fb\u8d25 {attacker_name}\uff0c\u5269\u4f59 {defender_hp}/{state["fighter_b_max_hp"]} \u6c14\u8840\u3002')
            attacker_index += 1
            if attacker_index < len(attacker_team):
                attacker_hp = int(attacker_team[attacker_index]['stats']['hp'])
                lines.append(f'\u3010\u9635\u95f4\u627f\u63a5\u3011{defender_name} \u7ee7\u7eed\u51fa\u6218\uff0c\u8fce\u6218 {attacker_team[attacker_index]["name"]}\u3002')
        else:
            lines.append(f'\u3010\u7b2c{duel_no}\u9635\u7ed3\u679c\u3011{attacker_name} \u4e0e {defender_name} \u540c\u5f52\u4e8e\u5c3d\uff0c\u53cc\u65b9\u5404\u6298\u4e00\u9635\u3002')
            attacker_index += 1
            defender_index += 1
            if attacker_index < len(attacker_team):
                attacker_hp = int(attacker_team[attacker_index]['stats']['hp'])
            if defender_index < len(defender_team):
                defender_hp = int(defender_team[defender_index]['stats']['hp'])
        duel_no += 1

    if attacker_index >= len(attacker_team) and defender_index >= len(defender_team):
        lines.append('\u30103v3\u7ed3\u679c\u3011\u53cc\u65b9\u4e09\u9635\u5168\u706d\uff0c\u672c\u573a\u4ee5\u5e73\u5c40\u544a\u7ec8\u3002')
        return lines, None
    if defender_index >= len(defender_team):
        lines.append(f'\u30103v3\u7ed3\u679c\u3011{attacker_label} \u4e09\u9635\u8fde\u6218\u80dc\u51fa\u3002')
        return lines, 'attacker'
    lines.append(f'\u30103v3\u7ed3\u679c\u3011{defender_label} \u4e09\u9635\u8fde\u6218\u80dc\u51fa\u3002')
    return lines, 'defender'


def run_team3_battle(repo: FighterRepository, engine: CombatEngine, attacker_label: str, attacker_team: list[dict], defender_label: str, defender_team: list[dict], write_rank: bool = True, attacker_user_id: str | None = None, defender_user_id: str | None = None) -> None:
    print('\u30103v3 \u5bf9\u51b3\u5f00\u59cb\u3011\u672c\u573a 3v3 \u8fde\u6218\u5df2\u5f00\u59cb\u3002')
    time.sleep(DELAY)
    lines, winner_side = build_team3_battle_lines(engine, attacker_label, attacker_team, defender_label, defender_team)
    print_with_delay(lines)
    if write_rank and attacker_user_id is not None and defender_user_id is not None:
        winner_user_id = None
        if winner_side == 'attacker':
            winner_user_id = attacker_user_id
        elif winner_side == 'defender':
            winner_user_id = defender_user_id
        change = repo.record_group_team3_battle('sim_group', attacker_user_id, attacker_label, defender_user_id, defender_label, winner_user_id)
        print(
            f'\u672c\u573a 3v3 \u5dc5\u5cf0\u5206\u53d8\u52a8: '
            f'{change["attacker"]["name"]} {change["attacker"]["delta"]:+.2f} '
            f'({change["attacker"]["before"]:.2f} -> {change["attacker"]["after"]:.2f}) | '
            f'{change["defender"]["name"]} {change["defender"]["delta"]:+.2f} '
            f'({change["defender"]["before"]:.2f} -> {change["defender"]["after"]:.2f})'
        )


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
        if raw.startswith('/fc3 '):
            if not require_login(current_user):
                continue
            parts = raw.split(maxsplit=1)
            if len(parts) != 2 or not parts[1].strip():
                print('\u7528\u6cd5: /fc3 \u7528\u6237ID')
                continue
            target_user_id = parts[1].strip()
            if target_user_id == current_user:
                print('\u4e0d\u80fd\u5411\u81ea\u5df1\u53d1\u8d77 3v3 \u5f3a\u5236\u5bf9\u51b3\u3002')
                continue
            attacker_team = repo.get_user_team3_fighters(current_user)
            defender_team = repo.get_user_team3_fighters(target_user_id)
            if len(attacker_team) < MAX_FIGHTERS_PER_USER:
                print('\u4f60\u5f53\u524d\u89d2\u8272\u672a\u6ee1 3 \u4e2a\uff0c\u6682\u65f6\u65e0\u6cd5\u53c2\u52a0 3v3\u3002')
                continue
            if len(defender_team) < MAX_FIGHTERS_PER_USER:
                print('\u76ee\u6807\u7528\u6237\u5f53\u524d\u672a\u51d1\u9f50 3 \u4e2a\u89d2\u8272\uff0c\u6682\u65f6\u65e0\u6cd5\u53c2\u52a0 3v3\u3002')
                continue
            run_team3_battle(repo, engine, current_user, attacker_team, target_user_id, defender_team, True, current_user, target_user_id)
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
        if raw.startswith('/devfight3 '):
            parts = raw.split()
            if len(parts) != 3:
                print('\u7528\u6cd5: /devfight3 \u524d\u7f00A \u524d\u7f00B')
                continue
            left_team = []
            right_team = []
            for index in range(1, 4):
                left_name = f'{parts[1]}{index}'
                right_name = f'{parts[2]}{index}'
                left = repo.get_fighter_by_name(left_name)
                if left is None:
                    left = repo.generate_preview_fighter(left_name)
                right = repo.get_fighter_by_name(right_name)
                if right is None:
                    right = repo.generate_preview_fighter(right_name)
                left_team.append(left)
                right_team.append(right)
            run_team3_battle(repo, engine, parts[1], left_team, parts[2], right_team, False)
            continue
        print('无法识别的指令。输入 /help 查看帮助。')


if __name__ == '__main__':
    main()
