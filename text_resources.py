# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

HELP_LINES = [
    '【指令导航】',
    '角色养成: /教程 /角色列表 /角色详情 /切换角色 /创建角色',
    '商店背包: /商店 /背包 /积分 /购买 道具名 数量',
    '3v3队伍: /三人队伍 /队伍顺序 2 1 3 /排位挑战3 @目标 /三排榜',
    '1v1对战: /排位挑战 角色名 /挑战 角色名 /接受 /拒绝 /排位榜',
    '世界BOSS: /boss /bosshelp /bossfight /bossquick /bosssim /bosssimquick',
    '管理员: /bossopen /bossclose /bosssettle /周榜结算 /日榜结算',
    '特殊召唤: /商店 查看道具，再用 /特殊召唤令 角色名',
    '提示: 想看具体道具效果用 /商店，想看 BOSS 规则和奖励用 /bosshelp。',
]

ITEM_USAGE_GUIDE = {
    '小星尘丹': '升星经验的小丹药。',
    '中星尘丹': '升星经验更多的丹药。',
    '破境丹': '让 5.0 星角色突破到 6.0 星。',
    '特殊召唤令': '90% 五星 / 10% 六星基础资质召唤。',
    '洗髓符': '随机更换 1 个武功。',
    '换宗令': '随机更换内功、轻功或武功。',
    '天机残卷': '生成 3 个候选供你自选。',
}

GUIDE_LINES = [
    '\u65b0\u624b\u6559\u7a0b:',
    '1. \u5148\u521b\u5efa\u89d2\u8272: /\u521b\u5efa\u89d2\u8272 \u89d2\u8272\u540d',
    '2. \u67e5\u770b\u540d\u4e0b\u89d2\u8272\u5e76\u5207\u6362\u51fa\u6218: /\u89d2\u8272\u5217\u8868, /\u5207\u6362\u89d2\u8272 \u89d2\u8272\u540d',
    '3. \u901a\u8fc7\u6b63\u5e38\u5bf9\u6218\u8d5a\u79ef\u5206: 1v1 \u7528 /\u6392\u4f4d\u6311\u6218 \u89d2\u8272\u540d, 3v3 \u7528 /\u6392\u4f4d\u6311\u62183 @\u76ee\u6807',
    '4. \u6bcf\u5929\u8bb0\u5f97\u7b7e\u5230: /\u7b7e\u5230',
    '5. \u67e5\u770b\u79ef\u5206\u548c\u5546\u5e97: /\u79ef\u5206, /\u5546\u5e97',
    '6. \u8d2d\u4e70\u5e76\u67e5\u770b\u9053\u5177: /\u8d2d\u4e70 \u9053\u5177\u540d \u6570\u91cf, /\u80cc\u5305',
    '7. \u7528\u661f\u7ecf\u9a8c\u4e39\u57f9\u517b\u89d2\u8272: /\u5582\u517b \u89d2\u8272\u540d \u9053\u5177\u540d [\u6570\u91cf]',
    '8. \u89d2\u8272\u5230 5.0 \u661f\u540e\u53ef\u7a81\u7834\u5230 6.0 \u661f: /\u7a81\u7834 \u89d2\u8272\u540d',
    '9. \u60f3\u6362\u6d41\u6d3e\u53ef\u76f4\u63a5\u7528\u9053\u5177\u547d\u4ee4: /\u968f\u673a\u6362\u6b66\u5b66, /\u6362\u5185\u529f, /\u6362\u8f7b\u529f, /\u6362\u6b66\u529f, /\u81ea\u9009\u6362\u6b66\u5b66, /\u9ad8\u7ea7\u6d17\u5185\u529f, /\u9ad8\u7ea7\u6d17\u8f7b\u529f, /\u9009\u62e9\u6b66\u5b66',
    '10. \u60f3\u7ed9\u670b\u53cb\u8f6c\u79ef\u5206: /\u8d60\u9001 @\u5bf9\u65b9 100',
    '',
    '\u517b\u6210\u4e3b\u7ebf:',
    '\u521b\u5efa\u89d2\u8272 -> \u6392\u4f4d\u6311\u6218\u8d5a\u79ef\u5206 -> \u5546\u5e97\u4e70\u9053\u5177 -> \u5582\u7ecf\u9a8c\u8865\u5230 5 \u661f -> \u7a81\u7834 6 \u661f -> \u6d17\u6b66\u5b66\u4f18\u5316',
    '',
    '\u9053\u5177\u8bf4\u660e:',
    '- \u5c0f\u661f\u5c18\u4e39 / \u4e2d\u661f\u5c18\u4e39: \u63d0\u4f9b\u661f\u7ecf\u9a8c\uff0c\u7528\u6765\u628a\u4f4e\u661f\u89d2\u8272\u8865\u5230 5 \u661f',
    '- \u7834\u5883\u4e39: \u53ea\u80fd\u5bf9 5.0 \u661f\u89d2\u8272\u4f7f\u7528\uff0c\u4f7f\u5176\u7a81\u7834\u5230 6.0 \u661f',
    '- \u6d17\u9ad3\u7b26: \u5168\u6b66\u5b66\u6c60\u968f\u673a\u6362\u6b66\u5b66\uff0c\u547d\u4ee4\u4e3a /\u968f\u673a\u6362\u6b66\u5b66 \u89d2\u8272\u540d',
    '- \u6362\u5b97\u4ee4: \u6307\u5b9a\u66ff\u6362 \u5185\u529f\u3001\u8f7b\u529f \u6216 \u6b66\u529f \u4e2d\u7684 1 \u7c7b\uff0c\u968f\u673a\u6362 1 \u4e2a',
    '- \u5929\u673a\u6b8b\u5377: \u53ef\u4ee5\u7528\u6765\u81ea\u9009 \u6b66\u529f\u3001\u5185\u529f \u6216 \u8f7b\u529f\uff0c\u6bcf\u6b21\u5148\u751f\u6210 3 \u4e2a\u5019\u9009\uff0c\u518d\u7528 /\u9009\u62e9\u6b66\u5b66 1|2|3 \u786e\u5b9a',
    '',
    '\u5173\u952e\u89c4\u5219:',
    '- 1.0 \u5230 5.0 \u661f\u5c5e\u4e8e\u57fa\u7840\u8d44\u8d28\u4f53\u7cfb\uff0c\u540e\u5929\u8865\u5230 5.0 \u661f\u540e\u4e0e\u5148\u5929 5.0 \u661f\u7b49\u4ef7',
    '- \u5f53\u524d\u7248\u672c\u4e0a\u9650\u662f 6.0 \u661f\uff0c\u53ea\u6709\u5230 5.0 \u661f\u540e\u624d\u80fd\u7a81\u7834',
    '- \u6392\u4f4d\u6311\u6218\u4f1a\u4ea7\u51fa\u79ef\u5206\uff0c\u5e76\u6309\u5bf9\u624b\u5f3a\u5ea6\u7ed9\u6311\u6218\u5956\u52b1',
    '- /\u6311\u6218 \u548c /\u6311\u62183 \u53ea\u7528\u4e8e\u5a31\u4e50\uff0c\u4e0d\u4ea7\u79ef\u5206\uff0c\u53ea\u8bb0\u5f55 2/5 \u5e45\u5ea6\u7684\u8f7b\u91cf ELO \u53d8\u5316',
    '- \u6d17\u6b66\u5b66\u53ea\u6539\u6b66\u5b66\uff0c\u4e0d\u4f1a\u91cd\u7f6e\u4f60\u7684\u8865\u661f\u548c\u7a81\u7834\u8fdb\u5ea6',
    '- \u5468\u699c\u7ed3\u7b97\u53ef\u53d1\u653e\u989d\u5916\u79ef\u5206\u548c\u7a00\u6709\u6d17\u7ec3\u9053\u5177',
    '',
    '\u4e16\u754cBOSS\u73a9\u6cd5:',
    '- \u7ba1\u7406\u5458\u5148\u7528 /bossopen \u5f00\u542f\u672c\u7fa4\u4e16\u754cBOSS\u6d3b\u52a8',
    '- \u73a9\u5bb6\u7528 /boss \u67e5\u770b\u5f53\u524d\u72b6\u6001\u3001\u5171\u4eab\u4e8c\u9636\u6bb5\u8840\u91cf\u548c\u81ea\u5df1\u4eca\u65e5\u5269\u4f59\u6b21\u6570',
    '- \u73a9\u5bb6\u7528\u5f53\u524d 3v3 \u9635\u5bb9\u6267\u884c /bossfight \u6311\u6218',
    '- \u5982\u679c\u53ea\u60f3\u770b\u7ed3\u8bba\uff0c\u53ef\u76f4\u63a5\u7528 /bossquick \u8d70\u5feb\u901f\u6458\u8981\u7248\u5b9e\u6218',
    '- \u5f00\u6253\u524d\u53ef\u5148\u7528 /bosssim\u3001/bosssim phase1\u3001/bosssim phase2 \u6f14\u7ec3\u961f\u4f0d\uff0c\u4e0d\u6263\u6b21\u6570\u4e5f\u4e0d\u5199\u5171\u4eab\u8840\u91cf',
    '- \u53ea\u60f3\u770b\u6458\u8981\u6a21\u62df\u7ed3\u679c\uff0c\u53ef\u7528 /bosssimquick\u3001/bosssimquick phase1\u3001/bosssimquick phase2',
    '- \u6bcf\u6b21\u6311\u6218\u90fd\u4f1a\u5148\u6253\u4e00\u9636\u6bb5\u95e8\u69db\uff0c\u53ea\u6709\u6253\u8fdb\u4e8c\u9636\u6bb5\u540e\u7684\u4f24\u5bb3\u624d\u4f1a\u8ba1\u5165\u5171\u4eab\u8840\u91cf\u548c\u8d21\u732e\u699c',
    '- \u6bcf\u4eba\u6bcf\u5929\u9ed8\u8ba4 3 \u6b21\u4e16\u754cBOSS\u6311\u6218\u6b21\u6570',
    '- \u7528 /bossrank \u67e5\u770b\u8d21\u732e\u699c\uff1b\u51fb\u6740\u540e\u53ef\u7528 /bosssettle \u67e5\u770b\u7ed3\u7b97\uff1b\u82e5\u6d3b\u52a8\u4f5c\u5e9f\u53ef\u7528 /bossclose \u5173\u95ed',
    '',
    '\u7279\u6b8a\u53ec\u5524:',
    '- \u5546\u5e97\u65b0\u589e\u300c\u7279\u6b8a\u53ec\u5524\u4ee4\u300d\uff0c\u552e\u4ef7 1000 \u79ef\u5206',
    '- \u5148\u7528 /\u8d2d\u4e70 \u7279\u6b8a\u53ec\u5524\u4ee4 1 \u8d2d\u5165\uff0c\u518d\u7528 /\u7279\u6b8a\u53ec\u5524 \u89d2\u8272\u540d \u6d88\u8017',
    '- \u53ec\u5524\u89d2\u8272\u53ef\u4ee5\u81ea\u5df1\u547d\u540d\uff0c\u57fa\u7840\u8d44\u8d28\u6309 90% \u4e94\u661f / 10% \u516d\u661f \u51b3\u5b9a',
    '- \u6b66\u5b66\u3001\u5185\u529f\u3001\u8f7b\u529f\u4ecd\u6309\u6b63\u5e38\u968f\u673a\u6c60\u751f\u6210\uff0c\u82e5\u540d\u4e0b\u5df2\u6ee1\u5219\u7167\u65e7\u8d70\u9876\u66ff\u6d41\u7a0b',
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

STAR_REQUIREMENTS = {
    1.0: 100,
    1.5: 140,
    2.0: 190,
    2.5: 250,
    3.0: 330,
    3.5: 400,
    4.0: 450,
    4.5: 540,
}


def stat_comment(stat: str, value: float) -> str:
    if stat == 'hp':
        if value >= 760:
            return '\u5317\u51a5\u5316\u751f'
        if value >= 620:
            return '\u6c14\u8840\u5982\u8679'
        if value >= 520:
            return '\u6839\u57fa\u6df1\u539a'
        if value >= 420:
            return '\u5185\u606f\u8fde\u7ef5'
        return '\u672c\u5143\u7a0d\u6b20'
    if stat == 'atk':
        if value >= 140:
            return '\u648c\u5929\u52a8\u5730'
        if value >= 100:
            return '\u6240\u5411\u62ab\u9761'
        if value >= 85:
            return '\u950b\u8292\u6bd5\u9732'
        if value >= 70:
            return '\u84c4\u52bf\u6210\u52b2'
        return '\u5b88\u62d9\u6c42\u7a33'
    if stat == 'def':
        if value >= 130:
            return '\u82cd\u5c71\u8d1f\u96ea'
        if value >= 95:
            return '\u4e0d\u52a8\u5982\u5c71'
        if value >= 80:
            return '\u5b88\u52bf\u6c89\u96c4'
        if value >= 65:
            return '\u4e25\u9635\u4ee5\u5f85'
        return '\u8f7b\u7532\u8584\u9635'
    if stat == 'spd':
        if value >= 110:
            return '\u6d6e\u5149\u63a0\u5f71'
        if value >= 72:
            return '\u8ffd\u98ce\u9010\u7535'
        if value >= 58:
            return '\u8eab\u8f7b\u5982\u71d5'
        if value >= 45:
            return '\u8fdb\u9000\u6709\u5ea6'
        return '\u6b65\u5c65\u6c89\u7a33'
    if stat == 'crt':
        if value >= 36:
            return '\u767d\u8679\u8d2f\u65e5'
        if value >= 24:
            return '\u6740\u673a\u70bd\u76db'
        if value >= 18:
            return '\u5947\u950b\u6697\u85cf'
        if value >= 12:
            return '\u5076\u9732\u5ce5\u5d58'
        return '\u7a33\u4e2d\u6c42\u80dc'
    if stat == 'eva':
        if value >= 42:
            return '\u7fe9\u82e5\u60ca\u9e3f'
        if value >= 28:
            return '\u98d8\u6e3a\u96be\u6d4b'
        if value >= 22:
            return '\u95ea\u8f6c\u817e\u632a'
        if value >= 16:
            return '\u8f6c\u5708\u81ea\u5982'
        return '\u820d\u907f\u5c31\u6321'
    return ''


def star_line(fighter: dict[str, Any]) -> str:
    rating = float(fighter.get('star_rating', 3.0))
    if rating >= 6.0:
        return '资质: ★★★★★★（6.0星）'
    rating = max(1.0, min(5.0, rating))
    full_stars = int(rating)
    has_half = (rating - full_stars) >= 0.5
    stars = '★' * full_stars + ('☆' if has_half else '')
    return f'资质: {stars}（{rating:.1f}星）'


def growth_line(fighter: dict[str, Any]) -> str:
    base_star_raw = float(fighter.get('base_star_rating', fighter.get('star_rating', 3.0)))
    base_star = max(1.0, min(6.0, base_star_raw))
    current_star = float(fighter.get('star_rating', base_star))
    breakthrough_stage = int(fighter.get('breakthrough_stage', 0) or 0)
    if current_star >= 6.0 or breakthrough_stage > 0:
        if base_star >= 6.0 and breakthrough_stage <= 0:
            return '成长: 先天 6.0星 | 当前 6.0星 | 天生绝品'
        return f'成长: 先天 {min(base_star, 5.0):.1f}星 | 当前 6.0星 | 已突破'
    if current_star >= 5.0:
        return f'成长: 先天 {base_star:.1f}星 | 当前 5.0星 | 可突破'
    star_exp = int(fighter.get('star_exp', 0) or 0)
    requirement = STAR_REQUIREMENTS.get(round(current_star, 1), 0)
    return f'成长: 先天 {base_star:.1f}星 | 当前 {current_star:.1f}星 | 星经验 {star_exp}/{requirement}'


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
    if weapon_type == 'hidden_weapon':
        return '\u9488\u96e8\u593a\u547d'
    if weapon_type == 'musical_instrument':
        return '\u9b54\u97f3\u6444\u9b42'
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
    if martial_art.get('type') == 'hidden_weapon' and effects:
        parts = [item for item in parts if item != '\u5468\u65cb\u66f4\u7075']
        parts.append('\u53ef' + '\u3001'.join(effects[:3]))
    elif martial_art.get('type') == 'musical_instrument' and effects:
        parts.append('\u53ef' + '\u3001'.join(effects[:3]))
    elif effects:
        parts.append('\u53ef' + '\u3001'.join(effects))
    if not parts:
        parts.append('\u62db\u5f0f\u5747\u8861')
    return '\uff0c'.join(parts[:4])




def _martial_signature(martial_art: dict[str, Any]) -> str:
    martial_id = str(martial_art.get('id') or '')
    if martial_id == 'staff_bainiaochaofeng':
        return '\u7279\u6027\uff1a\u51fa\u624b\u4e89\u5148\uff0c\u53ef\u6d41\u8840\u3001\u7834\u7532'
    if martial_id == 'short_shenghuoling':
        return '\u7279\u6027\uff1a\u6b65\u6cd5\u8be1\u5947\uff0c\u53ef\u7f34\u68b0\u3001\u7729\u6655\u3001\u8fdf\u7f13'
    tags: list[str] = []
    modifiers = martial_art.get('stat_modifiers', {})
    if float(modifiers.get('spd', 1.0)) >= 1.1:
        tags.append('\u51fa\u624b\u4e89\u5148')
    if float(modifiers.get('atk', 1.0)) >= 1.12:
        tags.append('\u91cd\u624b\u7834\u9635')
    effects = _effect_labels(martial_art)
    if effects:
        tags.append('\u53ef' + '\u3001'.join(effects[:3]))
    if not tags:
        return ''
    return '\u7279\u6027\uff1a' + '\uff0c'.join(tags[:2])


def _profile_summary(entry: dict[str, Any], fallback: str) -> str:
    summary = str(entry.get('combat_summary') or '').strip()
    if not summary:
        return fallback
    return summary

def _neigong_flavor(neigong: dict[str, Any]) -> str:
    hp = float(neigong.get('hp_multiplier', 1.0))
    defense = float(neigong.get('def_multiplier', 1.0))
    passives = neigong.get('passives', [])
    passive_types = {item.get('type') for item in passives}
    if 'damage_defer' in passive_types:
        return '刚柔并济'
    if 'stacking_defense' in passive_types:
        return '紫气绵长'
    if 'part_counter' in passive_types:
        return '借力挪劲'
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
    if 'damage_defer' in passive_types:
        parts.append('可化爆发为内伤')
    if 'stacking_defense' in passive_types:
        parts.append('防御会越战越强')
    if 'part_counter' in passive_types:
        parts.append('四肢受击可反震')
    if 'burst_heal' in passive_types:
        parts.append('\u6b8b\u8840\u7206\u53d1\u56de\u8840')
    if 'crisis_defense' in passive_types:
        parts.append('\u6b8b\u8840\u9632\u5fa1\u63d0\u5347')
    if guards and len(parts) < 4:
        favored = []
        if 'chest' in guards or 'abdomen' in guards:
            favored.append('\u80f8\u8179\u66f4\u8010\u6253')
        if 'arm' in guards or 'leg' in guards:
            favored.append('\u56db\u80a2\u66f4\u5584\u5378\u52b2')
        if 'head' in guards:
            favored.append('\u4e0a\u8def\u66f4\u7a33')
        for item in favored:
            if len(parts) < 4 and item not in parts:
                parts.append(item)
    if not parts:
        parts.append('\u8c03\u606f\u62a4\u4f53')
    return '\uff0c'.join(parts[:4])



def _neigong_signature(neigong: dict[str, Any]) -> str:
    neigong_id = str(neigong.get('id') or '')
    if neigong_id == 'shenzhao_jing':
        return '\u7279\u6027\uff1a\u53ef\u62b5\u6297\u81f4\u547d\u4e00\u51fb'
    if neigong_id == 'jinzhong_zhao':
        return '\u7279\u6027\uff1a\u5468\u8eab\u6781\u786c\uff0c\u8179\u90e8\u6709\u7f69\u95e8'
    tags: list[str] = []
    passives = neigong.get('passives', [])
    passive_types = {item.get('type') for item in passives}
    guards = neigong.get('part_guard', {})
    if 'fatal_block' in passive_types:
        tags.append('\u53ef\u62b5\u6297\u81f4\u547d\u4e00\u51fb')
    if 'regeneration' in passive_types:
        tags.append('\u53ef\u6301\u7eed\u56de\u6625')
    if 'vampirism' in passive_types:
        tags.append('\u53ef\u5438\u8840\u7eed\u547d')
    if 'thorns' in passive_types:
        tags.append('\u53ef\u53cd\u9707\u4f24\u654c')
    if 'damage_defer' in passive_types:
        tags.append('可延后承受重伤')
    if 'stacking_defense' in passive_types:
        tags.append('回合越久防御越强')
    if 'part_counter' in passive_types:
        tags.append('四肢受击可借力反打')
    if 'burst_heal' in passive_types:
        tags.append('\u6b8b\u8840\u53ef\u7206\u53d1\u56de\u8840')
    if 'crisis_defense' in passive_types:
        tags.append('\u6b8b\u8840\u65f6\u9632\u5fa1\u66b4\u6da8')
    abdomen_guard = float(guards.get('abdomen', 1.0)) if guards else 1.0
    if abdomen_guard >= 1.3:
        tags.append('\u8179\u90e8\u6709\u7f69\u95e8')
    if not tags:
        return ''
    return '\u7279\u6027\uff1a' + '\uff0c'.join(tags[:2])

def _qinggong_flavor(qinggong: dict[str, Any]) -> str:
    spd = float(qinggong.get('spd_multiplier', 1.0))
    eva = float(qinggong.get('eva_bonus', 0.0))
    effect_data = qinggong.get('special_effect_data') or {}
    effect_type = effect_data.get('type') if isinstance(effect_data, dict) else None
    if effect_type == 'action_spd_stack':
        return '御风渐疾'
    if effect_type == 'dodge_damage_boost':
        return '步藏星变'
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
    effect_data = qinggong.get('special_effect_data') or {}
    effect_type = effect_data.get('type') if isinstance(effect_data, dict) else None
    parts: list[str] = []
    if effect_type == 'battle_start_first_strike':
        parts.append('\u5f00\u573a\u5fc5\u5b9a\u5148\u624b')
    elif effect_type == 'low_hp_extra_action':
        parts.append('\u6fd2\u6b7b\u53ef\u989d\u5916\u51fa\u624b')
    elif effect_type == 'action_spd_stack':
        parts.append('行动后会越来越快')
    elif effect_type == 'dodge_damage_boost':
        parts.append('闪避后可强化下一击')
    elif spd >= 1.12:
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


def _qinggong_signature(qinggong: dict[str, Any]) -> str:
    effect_data = qinggong.get('special_effect_data') or {}
    effect_type = effect_data.get('type') if isinstance(effect_data, dict) else None
    tags: list[str] = []
    if effect_type == 'battle_start_first_strike':
        tags.append('开场可夺绝对先手')
    if effect_type == 'low_hp_extra_action':
        tags.append('濒死时可额外出手')
    if effect_type == 'action_spd_stack':
        tags.append('行动越多身法越快')
    if effect_type == 'dodge_damage_boost':
        tags.append('闪避后下一击更重')
    if not tags:
        return ''
    return '特性：' + '，'.join(tags[:2])


def fighter_summary_lines(fighter: dict[str, Any], created: bool) -> list[str]:
    stats = fighter['stats']
    martial_art = fighter['martial_art']
    neigong = fighter['neigong']
    qinggong = fighter['qinggong']
    if created:
        opener = f'\u3010\u65b0\u89d2\u8272\u751f\u6210\u3011{fighter["name"]}\u521d\u5165\u6c5f\u6e56\uff0c\u540d\u518c\u5df2\u6210\u3002'
    else:
        opener = f'\u3010\u89d2\u8272\u67e5\u770b\u3011{fighter["name"]}\u7684\u5f53\u524d\u9762\u677f\u5982\u4e0b\u3002'
    lines = [opener, star_line(fighter), growth_line(fighter)]
    martial_signature = _martial_signature(martial_art)
    martial_fallback = f'{_martial_flavor(martial_art)}，{_martial_mechanics(martial_art)}。'
    lines.append(f'\u6b66\u5b66: \u3010{martial_art["name"]}\u3011{_profile_summary(martial_art, martial_fallback)}' + (f' {martial_signature}' if martial_signature else ''))
    neigong_signature = _neigong_signature(neigong)
    neigong_fallback = f'{_neigong_flavor(neigong)}，{_neigong_mechanics(neigong)}。'
    lines.append(f'\u5185\u529f: \u3010{neigong["name"]}\u3011{_profile_summary(neigong, neigong_fallback)}' + (f' {neigong_signature}' if neigong_signature else ''))
    qinggong_signature = _qinggong_signature(qinggong)
    qinggong_fallback = f'{_qinggong_flavor(qinggong)}，{_qinggong_mechanics(qinggong)}。'
    lines.append(f'\u8f7b\u529f: \u3010{qinggong["name"]}\u3011{_profile_summary(qinggong, qinggong_fallback)}' + (f' {qinggong_signature}' if qinggong_signature else ''))
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


def team3_leaderboard_message(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return '【群内 3v3 巅峰排行榜】\n当前群还没有任何 3v3 对战记录。'
    lines = ['【群内 3v3 巅峰排行榜 Top 10】']
    for index, entry in enumerate(entries, start=1):
        honor = _leaderboard_honor(index)
        title, _tag = _peak_title(float(entry['elo_rating']))
        team_text = ' / '.join(entry.get('team_names') or ['未配置阵容'])
        name = entry.get('display_name') or entry.get('user_id') or '未知玩家'
        if honor:
            lines.append(f'{honor}-{name}-{title}')
            lines.append(
                f'{entry["elo_rating"]:.2f} | 胜场 {entry["wins"]} | 对战 {entry["battles"]} | 胜率 {entry["win_rate"]:.1f}%'
            )
            lines.append(f'阵容: {team_text}')
        else:
            lines.append(
                f'{index}. {name} | {entry["elo_rating"]:.2f} | {title} | 胜场 {entry["wins"]} | 对战 {entry["battles"]} | 胜率 {entry["win_rate"]:.1f}%'
            )
            lines.append(f'阵容: {team_text}')
    return '\n'.join(lines)


def wallet_message(wallet: dict[str, Any]) -> str:
    return f'【积分】当前持有 {int(wallet.get("points", 0))} 点。'


def bag_message(items: list[dict[str, Any]]) -> str:
    if not items:
        return '【背包】你当前还没有任何道具。\n常用入口: /商店 查看作用并购买道具。'
    lines = ['【背包】']
    for index, item in enumerate(items):
        desc = ITEM_USAGE_GUIDE.get(item['name'], '暂无额外说明。')
        if index > 0:
            lines.append('')
        lines.append(f"{item['name']} x{item['quantity']}")
        lines.append(f"效果: {desc}")
    lines.append('')
    lines.extend(
        [
            '通用使用:',
            '/喂养 角色名 道具名 [数量]',
            '/突破 角色名',
            '/洗髓符 角色名',
            '/换宗令 内功|轻功|武功 角色名',
            '/天机残卷 武功|内功|轻功 角色名',
            '/特殊召唤令 角色名',
            '常用相关: /商店 /购买 道具名 数量 /积分',
        ]
    )
    return '\n'.join(lines)


def shop_message(items: list[dict[str, Any]], wallet_points: int | None = None) -> str:
    lines = ['【积分商店】']
    if wallet_points is not None:
        lines.append(f'当前积分: {int(wallet_points)}')
    lines.append('常用相关: /积分 /购买 道具名 数量 /背包')
    for item in items:
        desc = ITEM_USAGE_GUIDE.get(item['name'], '暂无额外说明。')
        lines.append(f"{item['name']} | {item['price']}积分")
        lines.append(f"效果: {desc}")
    lines.extend(
        [
            '/购买 道具名 数量',
            '购买后去 /背包 查看对应使用方式。',
        ]
    )
    return '\n'.join(lines)


def _format_stat_delta(stat_delta: dict[str, Any]) -> str:
    labels = {
        "hp": "\u6c14\u8840",
        "atk": "\u653b\u51fb",
        "def": "\u9632\u5fa1",
        "spd": "\u901f\u5ea6",
        "crt": "\u66b4\u51fb",
        "eva": "\u95ea\u907f",
    }
    lines = ["\u672c\u6b21\u63d0\u5347:"]
    for key in ("hp", "atk", "def", "spd", "crt", "eva"):
        value = float(stat_delta.get(key, 0))
        if abs(value) <= 0:
            continue
        display = f"{value:g}" if key in ("spd", "crt", "eva") else str(int(round(value)))
        lines.append(f"{labels[key]} +{display}")
    if len(lines) == 1:
        lines.append("\u672c\u6b21\u65e0\u660e\u663e\u5c5e\u6027\u53d8\u5316")
    return "\n".join(lines)


def feed_result_message(result: dict[str, Any]) -> str:
    fighter = result["fighter"]
    before_star = float(result.get("before_star_rating", fighter.get("base_star_rating", 0.0)))
    after_star = float(fighter.get("star_rating", before_star))
    node_text = f" 本次提升了 {result['level_ups']} 个星级节点。" if result.get("level_ups") else ""
    if result.get("next_requirement") is None:
        progress = "当前已到 5.0 星，后续不能再喂星级经验。"
    else:
        progress = f"当前星级经验: {result['star_exp']}/{result['next_requirement']}"
    lines = [
        f"【喂养成功】{fighter['name']} 使用了 {result['item_name']} x{result['quantity']}，获得 {result['gained_exp']} 星级经验。{node_text}",
        f"星级变化: {before_star:.1f}星 -> {after_star:.1f}星",
        star_line(fighter),
        growth_line(fighter),
    ]
    if result.get("level_ups"):
        lines.append(_format_stat_delta(result.get("stat_delta", {})))
    if result.get("unused_quantity", 0) > 0:
        lines.append(f"已自动封顶，本次只消耗 {result['quantity']} 个；另外 {result['unused_quantity']} 个未使用。")
    lines.append(progress)
    return "\n".join(lines)


def breakthrough_message(result: dict[str, Any]) -> str:
    fighter = result["fighter"]
    lines = [
        f"\u3010\u7a81\u7834\u6210\u529f\u3011{fighter['name']} \u4f7f\u7528\u4e86 {result['item_name']}\uff0c\u5df2\u8e0f\u5165 6.0 \u661f\u3002",
        star_line(fighter),
        growth_line(fighter),
        _format_stat_delta(result.get("stat_delta", {})),
    ]
    return "\n".join(lines)


def loadout_reroll_message(result: dict[str, Any]) -> str:
    fighter = result['fighter']
    return (
        f"\u3010\u66ff\u6362\u6210\u529f\u3011{fighter['name']} \u4f7f\u7528\u4e86 {result['item_name']}\u3002\n"
        f"\u5df2\u5c06{result['target_label']}\u4ece\u3010{result['old_entry']['name']}\u3011\u66f4\u6362\u4e3a\u3010{result['new_entry']['name']}\u3011\u3002\n"
        f"{star_line(fighter)}"
    )


def martial_reroll_message(result: dict[str, Any]) -> str:
    fighter = result['fighter']
    return (
        f'【武学更换】{fighter["name"]} 使用【{result["item_name"]}】，'
        f'武学由【{result["old_martial"]["name"]}】变为【{result["new_martial"]["name"]}】。\n'
        f'{star_line(fighter)}'
    )


def martial_choice_message(payload: dict[str, Any]) -> str:
    target_label = payload.get("target_label", "\u6b66\u529f")
    old_entry = payload.get("old_entry") or payload.get("old_martial")
    lines = [
        f'【天机残卷】{payload["fighter_name"]} 当前{target_label}为【{old_entry["name"]}】，请使用 /pick 1|2|3 选择:',
    ]
    for index, item in enumerate(payload['options'], start=1):
        lines.append(f"{index}. {item['name']}")
        summary = _loadout_choice_summary(item, payload.get("category"))
        if summary:
            lines.append(f"   {summary}")
    return '\n'.join(lines)


def _loadout_choice_summary(item: dict[str, Any], category: str | None) -> str:
    normalized = str(category or "").strip().lower()
    if normalized == "martial_art":
        flavor = _martial_flavor(item)
        mechanics = _martial_mechanics(item)
        signature = _martial_signature(item)
        parts = [part for part in (flavor, mechanics, signature) if part]
        return " | ".join(parts[:3])
    if normalized == "neigong":
        flavor = _neigong_flavor(item)
        mechanics = _neigong_mechanics(item)
        signature = _neigong_signature(item)
        parts = [part for part in (flavor, mechanics, signature) if part]
        return " | ".join(parts[:3])
    if normalized == "qinggong":
        flavor = _qinggong_flavor(item)
        mechanics = _qinggong_mechanics(item)
        signature = _qinggong_signature(item)
        parts = [part for part in (flavor, mechanics, signature) if part]
        return " | ".join(parts[:3])
    return ""


def boss_status_message(
    activity: dict[str, Any] | None,
    entries: list[dict[str, Any]],
    remaining_attempts: int | None = None,
    daily_limit: int | None = None,
) -> str:
    if activity is None:
        return "【世界BOSS】当前群还没有正在进行的世界BOSS活动。"
    phase1 = activity.get("phase1_payload") or {}
    phase2 = activity.get("phase2_payload") or {}
    phase1_stats = phase1.get("stats") or {}
    phase2_stats = phase2.get("stats") or {}

    def _stage_title(payload: dict[str, Any], fallback: str) -> str:
        label = str(payload.get("label") or fallback)
        name = str(payload.get("name") or fallback)
        return f"{label}: {name}"

    def _stage_desc(payload: dict[str, Any]) -> str:
        return str(payload.get("description") or "").strip()

    def _stage_panel(stats: dict[str, Any], current_hp: int | None = None) -> str:
        hp_value = int(current_hp if current_hp is not None else stats.get("hp", 0))
        return (
            f"气血 {hp_value} | 攻击 {int(stats.get('atk', 0))} | 防御 {int(stats.get('def', 0))} | "
            f"速度 {float(stats.get('spd', 0)):.1f} | 暴击 {float(stats.get('crt', 0)):.1f}% | "
            f"闪避 {float(stats.get('eva', 0)):.1f}%"
        )

    def _stage_loadout(payload: dict[str, Any]) -> str:
        martial_obj = payload.get("martial_art") or {}
        neigong_obj = payload.get("neigong") or {}
        qinggong_obj = payload.get("qinggong") or {}
        martial = martial_obj.get("name") or payload.get("martial_art_id") or "未知武学"
        neigong = neigong_obj.get("name") or payload.get("neigong_id") or "未知内功"
        qinggong = qinggong_obj.get("name") or payload.get("qinggong_id") or "未知轻功"
        lines = [f"配置: {martial} / {neigong} / {qinggong}"]
        martial_summary = str(martial_obj.get("boss_summary") or "").strip()
        neigong_summary = str(neigong_obj.get("boss_summary") or "").strip()
        qinggong_summary = str(qinggong_obj.get("boss_summary") or "").strip()
        if martial_summary:
            lines.append(f"武学: {martial_summary}")
        if neigong_summary:
            lines.append(f"内功: {neigong_summary}")
        if qinggong_summary:
            lines.append(f"轻功: {qinggong_summary}")
        return "\n".join(lines)

    lines = [
        f"【世界BOSS】{activity['boss_name']}",
        "规则: 每次挑战都先打一阶段，只有二阶段伤害计入群共享血量与贡献榜。",
    ]
    phase1_desc = _stage_desc(phase1)
    if phase1_desc:
        lines.append(f"背景: {phase1_desc}")
    lines.extend(
        [
            _stage_title(phase1, "一阶段"),
            _stage_panel(phase1_stats),
            _stage_loadout(phase1),
            _stage_title(phase2, "二阶段"),
            _stage_panel(phase2_stats, int(activity["phase2_current_hp"])),
            _stage_loadout(phase2),
            f"二阶段共享血量: {activity['phase2_current_hp']}/{activity['phase2_max_hp']}",
        ]
    )
    phase2_desc = _stage_desc(phase2)
    if phase2_desc:
        lines.append(f"说明: {phase2_desc}")
    if remaining_attempts is not None and daily_limit is not None:
        used = max(0, int(daily_limit) - int(remaining_attempts))
        lines.append(f"今日次数: {used}/{daily_limit}, 剩余 {remaining_attempts}")
    if not entries:
        lines.append("当前还没有任何二阶段伤害记录。")
        return "\n".join(lines)
    lines.append("贡献榜 Top 5:")
    for index, entry in enumerate(entries[:5], start=1):
        lines.append(f"{index}. {entry['display_name']} | 伤害 {entry['total_damage']} | 挑战 {entry['attempts']}")
    return "\n".join(lines)


def boss_rank_message(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "【世界BOSS贡献榜】当前还没有任何二阶段贡献记录。"
    lines = ["【世界BOSS贡献榜 Top 10】"]
    for index, entry in enumerate(entries[:10], start=1):
        lines.append(f"{index}. {entry['display_name']} | 伤害 {entry['total_damage']} | 挑战 {entry['attempts']}")
    return "\n".join(lines)


def boss_fight_result_message(result: dict[str, Any]) -> str:
    boss_name = str(result.get("boss_name") or "世界BOSS")
    lines = [f"【世界BOSS挑战】{boss_name}"]
    if not result.get("phase1_cleared"):
        lines.append("你倒在了一阶段门槛前，本次未能进入二阶段。")
        lines.append(f"今日剩余次数: {result['remaining_attempts']}/{result['daily_limit']}")
        return "\n".join(lines)
    lines.append("你已击破一阶段，残阵进入二阶段。")
    if not result.get("entered_phase2"):
        lines.append("但你的队伍已在过门后耗尽，本次未对二阶段造成伤害。")
        lines.append(f"今日剩余次数: {result['remaining_attempts']}/{result['daily_limit']}")
        return "\n".join(lines)
    lines.append(f"本次二阶段伤害: {result['phase2_damage']}")
    lines.append(f"二阶段剩余血量: {result['phase2_current_hp']}/{result['phase2_max_hp']}")
    lines.append(f"你的累计贡献: {result['total_damage']}")
    lines.append(f"今日剩余次数: {result['remaining_attempts']}/{result['daily_limit']}")
    if result.get("is_killed"):
        lines.append("你们击杀了这期世界BOSS。")
    return "\n".join(lines)


def boss_settlement_message(payload: dict[str, Any] | None, closed_without_kill: bool = False) -> str:
    if closed_without_kill:
        return "【世界BOSS已关闭】本期世界BOSS未被击杀，不发放击杀奖励。"
    if not payload:
        return "【世界BOSS结算】当前没有可展示的击杀结算。"
    lines = [f"【世界BOSS结算】{payload.get('boss_name', '世界BOSS')}"]
    rewards = payload.get("rewards") or []
    if not rewards:
        lines.append("本期没有可发放的贡献奖励。")
        return "\n".join(lines)
    for reward in rewards[:10]:
        lines.append(
            f"第{reward['rank']}名 {reward['display_name']} | 伤害 {reward['total_damage']} | +{reward['points']}积分"
        )
    return "\n".join(lines)
