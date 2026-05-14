# -*- coding: utf-8 -*-
from __future__ import annotations

STAT_QUALITY_THRESHOLDS: dict[str, list[float]] = {
    "hp": [384, 427, 465, 509, 553],
    "atk": [73, 87, 99, 113, 125],
    "def": [60, 75, 87, 100, 112],
    "spd": [46, 58, 69, 81, 93],
    "crt": [15, 21, 26, 31, 35],
    "eva": [20, 26, 31, 36, 41],
}

STAT_QUALITY_COLORS: list[tuple[int, int, int]] = [
    (255, 255, 255),
    (80, 255, 80),
    (50, 200, 255),
    (230, 80, 255),
    (255, 190, 35),
    (150, 18, 18),
]

STAT_QUALITY_COMMENTS: dict[str, list[str]] = {
    "hp": ["气息虚浮", "本元稍欠", "内息连绵", "根基深厚", "气血如虹", "北冥化生"],
    "atk": ["力道未成", "守拙求稳", "蓄势成劲", "锋芒毕露", "所向披靡", "撼天动地"],
    "def": ["不堪一击", "轻甲薄阵", "严阵以待", "守势沉雄", "不动如山", "苍山负雪"],
    "spd": ["身形迟滞", "步履沉稳", "进退有度", "身轻如燕", "追风逐电", "浮光掠影"],
    "crt": ["锋芒未显", "稳中求胜", "偶露峥嵘", "奇锋暗藏", "杀机炽盛", "白虹贯日"],
    "eva": ["步法生疏", "舍避就挡", "转圜自如", "闪转腾挪", "飘渺难测", "翩若惊鸿"],
}


def stat_quality_tier(stat: str, value: float) -> int:
    thresholds = STAT_QUALITY_THRESHOLDS.get(stat)
    if thresholds is None:
        return 0
    for index in range(len(thresholds) - 1, -1, -1):
        if value >= thresholds[index]:
            return index + 1
    return 0


def stat_quality_color(stat: str, value: float) -> tuple[int, int, int]:
    return STAT_QUALITY_COLORS[stat_quality_tier(stat, value)]


def stat_quality_comment(stat: str, value: float) -> str:
    comments = STAT_QUALITY_COMMENTS.get(stat)
    if comments is None:
        return ""
    return comments[stat_quality_tier(stat, value)]
