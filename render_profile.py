# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import uuid
from typing import Any
from PIL import Image, ImageDraw, ImageFont

def render_6_star_card(fighter: dict[str, Any], data_dir: str) -> str:
    """
    渲染 6 星角色的立绘面板。
    返回生成图片的本地保存路径。
    """
    template_path = os.path.join(data_dir, "6star_template.jpg")
    output_filename = f"tmp_6star_{uuid.uuid4().hex[:8]}.jpg"
    output_path = os.path.join(data_dir, output_filename)
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Missing template image at {template_path}")

    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 字体加载：优先使用打包在 data 目录里的字体，兼容 Linux/Docker
    def _find_font(name: str, fallbacks: list[str]) -> str | None:
        # 1. 先找 data 目录里打包的
        bundled = os.path.join(data_dir, name)
        if os.path.exists(bundled):
            return bundled
        # 2. 再找系统路径
        for fb in fallbacks:
            if os.path.exists(fb):
                return fb
        return None

    title_path = _find_font("STXINGKA.TTF", [
        r"C:\Windows\Fonts\STXINGKA.TTF",
        "/usr/share/fonts/truetype/STXINGKA.TTF",
    ])
    normal_path = _find_font("STKAITI.TTF", [
        r"C:\Windows\Fonts\STKAITI.TTF",
        "/usr/share/fonts/truetype/STKAITI.TTF",
    ])

    try:
        font_title = ImageFont.truetype(title_path, 64) if title_path else ImageFont.load_default()
        font_normal = ImageFont.truetype(normal_path, 32) if normal_path else ImageFont.load_default()
        font_number = ImageFont.truetype(normal_path, 30) if normal_path else ImageFont.load_default()
    except IOError:
        font_title = font_normal = font_number = ImageFont.load_default()

    # 提取数据
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
    color = (205, 185, 155)      

    def get_stat_color(stat: str, value: float) -> tuple[int, int, int]:
        colors = [
            (255, 255, 255), # 0: 白 (纯白)
            (80, 255, 80),   # 1: 绿 (亮绿)
            (50, 200, 255),  # 2: 蓝 (亮蓝)
            (230, 80, 255),  # 3: 紫 (亮紫)
            (255, 160, 0),   # 4: 橙 (亮橙)
            (255, 50, 50)    # 5: 红 (大红)
        ]
        if stat == 'hp':
            if value >= 850: return colors[5]
            if value >= 760: return colors[4]
            if value >= 620: return colors[3]
            if value >= 520: return colors[2]
            if value >= 420: return colors[1]
        elif stat == 'atk':
            if value >= 160: return colors[5]
            if value >= 140: return colors[4]
            if value >= 100: return colors[3]
            if value >= 85: return colors[2]
            if value >= 70: return colors[1]
        elif stat == 'def':
            if value >= 150: return colors[5]
            if value >= 130: return colors[4]
            if value >= 95: return colors[3]
            if value >= 80: return colors[2]
            if value >= 65: return colors[1]
        elif stat == 'spd':
            if value >= 125: return colors[5]
            if value >= 110: return colors[4]
            if value >= 72: return colors[3]
            if value >= 58: return colors[2]
            if value >= 45: return colors[1]
        elif stat == 'crt':
            if value >= 45: return colors[5]
            if value >= 36: return colors[4]
            if value >= 24: return colors[3]
            if value >= 18: return colors[2]
            if value >= 12: return colors[1]
        elif stat == 'eva':
            if value >= 55: return colors[5]
            if value >= 42: return colors[4]
            if value >= 28: return colors[3]
            if value >= 22: return colors[2]
            if value >= 16: return colors[1]
        return colors[0]

    # 绘制名字
    name_center_x = 550
    name_y = 135
    bbox = draw.textbbox((0, 0), fighter_name, font=font_title)
    name_w = bbox[2] - bbox[0]
    draw.text((name_center_x - name_w / 2, name_y), fighter_name, font=font_title, fill=color_name)

    # 绘制武学等
    skill_x = 450 
    draw.text((skill_x, 385), martial_name, font=font_normal, fill=color)
    draw.text((skill_x, 475), neigong_name, font=font_normal, fill=color)
    draw.text((skill_x, 565), qinggong_name, font=font_normal, fill=color)

    # 绘制面板
    left_center = 330
    right_center = 630

    row1_y = 698
    row2_y = 793
    row3_y = 888

    def draw_centered_number(center_x, y, text, fill_color):
        box = draw.textbbox((0, 0), text, font=font_number)
        w = box[2] - box[0]
        draw.text((center_x - w / 2, y), text, font=font_number, fill=fill_color, stroke_width=2, stroke_fill=(40, 30, 20))

    draw_centered_number(left_center, row1_y, hp, get_stat_color('hp', hp_val))
    draw_centered_number(left_center, row2_y, atk, get_stat_color('atk', atk_val))
    draw_centered_number(left_center, row3_y, dfn, get_stat_color('def', dfn_val))
    
    draw_centered_number(right_center, row1_y, spd, get_stat_color('spd', spd_val))
    draw_centered_number(right_center, row2_y, crt, get_stat_color('crt', crt_val))
    draw_centered_number(right_center, row3_y, eva, get_stat_color('eva', eva_val))

    # 保存输出
    out_img = img.convert("RGB")
    out_img.save(output_path, quality=95)
    return output_path
