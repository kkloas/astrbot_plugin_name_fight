# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

HELP_LINES = [
    '\u53ef\u7528\u6307\u4ee4:',
    '/fhelp - \u67e5\u770b\u5168\u90e8\u6307\u4ee4\u8bf4\u660e',
    '/create \u89d2\u8272\u540d - \u521b\u5efa\u65b0\u89d2\u8272\uff1b\u82e5\u540d\u4e0b\u5df2\u6ee1 3 \u4eba\uff0c\u5219\u8fdb\u5165\u9876\u66ff\u9009\u62e9',
    '/choose \u5e8f\u53f7 - \u5728\u5019\u9009\u89d2\u8272\u51fa\u73b0\u540e\uff0c\u9009\u62e9\u8981\u88ab\u9876\u66ff\u7684\u65e7\u89d2\u8272\u680f\u4f4d',
    '/roster - \u67e5\u770b\u4f60\u5f53\u524d\u540d\u4e0b\u5168\u90e8\u89d2\u8272',
    '/use \u89d2\u8272\u540d - \u5207\u6362\u5f53\u524d\u51fa\u6218\u89d2\u8272',
    '/profile [\u89d2\u8272\u540d] - \u67e5\u770b\u81ea\u5df1\u7684\u89d2\u8272\u8be6\u60c5\uff1b\u4e0d\u586b\u540d\u5b57\u65f6\u67e5\u770b\u89d2\u8272\u680f',
    '/c \u89d2\u8272\u540d - \u5411\u76ee\u6807\u89d2\u8272\u53d1\u8d77\u6b63\u5e38\u6311\u6218\uff0c\u7b49\u5f85\u5bf9\u65b9 /a \u6216 /r',
    '/fc \u89d2\u8272\u540d - \u76f4\u63a5\u5f3a\u5236\u5f00\u6218\uff0c\u4e0d\u9700\u8981\u5bf9\u65b9\u786e\u8ba4',
    '/a - \u63a5\u53d7\u522b\u4eba\u53d1\u6765\u7684\u6311\u6218',
    '/r - \u62d2\u7edd\u522b\u4eba\u53d1\u6765\u7684\u6311\u6218',
    '/rank - \u67e5\u770b\u5f53\u524d\u7fa4\u7684\u5dc5\u5cf0\u6392\u884c\u699c',
]

OUTCOME_PREFIXES = (
    '胜负已分',
    '随着最后一声',
    '一番激战过后',
    '尘埃落定',
    '久战不下',
    '这一战斗到真气近枯',
    '鏖战至上限后',
    '不过五手',
    '这一战结束得比热茶变温还快',
    '转眼之间',
    '从头到尾都被压着打',
    '这一战几乎尽在',
    '这一战打到最后',
    '两人都已逼近极限',
    '胜负只在一线之间',
    '两人一路缠斗到推演上限',
    '这一战拖得极久',
    '打到最后已经不是谁更猛',
    '这一架打得难解难分',
    '两人鏖战良久',
    '这场对决从头咬到尾',
)

EFFECT_LABELS = {
    'stunned': '\u7729\u6655',
    'slowed': '\u8fdf\u7f13',
    'bleeding': '\u51fa\u8840',
    'weakened': '\u865a\u5f31',
    'disarmed': '\u7f34\u68b0',
    'armor_broken': '\u7834\u7532',
}


def stat_comment(stat: str, value: float) -> str:
    if stat == 'hp':
        if value >= 620:
            return '\u6c14\u8840\u5982\u8679'
        if value >= 520:
            return '\u6839\u57fa\u6df1\u539a'
        if value >= 420:
            return '\u5185\u606f\u8fde\u7ef5'
        return '\u672c\u5143\u7a0d\u6b20'
    if stat == 'atk':
        if value >= 100:
            return '\u6240\u5411\u62ab\u9761'
        if value >= 85:
            return '\u950b\u8292\u6bd5\u9732'
        if value >= 70:
            return '\u84c4\u52bf\u6210\u52b2'
        return '\u5b88\u62d9\u6c42\u7a33'
    if stat == 'def':
        if value >= 95:
            return '\u4e0d\u52a8\u5982\u5c71'
        if value >= 80:
            return '\u5b88\u52bf\u6c89\u96c4'
        if value >= 65:
            return '\u4e25\u9635\u4ee5\u5f85'
        return '\u8f7b\u7532\u8584\u9635'
    if stat == 'spd':
        if value >= 72:
            return '\u8ffd\u98ce\u9010\u7535'
        if value >= 58:
            return '\u8eab\u8f7b\u5982\u71d5'
        if value >= 45:
            return '\u8fdb\u9000\u6709\u5ea6'
        return '\u6b65\u5c65\u6c89\u7a33'
    if stat == 'crt':
        if value >= 24:
            return '\u6740\u673a\u70bd\u76db'
        if value >= 18:
            return '\u5947\u950b\u6697\u85cf'
        if value >= 12:
            return '\u5076\u9732\u5ce5\u5d58'
        return '\u7a33\u4e2d\u6c42\u80dc'
    if stat == 'eva':
        if value >= 28:
            return '\u98d8\u6e3a\u96be\u6d4b'
        if value >= 22:
            return '\u95ea\u8f6c\u817e\u632a'
        if value >= 16:
            return '\u8f6c\u5708\u81ea\u5982'
        return '\u820d\u907f\u5c31\u6321'
    return ''


def star_line(fighter: dict[str, Any]) -> str:
    rating = max(1.0, min(5.0, float(fighter.get('star_rating', 3.0))))
    full_stars = int(rating)
    has_half = (rating - full_stars) >= 0.5
    stars = '\u2605' * full_stars + ('\u2606' if has_half else '')
    return f'\u8d44\u8d28: {stars}\uff08{rating:.1f}\u661f\uff09'


def _effect_labels(martial_art: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for move in martial_art.get('moves', []):
        for effect in move.get('effects', []):
            label = EFFECT_LABELS.get(effect.get('type'))
            if label and label not in found:
                found.append(label)
    return found


def _martial_flavor(martial_art: dict[str, Any]) -> str:
    weapon_type = martial_art.get('type', '')
    modifiers = martial_art.get('stat_modifiers', {})
    atk = float(modifiers.get('atk', 1.0))
    spd = float(modifiers.get('spd', 1.0))
    if weapon_type == 'sword':
        return '\u5251\u8def\u98d8\u5ffd' if spd >= 1.08 else '\u5251\u8def\u7ef5\u5bc6'
    if weapon_type == 'blade':
        return '\u5200\u52bf\u51cc\u5389' if atk >= 1.08 else '\u5200\u8def\u8fde\u7ef5'
    if weapon_type == 'palm':
        return '\u638c\u52b2\u6c89\u96c4'
    if weapon_type == 'leg':
        return '\u817f\u5f71\u903c\u4eba'
    if weapon_type == 'staff':
        return '\u957f\u5175\u538b\u9635'
    if weapon_type == 'short_weapon':
        return '\u62db\u8def\u522b\u81f4'
    return '\u62db\u5f0f\u6210\u5957'


def _martial_mechanics(martial_art: dict[str, Any]) -> str:
    modifiers = martial_art.get('stat_modifiers', {})
    atk = float(modifiers.get('atk', 1.0))
    spd = float(modifiers.get('spd', 1.0))
    crt = float(modifiers.get('crt', 1.0))
    eva = float(modifiers.get('eva', 1.0))
    parts: list[str] = []
    if atk >= 1.12:
        parts.append('\u4f24\u5bb3\u51f6\u731b')
    elif atk >= 1.06:
        parts.append('\u6740\u4f24\u4e0d\u4fd7')
    if spd >= 1.1:
        parts.append('\u51fa\u624b\u4e89\u5148')
    elif spd <= 0.97:
        parts.append('\u8282\u594f\u6c89\u7a33')
    if crt >= 1.1:
        parts.append('\u66f4\u6613\u91cd\u51fb')
    if eva >= 1.05:
        parts.append('\u5468\u65cb\u66f4\u7075')
    effects = _effect_labels(martial_art)
    if effects:
        parts.append('\u53ef' + '\u3001'.join(effects))
    if not parts:
        parts.append('\u62db\u5f0f\u5747\u8861')
    return '\uff0c'.join(parts[:3])


def _neigong_flavor(neigong: dict[str, Any]) -> str:
    hp = float(neigong.get('hp_multiplier', 1.0))
    defense = float(neigong.get('def_multiplier', 1.0))
    passives = neigong.get('passives', [])
    passive_types = {item.get('type') for item in passives}
    if 'regeneration' in passive_types:
        return '\u6c14\u606f\u7ef5\u957f'
    if 'vampirism' in passive_types:
        return '\u6c14\u673a\u8083\u6740'
    if 'thorns' in passive_types:
        return '\u62a4\u4f53\u51dd\u5b9e'
    if hp >= 1.15 and defense >= 1.08:
        return '\u6839\u57fa\u6df1\u539a'
    if defense >= 1.12:
        return '\u62a4\u4f53\u6c89\u7a33'
    return '\u8c03\u606f\u51dd\u6c14'


def _neigong_mechanics(neigong: dict[str, Any]) -> str:
    hp = float(neigong.get('hp_multiplier', 1.0))
    defense = float(neigong.get('def_multiplier', 1.0))
    passives = neigong.get('passives', [])
    passive_types = {item.get('type') for item in passives}
    guards = neigong.get('part_guard', {})
    parts: list[str] = []
    if hp >= 1.15:
        parts.append('\u6c14\u8840\u66f4\u539a')
    elif hp >= 1.08:
        parts.append('\u6839\u57fa\u66f4\u7a33')
    if defense >= 1.18:
        parts.append('\u62a4\u4f53\u6781\u5f3a')
    elif defense >= 1.08:
        parts.append('\u5b88\u52bf\u66f4\u7a33')
    if 'regeneration' in passive_types:
        parts.append('\u53ef\u7f13\u6162\u56de\u8840')
    if 'vampirism' in passive_types:
        parts.append('\u53ef\u5438\u8840\u7eed\u547d')
    if 'thorns' in passive_types:
        parts.append('\u53ef\u53cd\u9707\u4f24\u654c')
    if guards and len(parts) < 3:
        favored = []
        if 'chest' in guards or 'abdomen' in guards:
            favored.append('\u80f8\u8179\u66f4\u8010\u6253')
        if 'arm' in guards or 'leg' in guards:
            favored.append('\u56db\u80a2\u66f4\u5584\u5378\u52b2')
        if 'head' in guards:
            favored.append('\u4e0a\u8def\u66f4\u7a33')
        for item in favored:
            if len(parts) < 3 and item not in parts:
                parts.append(item)
    if not parts:
        parts.append('\u8c03\u606f\u62a4\u4f53')
    return '\uff0c'.join(parts[:3])


def _qinggong_flavor(qinggong: dict[str, Any]) -> str:
    spd = float(qinggong.get('spd_multiplier', 1.0))
    eva = float(qinggong.get('eva_bonus', 0.0))
    if spd >= 1.12 and eva >= 8:
        return '\u6b65\u52bf\u8f7b\u7075'
    if spd >= 1.12:
        return '\u8eab\u6cd5\u8fc5\u6377'
    if eva >= 10:
        return '\u8eab\u5f62\u98d8\u5ffd'
    if spd < 1.0:
        return '\u4e0b\u76d8\u6c89\u7a33'
    return '\u6b65\u8f6c\u81ea\u5982'


def _qinggong_mechanics(qinggong: dict[str, Any]) -> str:
    spd = float(qinggong.get('spd_multiplier', 1.0))
    eva = float(qinggong.get('eva_bonus', 0.0))
    parts: list[str] = []
    if spd >= 1.12:
        parts.append('\u64c5\u957f\u62a2\u5148\u624b')
    elif spd >= 1.05:
        parts.append('\u51fa\u624b\u66f4\u5feb')
    elif spd < 1.0:
        parts.append('\u6b65\u8c03\u66f4\u7a33')
    if eva >= 10:
        parts.append('\u95ea\u907f\u63d0\u5347\u660e\u663e')
    elif eva >= 6:
        parts.append('\u517c\u987e\u907f\u950b')
    else:
        parts.append('\u66f4\u504f\u57fa\u7840\u8d70\u4f4d')
    return '\uff0c'.join(parts[:2])


def fighter_summary_lines(fighter: dict[str, Any], created: bool) -> list[str]:
    stats = fighter['stats']
    martial_art = fighter['martial_art']
    neigong = fighter['neigong']
    qinggong = fighter['qinggong']
    if created:
        opener = f'\u3010\u65b0\u89d2\u8272\u751f\u6210\u3011{fighter["name"]}\u521d\u5165\u6c5f\u6e56\uff0c\u540d\u518c\u5df2\u6210\u3002'
    else:
        opener = f'\u3010\u89d2\u8272\u67e5\u770b\u3011{fighter["name"]}\u7684\u5f53\u524d\u9762\u677f\u5982\u4e0b\u3002'
    lines = [opener, star_line(fighter)]
    lines.append(f'\u6b66\u5b66: \u3010{martial_art["name"]}\u3011{_martial_flavor(martial_art)}\uff0c{_martial_mechanics(martial_art)}\u3002')
    lines.append(f'\u5185\u529f: \u3010{neigong["name"]}\u3011{_neigong_flavor(neigong)}\uff0c{_neigong_mechanics(neigong)}\u3002')
    lines.append(f'\u8f7b\u529f: \u3010{qinggong["name"]}\u3011{_qinggong_flavor(qinggong)}\uff0c{_qinggong_mechanics(qinggong)}\u3002')
    lines.append(
        f'\u9762\u677f: \u6c14\u8840 {stats["hp"]}\u3010{stat_comment("hp", stats["hp"])}\u3011 '
        f'| \u653b\u51fb {stats["atk"]}\u3010{stat_comment("atk", stats["atk"])}\u3011 '
        f'| \u9632\u5fa1 {stats["def"]}\u3010{stat_comment("def", stats["def"])}\u3011'
    )
    lines.append(
        f'\u8eab\u6cd5: \u901f\u5ea6 {stats["spd"]:.1f}\u3010{stat_comment("spd", stats["spd"])}\u3011 '
        f'| \u66b4\u51fb {stats["crt"]:.1f}%\u3010{stat_comment("crt", stats["crt"])}\u3011 '
        f'| \u95ea\u907f {stats["eva"]:.1f}%\u3010{stat_comment("eva", stats["eva"])}\u3011'
    )
    return lines


def roster_message(fighters: list[dict[str, Any]], max_fighters: int) -> str:
    if not fighters:
        return '\u4f60\u5f53\u524d\u8fd8\u6ca1\u6709\u4efb\u4f55\u89d2\u8272\u3002\u5148\u7528 /create \u89d2\u8272\u540d \u521b\u5efa\u4e00\u4e2a\u3002'
    lines = ['\u3010\u89d2\u8272\u680f\u3011']
    for fighter in fighters:
        active = ' [\u5f53\u524d\u51fa\u6218]' if fighter.get('is_active') else ''
        lines.append(
            f'{fighter["slot_index"]}. {fighter["name"]}{active} | {fighter["martial_art"]["name"]} | {star_line(fighter)}'
        )
    lines.append(f'\u5171 {len(fighters)}/{max_fighters} \u540d\u89d2\u8272\u3002\u53ef\u7528 /use \u89d2\u8272\u540d \u5207\u6362\u51fa\u6218\u89d2\u8272\u3002')
    return '\n'.join(lines)


def pending_replace_message(new_name: str, fighters: list[dict[str, Any]], timeout_seconds: int) -> str:
    lines = [
        f'\u3010\u65b0\u547d\u683c\u663e\u73b0\u3011\u4f60\u62bd\u5230\u4e86\u4e00\u540d\u5019\u9009\u89d2\u8272\u3010{new_name}\u3011\u3002\u8bf7\u5728\u4fdd\u7559\u524d\u5148\u67e5\u770b\u5176\u8be6\u60c5\u3002',
        f'\u8bf7\u5728 {timeout_seconds} \u79d2\u5185\u4f7f\u7528 /choose \u5e8f\u53f7 \u9009\u62e9\u8981\u9876\u66ff\u7684\u65e7\u89d2\u8272\uff1a',
    ]
    for fighter in fighters:
        lines.append(f'{fighter["slot_index"]}. {fighter["name"]} | {fighter["martial_art"]["name"]}')
    lines.append('\u82e5\u8d85\u65f6\u672a\u9009\u62e9\uff0c\u672c\u6b21\u5019\u9009\u5c06\u81ea\u52a8\u4f5c\u5e9f\u3002')
    return '\n'.join(lines)


def battle_overview_line(attacker: dict[str, Any], defender: dict[str, Any]) -> str:
    a = attacker['stats']
    d = defender['stats']
    return (
        f'\u5bf9\u9635: {attacker["name"]}[{attacker["martial_art"]["name"]}/{attacker["neigong"]["name"]}/{attacker["qinggong"]["name"]}] '
        f'\u6c14\u8840{a["hp"]} \u653b\u51fb{a["atk"]} \u9632\u5fa1{a["def"]} \u901f\u5ea6{a["spd"]:.1f} \u66b4\u51fb{a["crt"]:.1f}% \u95ea\u907f{a["eva"]:.1f}% | '
        f'{defender["name"]}[{defender["martial_art"]["name"]}/{defender["neigong"]["name"]}/{defender["qinggong"]["name"]}] '
        f'\u6c14\u8840{d["hp"]} \u653b\u51fb{d["atk"]} \u9632\u5fa1{d["def"]} \u901f\u5ea6{d["spd"]:.1f} \u66b4\u51fb{d["crt"]:.1f}% \u95ea\u907f{d["eva"]:.1f}%'
    )


def is_outcome_line(line: str) -> bool:
    return line.startswith(OUTCOME_PREFIXES)


def compact_battle_logs(logs: list[str]) -> list[str]:
    if not logs:
        return []
    compacted = [logs[0]]
    current_turn: list[str] = []
    for line in logs[2:]:
        if line.startswith('\u3010\u7b2c'):
            if current_turn:
                compacted.append(' '.join(current_turn))
            current_turn = [line]
            continue
        if is_outcome_line(line):
            if current_turn:
                compacted.append(' '.join(current_turn))
                current_turn = []
            compacted.append(line)
            continue
        if current_turn:
            current_turn.append(line)
        else:
            compacted.append(line)
    if current_turn:
        compacted.append(' '.join(current_turn))
    return compacted


def join_lines(lines: list[str]) -> str:
    return '\n'.join(lines)


def _leaderboard_honor(index: int) -> str:
    honors = {
        1: '\u699c\u9996',
        2: '\u6b21\u5e2d',
        3: '\u63a2\u82b1',
    }
    return honors.get(index, '')


def _peak_title(score: float) -> tuple[str, str]:
    if score < 1000:
        return '\u864e\u843d\u5e73\u9633', '\u6389\u5206\u6df1\u6e0a'
    if score < 1100:
        return '\u94e9\u7fbd\u800c\u5f52', '\u53d7\u632b\u82e6\u6218'
    if score < 1200:
        return '\u9006\u6c34\u884c\u821f', '\u74f6\u9888\u6323\u624e'
    if score < 1250:
        return '\u9010\u9e7f\u6c5f\u6e56', '\u5b9a\u7ea7\u57fa\u51c6'
    if score < 1300:
        return '\u950b\u8292\u6bd5\u9732', '\u7a81\u7834\u91cd\u56f4'
    if score < 1350:
        return '\u6280\u9ad8\u4e00\u7b79', '\u7a33\u6b65\u8fde\u80dc'
    if score < 1400:
        return '\u52bf\u5982\u7834\u7af9', '\u624b\u611f\u706b\u70ed'
    if score < 1450:
        return '\u529b\u538b\u7fa4\u96c4', '\u5b97\u5e08\u7edf\u6cbb'
    if score < 1500:
        return '\u51a0\u7edd\u5f53\u4e16', '\u6700\u5f3a\u738b\u8005'
    return '\u72ec\u5b64\u6c42\u8d25', '\u6b66\u6797\u795e\u8bdd'


def leaderboard_message(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return '\u3010\u7fa4\u5185\u5dc5\u5cf0\u6392\u884c\u699c\u3011\n\u5f53\u524d\u7fa4\u8fd8\u6ca1\u6709\u4efb\u4f55\u5bf9\u6218\u8bb0\u5f55\u3002'
    lines = ['\u3010\u7fa4\u5185\u5dc5\u5cf0\u6392\u884c\u699c Top 10\u3011']
    for index, entry in enumerate(entries, start=1):
        honor = _leaderboard_honor(index)
        title, _tag = _peak_title(float(entry['elo_rating']))
        if honor:
            lines.append(f'{honor}-{entry["fighter_name"]}-{title}')
            lines.append(
                f'{entry["elo_rating"]:.2f} | \u80dc\u573a {entry["wins"]} | \u5bf9\u6218 {entry["battles"]} | \u80dc\u7387 {entry["win_rate"]:.1f}%'
            )
        else:
            lines.append(
                f'{index}. {entry["fighter_name"]} | {entry["elo_rating"]:.2f} | {title} | \u80dc\u573a {entry["wins"]} | \u5bf9\u6218 {entry["battles"]} | \u80dc\u7387 {entry["win_rate"]:.1f}%'
            )
    return '\n'.join(lines)
