from PIL import Image, ImageDraw, ImageFont
import os

def create_preview():
    template_path = r"d:\NFIGHTPLUS\astrbot_plugin_name_fight\data\6star_template.jpg"
    artifact_dir = r"C:\Users\pc\.gemini\antigravity\brain\9750566e-4e5c-44c8-b73d-204657209f25\artifacts"
    os.makedirs(artifact_dir, exist_ok=True)
    output_path = os.path.join(artifact_dir, "tmp_preview5.jpg")
    
    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    font_title_path = r"C:\Windows\Fonts\STXINGKA.TTF"
    font_normal_path = r"C:\Windows\Fonts\STKAITI.TTF"
        
    font_title = ImageFont.truetype(font_title_path, 64) 
    font_normal = ImageFont.truetype(font_normal_path, 32)
    font_number = ImageFont.truetype(font_normal_path, 30)

    fighter_name = "风清扬"
    
    martial_name = "独孤九剑"
    neigong_name = "紫霞神功"
    qinggong_name = "神行百变"

    hp, spd = "850", "125.5"
    atk, crt = "165", "45.0%"
    dfn, eva = "85", "30.0%"

    color_name = (245, 235, 210) 
    color = (205, 185, 155)      
    color_num = (240, 230, 210) 

    name_center_x = 550
    name_y = 135
    bbox = draw.textbbox((0, 0), fighter_name, font=font_title)
    name_w = bbox[2] - bbox[0]
    draw.text((name_center_x - name_w / 2, name_y), fighter_name, font=font_title, fill=color_name)

    # 武学字再向右移
    skill_x = 450 
    draw.text((skill_x, 385), martial_name, font=font_normal, fill=color)
    draw.text((skill_x, 475), neigong_name, font=font_normal, fill=color)
    draw.text((skill_x, 565), qinggong_name, font=font_normal, fill=color)

    left_center = 330
    right_center = 630

    row1_y = 698
    row2_y = 793
    row3_y = 888

    def draw_centered_number(center_x, y, text):
        box = draw.textbbox((0, 0), text, font=font_number)
        w = box[2] - box[0]
        draw.text((center_x - w / 2, y), text, font=font_number, fill=color_num)

    draw_centered_number(left_center, row1_y, hp)
    draw_centered_number(left_center, row2_y, atk)
    draw_centered_number(left_center, row3_y, dfn)
    
    draw_centered_number(right_center, row1_y, spd)
    draw_centered_number(right_center, row2_y, crt)
    draw_centered_number(right_center, row3_y, eva)

    out_img = img.convert("RGB")
    out_img.save(output_path, quality=95)
    print(f"saved to {output_path}")

create_preview()
