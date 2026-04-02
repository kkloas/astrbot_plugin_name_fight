# Name Fight

![Name Fight Logo](./logo.png)

一个给 AstrBot 用的武侠名字格斗插件。输入名字，就会生成一名命格固定的角色；围绕武学、内功、轻功展开对决，并在群内累计巅峰分排行。  
A wuxia-flavored AstrBot plugin for deterministic name-based fighter generation, duels, and group peak ranking.

## 项目简介

这个插件的重点，不是做传统数值表，而是做一种“名字入局”的武侠对战体验：

- 同一个名字，永远对应同一套命格
- 每个角色都有自己的武学、内功、轻功与面板倾向
- 对战会播报招式过程、胜负结果与巅峰分变化
- 排行榜按群独立结算，适合长期在群里养成和冲榜

如果你想要的是一个有点江湖味、又能长期玩出竞争感的 AstrBot 插件，这个项目就是按这个方向做的。

## 核心特色

### 1. 同名固定生成

角色不是纯随机漂移，而是按名字稳定生成。  
同一个名字，每次生成出来的属性、武学、内功、轻功都一致，名字本身就是命格种子。

### 2. 武侠风格战斗播报

战斗不是只回一个胜负结果，而是会按过程播报：

- 招式往来
- 命中部位
- 特殊效果
- 回合推进
- 胜负结语
- 战后巅峰分变化

### 3. 巅峰排行榜

项目内置群独立巅峰榜：

- 每个群单独计算
- 前三名有专属显示
- 分数越高，称号越高
- 战斗结束后会直接显示本场加减分

### 4. 数据驱动扩展

武功、内功、轻功都来自 JSON 配置，可以继续往里追加新内容，不需要改核心逻辑就能扩展玩法。

## 指令一览

- `/fhelp` 查看全部指令说明
- `/create 角色名` 创建新角色
- `/choose 序号` 选择要被顶替的旧角色栏位
- `/roster` 查看当前角色栏
- `/use 角色名` 切换当前出战角色
- `/profile [角色名]` 查看角色详情
- `/c 角色名` 发起普通挑战
- `/fc 角色名` 直接强制开战
- `/a` 接受挑战
- `/r` 拒绝挑战
- `/rank` 查看当前群的巅峰排行榜

## 适合的使用场景

- 群聊里长期养角色、冲排行榜
- 用名字抽命格，看谁更强
- 做轻量武侠对战娱乐插件
- 在 AstrBot 里做偏游戏化的互动玩法

## 安装方式

把整个 `astrbot_plugin_name_fight` 目录复制到 AstrBot 的插件目录中。

```text
plugin_data/
  plugins/
    astrbot_plugin_name_fight/
      main.py
      engine.py
      database.py
      text_resources.py
      configs/
      metadata.yaml
```

## 数据文件

- `configs/martial_arts.json`：武功配置
- `configs/neigong.json`：内功配置
- `configs/qinggong.json`：轻功配置
- `name_fight_data/fighters.db`：角色与群排行数据库

## 编码说明

- Python / JSON / Markdown：统一使用 `UTF-8`
- `metadata.yaml`：建议使用 `UTF-8 with BOM`
- 详细约束见 [FORMAT_REQUIREMENTS.md](./FORMAT_REQUIREMENTS.md)

## English Summary

Name Fight is an AstrBot plugin built around deterministic fighter generation from names. The same name always maps to the same fighter build. Battles are presented as wuxia-style combat logs, and each group maintains its own peak ladder with visible rating changes after every match.

## Version

Current version: `1.2.1`
