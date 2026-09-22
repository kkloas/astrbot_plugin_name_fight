# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import uuid
from typing import Any

from PIL import Image, ImageDraw, ImageFont

try:
    from .render_profile import _find_font, _paste_avatar, get_stat_color
except ImportError:
    from render_profile import _find_font, _paste_avatar, get_stat_color

TEMPLATE_CANDIDATES = {
    'dragon_chief_phase1': ['boss_phase1_template.jpg', 'boss_phase1.jpg'],
    'dragon_chief_phase2': ['boss_phase2_template.jpg', 'boss_phase2.jpg'],
}

TITLE_FONT_SIZE = 64
SKILL_FONT_SIZE = 34
NUMBER_FONT_SIZE = 36
NAME_CENTER_X = 550
NAME_Y = 135
SKILL_X = 450
SKILL_YS = (385, 475, 565)
LEFT_CENTER = 330
RIGHT_CENTER = 630
ROW_YS = (698, 793, 888)
NAME_MAX_WIDTH = 430
SKILL_MAX_WIDTH = 275
NAME_FALLBACK = '世界BOSS'
MARTIAL_FALLBACK = '无名武学'
NEIGONG_FALLBACK = '无名内功'
QINGGONG_FALLBACK = '无名轻功'
NAME_COLOR = (245, 235, 210)
SKILL_COLOR = (205, 185, 155)
STROKE_DARK = (40, 30, 20)
TITLE_STROKE = (30, 20, 10)


def _template_path(data_dir: str, payload: dict[str, Any]) -> str | None:
    boss_key = str(payload.get('boss_key') or '').strip()
    for filename in TEMPLATE_CANDIDATES.get(boss_key, []):
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            return path
    return None


def _build_font(data_dir: str, filename: str, fallbacks: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = _find_font(data_dir, filename, fallbacks)
    try:
        return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
    except OSError:
        return ImageFont.load_default()


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font_factory, max_width: int, min_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for size in range(font_factory['size'], min_size - 1, -2):
        font = font_factory['builder'](size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
    return font_factory['builder'](min_size)


def _truncate_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int) -> str:
    if not text:
        return ''
    bbox = draw.textbbox((0, 0), text, font=font)
    if (bbox[2] - bbox[0]) <= max_width:
        return text
    ellipsis = '...'
    for idx in range(len(text) - 1, 0, -1):
        candidate = text[:idx] + ellipsis
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return candidate
    return ellipsis


def _draw_centered(draw: ImageDraw.ImageDraw, cx: int, y: int, text: str, font, color: tuple[int, int, int]) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text(
        (cx - width / 2, y),
        text,
        font=font,
        fill=color,
        stroke_width=3,
        stroke_fill=STROKE_DARK,
    )


def render_boss_card(payload: dict[str, Any], data_dir: str, avatar_path: str | None = None) -> str | None:
    template_path = _template_path(data_dir, payload)
    if not template_path or not os.path.exists(template_path):
        return None

    output_filename = f'tmp_boss_card_{uuid.uuid4().hex[:8]}.jpg'
    output_path = os.path.join(data_dir, output_filename)

    img = Image.open(template_path).convert('RGBA')
    if avatar_path:
        _paste_avatar(img, {'avatar_path': avatar_path})
    draw = ImageDraw.Draw(img)

    title_factory = {
        'size': TITLE_FONT_SIZE,
        'builder': lambda size: _build_font(data_dir, 'STXINGKA.TTF', [r'C:\Windows\Fonts\STXINGKA.TTF'], size),
    }
    skill_factory = {
        'size': SKILL_FONT_SIZE,
        'builder': lambda size: _build_font(data_dir, 'STKAITI.TTF', [r'C:\Windows\Fonts\STKAITI.TTF'], size),
    }
    number_font = _build_font(data_dir, 'STKAITI.TTF', [r'C:\Windows\Fonts\STKAITI.TTF'], NUMBER_FONT_SIZE)

    boss_name = str(payload.get('name') or NAME_FALLBACK)
    martial_name = str((payload.get('martial_art') or {}).get('name') or MARTIAL_FALLBACK)
    neigong_name = str((payload.get('neigong') or {}).get('name') or NEIGONG_FALLBACK)
    qinggong_name = str((payload.get('qinggong') or {}).get('name') or QINGGONG_FALLBACK)

    name_font = _fit_text(draw, boss_name, title_factory, NAME_MAX_WIDTH, 34)
    boss_name = _truncate_text(draw, boss_name, name_font, NAME_MAX_WIDTH)
    bbox = draw.textbbox((0, 0), boss_name, font=name_font)
    name_width = bbox[2] - bbox[0]
    draw.text(
        (NAME_CENTER_X - name_width / 2, NAME_Y),
        boss_name,
        font=name_font,
        fill=NAME_COLOR,
        stroke_width=2,
        stroke_fill=TITLE_STROKE,
    )

    for text, y in zip((martial_name, neigong_name, qinggong_name), SKILL_YS):
        skill_font = _fit_text(draw, text, skill_factory, SKILL_MAX_WIDTH, 24)
        text = _truncate_text(draw, text, skill_font, SKILL_MAX_WIDTH)
        draw.text((SKILL_X, y), text, font=skill_font, fill=SKILL_COLOR, stroke_width=1, stroke_fill=STROKE_DARK)

    stats = payload.get('stats') or {}
    hp_val = float(stats.get('hp', 0))
    atk_val = float(stats.get('atk', 0))
    def_val = float(stats.get('def', 0))
    spd_val = float(stats.get('spd', 0))
    crt_val = float(stats.get('crt', 0))
    eva_val = float(stats.get('eva', 0))

    _draw_centered(draw, LEFT_CENTER, ROW_YS[0], str(int(hp_val)), number_font, get_stat_color('hp', hp_val))
    _draw_centered(draw, LEFT_CENTER, ROW_YS[1], str(int(atk_val)), number_font, get_stat_color('atk', atk_val))
    _draw_centered(draw, LEFT_CENTER, ROW_YS[2], str(int(def_val)), number_font, get_stat_color('def', def_val))
    _draw_centered(draw, RIGHT_CENTER, ROW_YS[0], f'{spd_val:.1f}', number_font, get_stat_color('spd', spd_val))
    _draw_centered(draw, RIGHT_CENTER, ROW_YS[1], f'{crt_val:.1f}%', number_font, get_stat_color('crt', crt_val))
    _draw_centered(draw, RIGHT_CENTER, ROW_YS[2], f'{eva_val:.1f}%', number_font, get_stat_color('eva', eva_val))

    img.convert('RGB').save(output_path, quality=95)
    return output_path
