# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

try:
    from .stat_quality import stat_quality_comment
except ImportError:
    from stat_quality import stat_quality_comment

HELP_LINES = [
    '\u53ef\u7528\u6307\u4ee4:',
    '/\u5e2e\u52a9 - \u67e5\u770b\u5168\u90e8\u6307\u4ee4\u8bf4\u660e',
    '/\u6559\u7a0b - \u67e5\u770b\u65b0\u624b\u6559\u7a0b\u548c\u517b\u6210\u8bf4\u660e',
    '/\u521b\u5efa\u89d2\u8272 \u89d2\u8272\u540d - \u521b\u5efa\u65b0\u89d2\u8272\uff1b\u82e5\u540d\u4e0b\u5df2\u6ee1 3 \u4eba\uff0c\u5219\u8fdb\u5165\u9876\u66ff\u9009\u62e9',
    '/\u9009\u62e9\u89d2\u8272 \u5e8f\u53f7 - \u5728\u5019\u9009\u89d2\u8272\u51fa\u73b0\u540e\uff0c\u9009\u62e9\u8981\u88ab\u9876\u66ff\u7684\u65e7\u89d2\u8272\u680f\u4f4d',
    '/\u89d2\u8272\u5217\u8868 - \u67e5\u770b\u4f60\u5f53\u524d\u540d\u4e0b\u5168\u90e8\u89d2\u8272',
    '/\u5207\u6362\u89d2\u8272 \u89d2\u8272\u540d - \u5207\u6362\u5f53\u524d\u51fa\u6218\u89d2\u8272',
    '/\u89d2\u8272\u8be6\u60c5 [\u89d2\u8272\u540d] - \u67e5\u770b\u89d2\u8272\u8be6\u60c5\uff1b\u4e0d\u586b\u540d\u5b57\u65f6\u67e5\u770b\u89d2\u8272\u680f',
    '/\u7b7e\u5230 - \u6bcf\u65e5\u7b7e\u5230\u9886\u53d6\u79ef\u5206',
    '/\u79ef\u5206 - \u67e5\u770b\u5f53\u524d\u79ef\u5206',
    '/\u8d60\u9001 @\u5bf9\u65b9 100 - \u7ed9\u540c\u7fa4\u73a9\u5bb6\u8d60\u9001\u79ef\u5206',
    '/\u80cc\u5305 - \u67e5\u770b\u80cc\u5305\u9053\u5177',
    '/\u5546\u5e97 - \u67e5\u770b\u79ef\u5206\u5546\u5e97',
    '/\u8d2d\u4e70 \u9053\u5177\u540d \u6570\u91cf - \u4ece\u5546\u5e97\u5151\u6362\u9053\u5177',
    '/\u5582\u517b \u89d2\u8272\u540d \u9053\u5177\u540d [\u6570\u91cf] - \u7ed9\u89d2\u8272\u5582\u661f\u7ecf\u9a8c\u9053\u5177',
    '/\u7a81\u7834 \u89d2\u8272\u540d - \u8ba9 5 \u661f\u89d2\u8272\u7a81\u7834\u5230 6 \u661f',
    '/\u968f\u673a\u6362\u6b66\u5b66 \u89d2\u8272\u540d - \u6d88\u8017\u6d17\u9ad3\u7b26\uff0c\u5168\u6b66\u5b66\u6c60\u968f\u673a\u6362 1 \u4e2a\u6b66\u529f',
    '/\u6d17\u9ad3\u7b26 \u89d2\u8272\u540d - \u4e0e /\u968f\u673a\u6362\u6b66\u5b66 \u7b49\u4ef7',
    '/\u6362\u5185\u529f \u89d2\u8272\u540d - \u6d88\u8017\u6362\u5b97\u4ee4\uff0c\u968f\u673a\u66f4\u6362 1 \u4e2a\u5185\u529f',
    '/\u6362\u8f7b\u529f \u89d2\u8272\u540d - \u6d88\u8017\u6362\u5b97\u4ee4\uff0c\u968f\u673a\u66f4\u6362 1 \u4e2a\u8f7b\u529f',
    '/\u6362\u6b66\u529f \u89d2\u8272\u540d - \u6d88\u8017\u6362\u5b97\u4ee4\uff0c\u968f\u673a\u66f4\u6362 1 \u4e2a\u6b66\u529f',
    '/\u6362\u5b97\u4ee4 \u5185\u529f|\u8f7b\u529f|\u6b66\u529f \u89d2\u8272\u540d - \u6309\u6307\u5b9a\u7c7b\u578b\u968f\u673a\u66f4\u6362',
    '/\u81ea\u9009\u6362\u6b66\u5b66 \u89d2\u8272\u540d - \u6d88\u8017\u5929\u673a\u6b8b\u5377\uff0c\u83b7\u5f97 3 \u4e2a\u6b66\u529f\u5019\u9009',
    '/\u9ad8\u7ea7\u6d17\u5185\u529f \u89d2\u8272\u540d - \u6d88\u8017\u5929\u673a\u6b8b\u5377\uff0c\u83b7\u5f97 3 \u4e2a\u5185\u529f\u5019\u9009',
    '/\u9ad8\u7ea7\u6d17\u8f7b\u529f \u89d2\u8272\u540d - \u6d88\u8017\u5929\u673a\u6b8b\u5377\uff0c\u83b7\u5f97 3 \u4e2a\u8f7b\u529f\u5019\u9009',
    '/\u5929\u673a\u6b8b\u5377 \u6b66\u529f|\u5185\u529f|\u8f7b\u529f \u89d2\u8272\u540d - \u6309\u6307\u5b9a\u7c7b\u578b\u751f\u6210 3 \u4e2a\u5019\u9009',
    '/\u9009\u62e9\u6b66\u5b66 1|2|3 - \u5728\u9ad8\u7ea7\u81ea\u9009\u540e\u9009\u62e9\u6700\u7ec8\u6761\u76ee',
    '/\u6392\u4f4d\u6311\u6218 \u89d2\u8272\u540d - \u5411\u76ee\u6807\u89d2\u8272\u53d1\u8d77\u6392\u4f4d\u6311\u6218\uff0c\u7b49\u5f85\u5bf9\u65b9 /\u63a5\u53d7 \u6216 /\u62d2\u7edd',
    '/\u6311\u6218 \u89d2\u8272\u540d - \u76f4\u63a5\u5f3a\u5236\u5f00\u6218\uff0c\u4e0d\u9700\u8981\u5bf9\u65b9\u786e\u8ba4\uff1b\u53ea\u8bb0 1/3 \u5a31\u4e50\u5411 ELO\uff0c\u4e0d\u4ea7\u79ef\u5206',
    '/\u63a5\u53d7 - \u63a5\u53d7\u522b\u4eba\u53d1\u6765\u7684 1v1 \u6311\u6218',
    '/\u62d2\u7edd - \u62d2\u7edd\u522b\u4eba\u53d1\u6765\u7684 1v1 \u6311\u6218',
    '/\u6392\u4f4d\u699c - \u67e5\u770b\u5f53\u524d\u7fa4\u7684 1v1 \u5dc5\u5cf0\u6392\u884c\u699c',
    '/\u4e09\u4eba\u961f\u4f0d - \u67e5\u770b\u5f53\u524d 3v3 \u51fa\u6218\u987a\u5e8f\u4e0e\u9635\u5bb9',
    '/\u961f\u4f0d\u987a\u5e8f 2 1 3 - \u8c03\u6574 3v3 \u51fa\u6218\u987a\u5e8f',
    '/\u6392\u4f4d\u6311\u62183 @\u76ee\u6807 - \u5411\u5bf9\u65b9\u53d1\u8d77 3v3 \u6392\u4f4d\u6311\u6218',
    '/\u6311\u62183 @\u76ee\u6807\u73a9\u5bb6 - \u76f4\u63a5\u5f3a\u5236\u5f00\u59cb 3v3 \u8fde\u6218\uff1b\u53ea\u8bb0 1/3 \u5a31\u4e50\u5411 ELO\uff0c\u4e0d\u4ea7\u79ef\u5206',
    '/\u63a5\u53d73 - \u63a5\u53d7\u522b\u4eba\u53d1\u6765\u7684 3v3 \u6311\u6218',
    '/\u62d2\u7edd3 - \u62d2\u7edd\u522b\u4eba\u53d1\u6765\u7684 3v3 \u6311\u6218',
    '/\u4e09\u6392\u699c - \u67e5\u770b\u5f53\u524d\u7fa4\u7684 3v3 \u5dc5\u5cf0\u6392\u884c\u699c',
    '/\u5468\u699c\u7ed3\u7b97 [1v1|3v3|all] - \u624b\u52a8\u7ed3\u7b97\u672c\u5468\u6392\u884c\u699c\u5956\u52b1',
    '/\u65e5\u699c\u7ed3\u7b97 [1v1|3v3|all] [YYYY-MM-DD] - \u624b\u52a8\u8865\u7ed3\u7b97\u67d0\u4e00\u5929\u7684\u65e5\u699c\u5956\u52b1',
]

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
    return stat_quality_comment(stat, value)


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
    lines.append(f'\u6b66\u5b66: \u3010{martial_art["name"]}\u3011{_martial_flavor(martial_art)}\uff0c{_martial_mechanics(martial_art)}\u3002' + (f' {martial_signature}' if martial_signature else ''))
    neigong_signature = _neigong_signature(neigong)
    lines.append(f'\u5185\u529f: \u3010{neigong["name"]}\u3011{_neigong_flavor(neigong)}\uff0c{_neigong_mechanics(neigong)}\u3002' + (f' {neigong_signature}' if neigong_signature else ''))
    qinggong_signature = _qinggong_signature(qinggong)
    lines.append(f'\u8f7b\u529f: \u3010{qinggong["name"]}\u3011{_qinggong_flavor(qinggong)}\uff0c{_qinggong_mechanics(qinggong)}\u3002' + (f' {qinggong_signature}' if qinggong_signature else ''))
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
        return '【背包】你当前还没有任何道具。'
    lines = ['【背包】']
    for item in items:
        lines.append(f"{item['name']} x{item['quantity']}")
    return '\n'.join(lines)


def shop_message(items: list[dict[str, Any]]) -> str:
    lines = ['【积分商店】']
    for item in items:
        lines.append(f"{item['name']} | {item['price']}积分")
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



def boss_status_message(activity: dict[str, Any] | None, entries: list[dict[str, Any]], remaining_attempts: int | None = None, daily_limit: int | None = None) -> str:
    if activity is None:
        return '\u3010\u4e16\u754cBOSS\u3011\u5f53\u524d\u7fa4\u8fd8\u6ca1\u6709\u6b63\u5728\u8fdb\u884c\u7684\u4e16\u754cBOSS\u6d3b\u52a8\u3002'
    lines = [
        f"\u3010\u4e16\u754cBOSS\u3011{activity['boss_name']}",
        '\u89c4\u5219: \u6bcf\u6b21\u6311\u6218\u90fd\u5148\u6253\u4e00\u9636\u6bb5, \u53ea\u6709\u4e8c\u9636\u6bb5\u4f24\u5bb3\u8ba1\u5165\u7fa4\u5171\u4eab\u8840\u91cf\u4e0e\u8d21\u732e\u699c\u3002',
        f"\u4e8c\u9636\u6bb5\u8840\u91cf: {activity['phase2_current_hp']}/{activity['phase2_max_hp']}",
    ]
    if remaining_attempts is not None and daily_limit is not None:
        used = max(0, int(daily_limit) - int(remaining_attempts))
        lines.append(f'\u4eca\u65e5\u6b21\u6570: {used}/{daily_limit}, \u5269\u4f59 {remaining_attempts}')
    if not entries:
        lines.append('\u5f53\u524d\u8fd8\u6ca1\u6709\u4efb\u4f55\u4e8c\u9636\u6bb5\u4f24\u5bb3\u8bb0\u5f55\u3002')
        return '\n'.join(lines)
    lines.append('\u8d21\u732e\u699c Top 5:')
    for index, entry in enumerate(entries[:5], start=1):
        lines.append(f"{index}. {entry['display_name']} | \u4f24\u5bb3 {entry['total_damage']} | \u6311\u6218 {entry['attempts']}")
    return '\n'.join(lines)


def boss_rank_message(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return '\u3010\u4e16\u754cBOSS\u8d21\u732e\u699c\u3011\u5f53\u524d\u8fd8\u6ca1\u6709\u4efb\u4f55\u4e8c\u9636\u6bb5\u8d21\u732e\u8bb0\u5f55\u3002'
    lines = ['\u3010\u4e16\u754cBOSS\u8d21\u732e\u699c Top 10\u3011']
    for index, entry in enumerate(entries[:10], start=1):
        lines.append(f"{index}. {entry['display_name']} | \u4f24\u5bb3 {entry['total_damage']} | \u6311\u6218 {entry['attempts']}")
    return '\n'.join(lines)


def boss_fight_result_message(result: dict[str, Any]) -> str:
    boss_name = str(result.get('boss_name') or '\u4e16\u754cBOSS')
    lines = [f'\u3010\u4e16\u754cBOSS\u6311\u6218\u3011{boss_name}']
    if not result.get('phase1_cleared'):
        lines.append('\u4f60\u5012\u5728\u4e86\u4e00\u9636\u6bb5\u95e8\u69db\u524d, \u672c\u6b21\u672a\u80fd\u8fdb\u5165\u4e8c\u9636\u6bb5\u3002')
        lines.append(f"\u4eca\u65e5\u5269\u4f59\u6b21\u6570: {result['remaining_attempts']}/{result['daily_limit']}")
        return '\n'.join(lines)
    lines.append('\u4f60\u5df2\u51fb\u7834\u4e00\u9636\u6bb5, \u6b8b\u9635\u8fdb\u5165\u4e8c\u9636\u6bb5\u3002')
    if not result.get('entered_phase2'):
        lines.append('\u4f46\u4f60\u7684\u961f\u4f0d\u5df2\u5728\u8fc7\u95e8\u540e\u8017\u5c3d, \u672c\u6b21\u672a\u5bf9\u4e8c\u9636\u6bb5\u9020\u6210\u4f24\u5bb3\u3002')
        lines.append(f"\u4eca\u65e5\u5269\u4f59\u6b21\u6570: {result['remaining_attempts']}/{result['daily_limit']}")
        return '\n'.join(lines)
    lines.append(f"\u672c\u6b21\u4e8c\u9636\u6bb5\u4f24\u5bb3: {result['phase2_damage']}")
    lines.append(f"\u4e8c\u9636\u6bb5\u5269\u4f59\u8840\u91cf: {result['phase2_current_hp']}/{result['phase2_max_hp']}")
    lines.append(f"\u4f60\u7684\u7d2f\u8ba1\u8d21\u732e: {result['total_damage']}")
    lines.append(f"\u4eca\u65e5\u5269\u4f59\u6b21\u6570: {result['remaining_attempts']}/{result['daily_limit']}")
    if result.get('is_killed'):
        lines.append('\u4f60\u4eec\u51fb\u6740\u4e86\u8fd9\u671f\u4e16\u754cBOSS\u3002')
    return '\n'.join(lines)


def boss_settlement_message(payload: dict[str, Any] | None, closed_without_kill: bool = False) -> str:
    if closed_without_kill:
        return '\u3010\u4e16\u754cBOSS\u5df2\u5173\u95ed\u3011\u672c\u671f\u4e16\u754cBOSS\u672a\u88ab\u51fb\u6740, \u4e0d\u53d1\u653e\u51fb\u6740\u5956\u52b1\u3002'
    if not payload:
        return '\u3010\u4e16\u754cBOSS\u7ed3\u7b97\u3011\u5f53\u524d\u6ca1\u6709\u53ef\u5c55\u793a\u7684\u51fb\u6740\u7ed3\u7b97\u3002'
    lines = [f"\u3010\u4e16\u754cBOSS\u7ed3\u7b97\u3011{payload.get('boss_name', '\u4e16\u754cBOSS')}"]
    rewards = payload.get('rewards') or []
    if not rewards:
        lines.append('\u672c\u671f\u6ca1\u6709\u53ef\u53d1\u653e\u7684\u8d21\u732e\u5956\u52b1\u3002')
        return '\n'.join(lines)
    for reward in rewards[:10]:
        lines.append(
            f"\u7b2c{reward['rank']}\u540d {reward['display_name']} | \u4f24\u5bb3 {reward['total_damage']} | +{reward['points']}\u79ef\u5206"
        )
    return '\n'.join(lines)
