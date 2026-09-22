# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any


_DRAGON_CHIEF_PHASE1_MOVES = [
    {
        "name": "封门第一剑",
        "texts": [
            "{attacker} 守在山门正中，长剑一压，一式「{move_name}」沉沉逼向 {defender} 的{body_part_text}。",
            "{attacker} 剑圈忽收忽放，以「{move_name}」封死来路，冷冷压向 {defender} 的{body_part_text}。",
        ],
    },
    {
        "name": "回锋镇关",
        "texts": [
            "{attacker} 腕间一翻，剑锋回卷如关门落栓，一招「{move_name}」横截 {defender} 的{body_part_text}。",
            "{attacker} 剑势不快却极稳，借「{move_name}」硬生生将 {defender} 的{body_part_text}拦在阵前。",
        ],
    },
    {
        "name": "岳影压顶",
        "texts": [
            "{attacker} 身形前逼，剑光自上而下压落，「{move_name}」如山影覆顶，直逼 {defender} 的{body_part_text}。",
            "{attacker} 提剑一沉，厚重剑势借「{move_name}」当头罩下，逼得 {defender} 的{body_part_text}几无退处。",
        ],
    },
    {
        "name": "锁阵穿心",
        "texts": [
            "{attacker} 气息一敛，剑锋骤直，一式「{move_name}」破空刺向 {defender} 的{body_part_text}。",
            "{attacker} 借阵势凝成一点寒芒，以「{move_name}」狠辣探入 {defender} 的{body_part_text}。",
        ],
    },
    {
        "name": "拦云待客",
        "texts": [
            "{attacker} 剑招圆转，看似守势，实则暗藏机锋，一招「{move_name}」削向 {defender} 的{body_part_text}。",
            "{attacker} 立在原地不退半步，长剑微扬，以「{move_name}」稳稳递向 {defender} 的{body_part_text}。",
        ],
    },
    {
        "name": "巡关横斩",
        "texts": [
            "{attacker} 足下微移，剑光横掠，一记「{move_name}」迅速扫过 {defender} 的{body_part_text}。",
            "{attacker} 借换位之势发剑，「{move_name}」如巡关铁律般斩向 {defender} 的{body_part_text}。",
        ],
    },
    {
        "name": "千门俱闭",
        "texts": [
            "{attacker} 剑影骤密，宛如重门尽合，一招「{move_name}」将 {defender} 的{body_part_text}一并罩住。",
            "{attacker} 气机连成一片，借「{move_name}」逼出满天剑影，将 {defender} 的{body_part_text}压得透不过气。",
        ],
    },
    {
        "name": "镇山喝止",
        "texts": [
            "{attacker} 目光一沉，长剑骤然直落，绝招「{move_name}」重重斩向 {defender} 的{body_part_text}。",
            "{attacker} 真气灌注剑脊，借「{move_name}」斩出镇山之威，硬生生砸向 {defender} 的{body_part_text}。",
        ],
    },
]

_DRAGON_CHIEF_PHASE2_MOVES = [
    {
        "name": "龙门压界",
        "texts": [
            "{attacker} 真身显现，剑势如门如岳，一式「{move_name}」沉沉压向 {defender} 的{body_part_text}。",
            "{attacker} 立在原地便有威压铺开，以「{move_name}」将整片战圈都逼向 {defender} 的{body_part_text}。",
        ],
    },
    {
        "name": "回岳断潮",
        "texts": [
            "{attacker} 剑锋回卷如山势折返，一招「{move_name}」轰然截向 {defender} 的{body_part_text}。",
            "{attacker} 周身真气回荡不绝，借「{move_name}」将厚重剑压尽数倾在 {defender} 的{body_part_text}上。",
        ],
    },
    {
        "name": "镇岳垂锋",
        "texts": [
            "{attacker} 长剑高举，下一瞬如山岳塌落，一式「{move_name}」正压 {defender} 的{body_part_text}。",
            "{attacker} 剑未全落，威势已先压人，借「{move_name}」逼得 {defender} 的{body_part_text}一阵发紧。",
        ],
    },
    {
        "name": "潜龙穿阙",
        "texts": [
            "{attacker} 剑锋忽然内敛成一线，绝快的一招「{move_name}」直取 {defender} 的{body_part_text}。",
            "{attacker} 厚重剑势中忽藏一缕锐芒，以「{move_name}」穿入 {defender} 的{body_part_text}之前。",
        ],
    },
    {
        "name": "万壑迎敌",
        "texts": [
            "{attacker} 周身气墙微震，长剑顺势斜削，一记「{move_name}」稳稳拦向 {defender} 的{body_part_text}。",
            "{attacker} 不争一时快慢，只凭沉稳换位，以「{move_name}」逼退 {defender} 的{body_part_text}。",
        ],
    },
    {
        "name": "龙脊横江",
        "texts": [
            "{attacker} 剑脊一摆，横斩如江潮拦路，一式「{move_name}」扫向 {defender} 的{body_part_text}。",
            "{attacker} 真身微侧，长剑已如巨浪横拍，以「{move_name}」狠狠压过 {defender} 的{body_part_text}。",
        ],
    },
    {
        "name": "群峰并起",
        "texts": [
            "{attacker} 剑意骤涨，仿佛群峰齐压，一招「{move_name}」将 {defender} 的{body_part_text}尽数笼在其中。",
            "{attacker} 重重剑影自四面合围，借「{move_name}」将 {defender} 的{body_part_text}压进层层威势里。",
        ],
    },
    {
        "name": "龙首镇岳",
        "texts": [
            "{attacker} 一声沉喝，真气与剑势合为一处，绝招「{move_name}」如山崩般轰向 {defender} 的{body_part_text}。",
            "{attacker} 剑光不炫却重得惊人，这一式「{move_name}」带着整座山门的威压砸向 {defender} 的{body_part_text}。",
        ],
    },
]

_BOSS_MOVE_SKINS = {
    "dragon_chief_phase1": _DRAGON_CHIEF_PHASE1_MOVES,
    "dragon_chief_phase2": _DRAGON_CHIEF_PHASE2_MOVES,
}


def _copy_skin_lines(skin: dict[str, Any], fallback_name: str) -> list[str]:
    summary = str(skin.get("summary") or "").strip()
    lines: list[str] = []
    if summary:
        lines.append(summary)
    return lines


def apply_boss_phase_skin(
    template: dict[str, Any],
    martial_art: dict[str, Any],
    neigong: dict[str, Any],
    qinggong: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    martial_art = deepcopy(martial_art)
    neigong = deepcopy(neigong)
    qinggong = deepcopy(qinggong)
    for key, target in (
        ("martial_art_skin", martial_art),
        ("neigong_skin", neigong),
        ("qinggong_skin", qinggong),
    ):
        skin = template.get(key) or {}
        if skin.get("name"):
            target["name"] = str(skin["name"])
        if skin.get("summary"):
            target["boss_summary"] = str(skin["summary"])

    boss_key = str(template.get("boss_key") or "").strip()
    move_skins = _BOSS_MOVE_SKINS.get(boss_key) or []
    base_moves = list(martial_art.get("moves") or [])
    if move_skins and base_moves:
        skinned_moves: list[dict[str, Any]] = []
        for index, base_move in enumerate(base_moves):
            move = deepcopy(base_move)
            if index < len(move_skins):
                skin = move_skins[index]
                if skin.get("name"):
                    move["name"] = str(skin["name"])
                if skin.get("texts"):
                    move["texts"] = [str(text) for text in skin["texts"]]
            skinned_moves.append(move)
        martial_art["moves"] = skinned_moves
    return martial_art, neigong, qinggong


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
    for label, skin_obj in (("武学", martial_obj), ("内功", neigong_obj), ("轻功", qinggong_obj)):
        for line in _copy_skin_lines(skin_obj, ""):
            lines.append(f"{label}: {line}")
    return "\n".join(lines)


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
    lines = [
        f"【世界BOSS】{activity['boss_name']}",
        "规则: 每次挑战都先打一阶段，只有二阶段伤害计入群共享血量与贡献榜。",
        "演练: 可用 /bosssim、/bosssim phase1、/bosssim phase2 先测试当前 3v3 队伍。",
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
    lines.extend(
        [
            "本期奖励预览:",
            "击杀参与: 所有有贡献记录的成员 +500积分 + 特殊召唤令x2 + 天机残卷x2 + 换宗令x2 + 中星尘丹x3 + 小星尘丹x5",
            "击杀排行: 第1 额外+1500积分+特殊召唤令x3，第2 +1200积分+特殊召唤令x2，第3 +1000积分+特殊召唤令x1",
            "未击杀排行: 第1 +900积分+特殊召唤令x1，第2 +700积分，第3 +500积分，4-10名 +300积分",
            "详细规则与完整奖励: /bosshelp",
        ]
    )
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
        lines.append("你的小队被拦在山门之外，一阶段未能破阵，本次挑战止步于前锋关。")
        lines.append(f"今日剩余次数: {result['remaining_attempts']}/{result['daily_limit']}")
        return "\n".join(lines)
    if not result.get("entered_phase2"):
        lines.append("你已击穿一阶段守关，但队伍在逼出真身后力竭，未能留下有效伤害。")
        lines.append(f"今日剩余次数: {result['remaining_attempts']}/{result['daily_limit']}")
        return "\n".join(lines)
    lines.append("你已破开前阵，真身现世，二阶段共享血量已被撼动。")
    lines.append(f"本次二阶段伤害: {result['phase2_damage']}")
    lines.append(f"二阶段剩余血量: {result['phase2_current_hp']}/{result['phase2_max_hp']}")
    lines.append(f"你的累计贡献: {result['total_damage']}")
    lines.append(f"今日剩余次数: {result['remaining_attempts']}/{result['daily_limit']}")
    if result.get("is_killed"):
        lines.append("最后一道防线已被击溃，本期世界BOSS已被全群联手斩落。")
    return "\n".join(lines)


def boss_phase_opening_message(team_label: str, payload: dict[str, Any]) -> str:
    stage_label = str(payload.get("label") or "\u9636\u6bb5")
    boss_name = str(payload.get("name") or "\u4e16\u754cBOSS")
    summary = _stage_loadout(payload).splitlines()[0]
    desc = _stage_desc(payload)
    lines = [f"\u3010{stage_label}\u8fce\u6218\u3011{team_label} \u903c\u8fd1 {boss_name}。", summary]
    if desc:
        lines.append(desc)
    return "\n".join(lines)


def boss_phase_transition_message(phase1: dict[str, Any], phase2: dict[str, Any]) -> str:
    phase1_name = str(phase1.get("name") or "\u4e00\u9636\u6bb5")
    phase2_name = str(phase2.get("name") or "\u4e8c\u9636\u6bb5")
    return f"\u3010\u9636\u6bb5\u5207\u6362\u3011{phase1_name} \u5df2\u88ab\u51fb\u7a7f\uff0c{phase2_name} \u6ee1\u8840\u73b0\u4e16\uff0c\u6b8b\u9635\u7ee7\u7eed\u5f3a\u653b\u3002"


def boss_duel_intro_message(phase_label: str, duel_no: int, fighter_name: str, boss_name: str) -> str:
    return f"\u3010{phase_label}\u00b7\u7b2c{duel_no}\u9635\u3011{fighter_name} \u6b63\u9762\u8fce\u6218 {boss_name}。"


def boss_duel_round_message(
    phase_label: str,
    fighter_name: str,
    boss_name: str,
    before_fighter_hp: int,
    after_fighter_hp: int,
    before_boss_hp: int,
    after_boss_hp: int,
) -> str:
    dealt = max(0, int(before_boss_hp) - int(after_boss_hp))
    taken = max(0, int(before_fighter_hp) - int(after_fighter_hp))
    return (
        f"\u3010{phase_label}\u4ea4\u950b\u3011{fighter_name} \u5bf9 {boss_name} \u9020\u6210 {dealt} \u70b9\u4f24\u5bb3\uff0c"
        f"\u81ea\u8eab\u627f\u53d7 {taken} \u70b9\u4f24\u5bb3\u3002"
    )


def boss_duel_result_message(
    phase_label: str,
    fighter_name: str,
    boss_name: str,
    winner_name: str | None,
    fighter_hp: int,
    fighter_max_hp: int,
    boss_hp: int,
    boss_max_hp: int,
) -> str:
    if winner_name == fighter_name:
        return (
            f"\u3010{phase_label}\u7ed3\u679c\u3011{fighter_name} \u538b\u8fc7 {boss_name}\uff0c"
            f"\u81ea\u8eab\u5269\u4f59 {fighter_hp}/{fighter_max_hp}\uff0cBOSS \u5269\u4f59 {boss_hp}/{boss_max_hp}\u3002"
        )
    if winner_name == boss_name:
        return f"\u3010{phase_label}\u7ed3\u679c\u3011{fighter_name} \u9000\u573a\uff0c{boss_name} \u4ecd\u4f59 {boss_hp}/{boss_max_hp}\u3002"
    return (
        f"\u3010{phase_label}\u7ed3\u679c\u3011{fighter_name} \u4e0e {boss_name} \u540c\u65f6\u9000\u573a\uff0c"
        f"BOSS \u5f53\u524d {boss_hp}/{boss_max_hp}\u3002"
    )


def boss_settlement_message(payload: dict[str, Any] | None, closed_without_kill: bool = False) -> str:
    if closed_without_kill:
        return "【世界BOSS已关闭】本期世界BOSS未被击杀，山门重闭，可使用 /bosssettle 发放未击杀版贡献奖励。"
    if not payload:
        return "【世界BOSS结算】当前没有可展示的击杀结算。"
    lines = [f"【世界BOSS结算】{payload.get('boss_name', '世界BOSS')}"]
    settlement_type = str(payload.get("settlement_type") or "killed")
    participant_rewards = payload.get("participant_rewards") or []
    rank_rewards = payload.get("rank_rewards") or []
    if settlement_type == "killed":
        lines.append("本期已击杀，先发参与奖励，再按贡献榜发额外排行奖励。")
    else:
        lines.append("本期未击杀关闭，本次仅发放未击杀版贡献排行奖励。")
    if participant_rewards:
        sample = participant_rewards[0]
        sample_items = sample.get("items") or []
        item_text = "、".join(f"{entry['item_name']}x{entry['quantity']}" for entry in sample_items)
        if item_text:
            lines.append(
                f"参与奖励: 所有有贡献记录的成员 +{sample['points']}积分，外加 {item_text}"
            )
        else:
            lines.append(f"参与奖励: 所有有贡献记录的成员 +{sample['points']}积分")
    if not rank_rewards:
        lines.append("本期没有可发放的贡献奖励。")
        return "\n".join(lines)
    lines.append("排行奖励:")
    for reward in rank_rewards[:10]:
        item_text = ""
        if reward.get("items"):
            item_text = " | " + "、".join(f"{entry['item_name']}x{entry['quantity']}" for entry in reward["items"])
        lines.append(
            f"第{reward['rank']}名 {reward['display_name']} | 伤害 {reward['total_damage']} | +{reward['points']}积分{item_text}"
        )
    return "\n".join(lines)


def boss_help_message() -> str:
    return "\n".join(
        [
            "【世界BOSS帮助】",
            "常用命令:",
            "/boss - 查看当前状态、血量、次数和本期奖励预览",
            "/bossfight - 详细版挑战，展示完整阶段日志",
            "/bossquick - 快速版挑战，只看阶段摘要",
            "/bosssim [phase1|phase2] - 详细演练，不扣次数，不写共享血量",
            "/bosssimquick [phase1|phase2] - 快速演练，不扣次数，不写共享血量",
            "/bossrank - 查看贡献榜",
            "/bossopen /bossclose /bosssettle - 管理员开启、关闭、结算",
            "规则:",
            "每次挑战都先打一阶段，只有二阶段伤害计入共享血量和贡献榜。",
            "每人每天默认 3 次挑战次数。",
            "击杀成功时，所有有贡献记录的成员都会先拿一层参与奖励。",
            "之后再按贡献榜额外发排行奖励；未击杀关闭时则改发未击杀版排行奖励。",
            "奖励预览:",
            "击杀参与: +500积分 + 特殊召唤令x2 + 天机残卷x2 + 换宗令x2 + 中星尘丹x3 + 小星尘丹x5",
            "击杀排行: 第1 +1500积分+特殊召唤令x3+天机残卷x2+中星尘丹x6",
            "击杀排行: 第2 +1200积分+特殊召唤令x2+天机残卷x1+中星尘丹x5",
            "击杀排行: 第3 +1000积分+特殊召唤令x1+换宗令x2+中星尘丹x4",
            "击杀排行: 第4-5 +800积分+换宗令x2+中星尘丹x3+小星尘丹x4",
            "击杀排行: 第6-10 +500积分+换宗令x1+中星尘丹x2+小星尘丹x3",
            "未击杀排行: 第1 +900积分+特殊召唤令x1+天机残卷x1+中星尘丹x4",
            "未击杀排行: 第2 +700积分+换宗令x2+中星尘丹x3",
            "未击杀排行: 第3 +500积分+换宗令x1+中星尘丹x2",
            "未击杀排行: 第4-10 +300积分+小星尘丹x3",
        ]
    )
