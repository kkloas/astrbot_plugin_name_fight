# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import uuid
from typing import Any
from PIL import Image, ImageDraw, ImageFont

AVATAR_BOX = (126, 96, 332, 302)
try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_LANCZOS = Image.LANCZOS


def _find_font(data_dir: str, name: str, fallbacks: list[str]) -> str | None:
    """优先从 data 目录找字体，再找系统路径"""
    bundled = os.path.join(data_dir, name)
    if os.path.exists(bundled):
        return bundled
    for fb in fallbacks:
        if os.path.exists(fb):
            return fb
    return None


def _build_avatar_layer(avatar_path: str, size: int) -> Image.Image | None:
    if not avatar_path or not os.path.exists(avatar_path):
        return None
    avatar = Image.open(avatar_path).convert("RGBA")
    side = min(avatar.size)
    left = (avatar.width - side) // 2
    top = (avatar.height - side) // 2
    avatar = avatar.crop((left, top, left + side, top + side))
    avatar = avatar.resize((size, size), RESAMPLE_LANCZOS)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    avatar.putalpha(mask)
    return avatar


def _paste_avatar(img: Image.Image, fighter: dict[str, Any]) -> None:
    avatar_path = str(fighter.get("avatar_path") or "").strip()
    if not avatar_path:
        return
    left, top, right, bottom = AVATAR_BOX
    size = min(right - left, bottom - top)
    avatar = _build_avatar_layer(avatar_path, size)
    if avatar is None:
        return
    img.alpha_composite(avatar, (left, top))


def get_stat_color(stat: str, value: float) -> tuple[int, int, int]:
    """绿/蓝/紫/橙/红五级属性色彩，严格对齐 stat_comment 文字分级"""
    colors = [
        (80, 255, 80),
        (50, 200, 255),
        (230, 80, 255),
        (255, 160, 0),
        (255, 70, 70),
    ]
    thresholds = {
        'hp':  [420, 520, 620, 760],
        'atk': [70,  85,  100, 140],
        'def': [65,  80,  95,  130],
        'spd': [45,  58,  72,  110],
        'crt': [12,  18,  24,  36],
        'eva': [16,  22,  28,  42],
    }
    t = thresholds.get(stat)
    if t is None:
        return colors[0]
    for i in range(3, -1, -1):
        if value >= t[i]:
            return colors[i + 1]
    return colors[0]


def render_star_card(fighter: dict[str, Any], data_dir: str) -> str | None:
    """
    根据角色星级渲染 5 星或 6 星的角色立绘面板。
    返回生成图片的本地保存路径，不满足条件时返回 None。
    """
    rating = float(fighter.get('star_rating', 0))
    breakthrough = int(fighter.get('breakthrough_stage', 0) or 0)

    if rating >= 6.0 or breakthrough > 0:
        template_name = "6star_template.jpg"
    elif rating >= 5.0:
        template_name = "5star_template.jpg"
    else:
        return None
    template_path = os.path.join(data_dir, template_name)
    if not os.path.exists(template_path):
        return None

    output_filename = f"tmp_card_{uuid.uuid4().hex[:8]}.jpg"
    output_path = os.path.join(data_dir, output_filename)

    img = Image.open(template_path).convert("RGBA")
    _paste_avatar(img, fighter)
    draw = ImageDraw.Draw(img)

    title_path = _find_font(data_dir, "STXINGKA.TTF", [
        r"C:\Windows\Fonts\STXINGKA.TTF",
    ])
    normal_path = _find_font(data_dir, "STKAITI.TTF", [
        r"C:\Windows\Fonts\STKAITI.TTF",
    ])

    try:
        font_title = ImageFont.truetype(title_path, 64) if title_path else ImageFont.load_default()
        font_normal = ImageFont.truetype(normal_path, 32) if normal_path else ImageFont.load_default()
        font_skill = ImageFont.truetype(normal_path, 34) if normal_path else ImageFont.load_default()
        font_number = ImageFont.truetype(normal_path, 36) if normal_path else ImageFont.load_default()
    except IOError:
        font_title = font_normal = font_skill = font_number = ImageFont.load_default()

    fighter_name = str(fighter.get("name", "未知"))
    martial_art = fighter.get("martial_art", {})
    neigong = fighter.get("neigong", {})
    qinggong = fighter.get("qinggong", {})

    martial_name = martial_art.get("name", "无名武学")
    neigong_name = neigong.get("name", "无名内功")
    qinggong_name = qinggong.get("name", "无名轻功")

    stats = fighter.get("stats", {})
    hp_val = float(stats.get("hp", 0))
    spd_val = float(stats.get("spd", 0))
    atk_val = float(stats.get("atk", 0))
    crt_val = float(stats.get("crt", 0))
    dfn_val = float(stats.get("def", 0))
    eva_val = float(stats.get("eva", 0))

    hp = str(int(hp_val))
    spd = f"{spd_val:.1f}"
    atk = str(int(atk_val))
    crt = f"{crt_val:.1f}%"
    dfn = str(int(dfn_val))
    eva = f"{eva_val:.1f}%"

    color_name = (245, 235, 210)
    color_skill = (205, 185, 155)

    name_center_x = 550
    name_y = 135
    bbox = draw.textbbox((0, 0), fighter_name, font=font_title)
    name_w = bbox[2] - bbox[0]
    draw.text(
        (name_center_x - name_w / 2, name_y), fighter_name,
        font=font_title, fill=color_name,
        stroke_width=2, stroke_fill=(30, 20, 10)
    )

    skill_x = 450
    draw.text((skill_x, 385), martial_name, font=font_skill, fill=color_skill, stroke_width=1, stroke_fill=(40, 30, 20))
    draw.text((skill_x, 475), neigong_name, font=font_skill, fill=color_skill, stroke_width=1, stroke_fill=(40, 30, 20))
    draw.text((skill_x, 565), qinggong_name, font=font_skill, fill=color_skill, stroke_width=1, stroke_fill=(40, 30, 20))

    left_center = 330
    right_center = 630
    row1_y = 698
    row2_y = 793
    row3_y = 888

    def draw_centered(cx, y, text, color):
        box = draw.textbbox((0, 0), text, font=font_number)
        w = box[2] - box[0]
        draw.text(
            (cx - w / 2, y), text, font=font_number, fill=color,
            stroke_width=3, stroke_fill=(40, 30, 20),
        )

    draw_centered(left_center,  row1_y, hp,  get_stat_color('hp',  hp_val))
    draw_centered(left_center,  row2_y, atk, get_stat_color('atk', atk_val))
    draw_centered(left_center,  row3_y, dfn, get_stat_color('def', dfn_val))
    draw_centered(right_center, row1_y, spd, get_stat_color('spd', spd_val))
    draw_centered(right_center, row2_y, crt, get_stat_color('crt', crt_val))
    draw_centered(right_center, row3_y, eva, get_stat_color('eva', eva_val))

    out_img = img.convert("RGB")
    out_img.save(output_path, quality=95)
    return output_path



