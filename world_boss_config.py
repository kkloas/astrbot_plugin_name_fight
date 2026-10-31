"""Shared world boss rules and phase templates for Bot and Web."""

WORLD_BOSS_DAILY_LIMIT = 3

WORLD_BOSS_NAME = "群龙之首"

WORLD_BOSS_PHASE1 = {
    "boss_key": "dragon_chief_phase1",
    "name": "群龙之首·破阵前锋",
    "label": "一阶段",
    "description": "前锋镇守山门，先破其阵，方能逼出真身。",
    "stats": {"hp": 1100, "atk": 110, "def": 70, "spd": 96.0, "crt": 8.0, "eva": 5.0},
    "martial_art_id": "sword_huashan",
    "neigong_id": "shenzhao_jing",
    "qinggong_id": "lightning_flash",
    "martial_art_skin": {
        "name": "锁关剑阵",
        "summary": "剑势连环封路，专为守门而设，压迫感强于杀伤。",
    },
    "neigong_skin": {
        "name": "镇岳罡息",
        "summary": "护体真气厚重绵长，前排硬抗时更显韧性。",
    },
    "qinggong_skin": {
        "name": "巡门疾步",
        "summary": "步法紧凑稳健，重在抢位拦截，不以花巧见长。",
    },
}

WORLD_BOSS_PHASE2 = {
    "boss_key": "dragon_chief_phase2",
    "name": "群龙之首·真身",
    "label": "二阶段",
    "description": "真身现世后共享血量开启，全群合力围攻，按贡献结算。",
    "stats": {"hp": 50000, "atk": 95, "def": 105, "spd": 92.0, "crt": 6.0, "eva": 4.0},
    "martial_art_id": "sword_huashan",
    "neigong_id": "shenzhao_jing",
    "qinggong_id": "lightning_flash",
    "martial_art_skin": {
        "name": "龙首镇岳剑",
        "summary": "剑路大开大阖，以厚重威压统摄全场，久战压阵。",
    },
    "neigong_skin": {
        "name": "万壑归元功",
        "summary": "真元深锁于体，血厚防高，越围攻越难撼动。",
    },
    "qinggong_skin": {
        "name": "潜龙回岳步",
        "summary": "身法不求极速，只求沉稳换位，专注拖长战线。",
    },
}
