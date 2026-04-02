# Combat Flow

这份文档用于说明 `Name Fight` 当前版本的真实战斗计算流程。

目标有两个：

- 让没接触过项目的人，也能顺着代码理解一场战斗是如何推进的
- 给后续策划、平衡和 AI 协作提供统一口径

本文对应的是当前项目里的实际实现，不是纯设计草案。

相关实现文件：

- [database.py](/D:/NFIGHTPLUS/astrbot_plugin_name_fight/database.py)
- [engine.py](/D:/NFIGHTPLUS/astrbot_plugin_name_fight/engine.py)
- [configs/martial_arts.json](/D:/NFIGHTPLUS/astrbot_plugin_name_fight/configs/martial_arts.json)
- [configs/neigong.json](/D:/NFIGHTPLUS/astrbot_plugin_name_fight/configs/neigong.json)
- [configs/qinggong.json](/D:/NFIGHTPLUS/astrbot_plugin_name_fight/configs/qinggong.json)

## 1. 总览

当前战斗系统可以分成两层：

1. 战斗前，先把角色面板算出来
2. 战斗中，再按行动条、闪避、部位、伤害、状态逐手推进

如果只记一句话，可以记成：

```text
最终战斗 = 面板生成 + 行动条推进 + 单手结算
```

## 2. 战斗前：角色面板如何生成

### 2.1 基础六维

每个角色会先生成基础六维：

- `hp`
- `atk`
- `def`
- `spd`
- `crt`
- `eva`

基础池来自 [database.py](/D:/NFIGHTPLUS/astrbot_plugin_name_fight/database.py) 的 `_generate_base_stats()`：

```text
total_pool = 340 ~ 460

raw hp  = 110 ~ 190
raw atk = 42 ~ 96
raw def = 32 ~ 88
raw spd = 22 ~ 64
raw crt = 6 ~ 26
raw eva = 6 ~ 24
```

然后按总池统一缩放：

```text
scale = total_pool / sum(raw_stats)
scaled_stat = raw_stat x scale
```

其中：

- `crt` 会被限制在 `4.0 ~ 38.0`
- `eva` 会被限制在 `4.0 ~ 38.0`

### 2.2 武学 / 内功 / 轻功修正

基础六维生成后，会叠加三类配置修正。

武学修正：

```text
atk = base_atk x martial.atk
spd = base_spd x martial.spd
crt = base_crt x martial.crt
eva = base_eva x martial.eva
```

内功修正：

```text
hp  = base_hp x neigong.hp_multiplier
def = base_def x neigong.def_multiplier
```

轻功修正：

```text
spd = spd x qinggong.spd_multiplier
eva = eva + qinggong.eva_bonus
```

### 2.3 最终战斗面板

最后进入战斗的六维会做统一收口：

```text
hp  = round(hp x HP_BATTLE_SCALE)
atk = round(atk)
def = round(def)
spd = round(spd, 2)
crt = clamp(round(crt, 2), 1, 65)
eva = clamp(round(eva, 2), 1, 65)
```

其中：

```text
HP_BATTLE_SCALE = 2.2
```

这意味着项目会故意把气血拉高，避免战斗过快结束。

## 3. 进入战斗后的基础状态

每个角色进入战斗后，会被包装成一个 Actor。

除了面板外，还会有这些战斗态：

- `hp`
- `max_hp`
- `ag`
- `states`
- `passive_usage`
- `special_usage`
- `weapon_ready`

含义分别是：

- `hp`: 当前气血
- `max_hp`: 最大气血
- `ag`: 行动条，初始为 `0`
- `states`: 当前挂着的状态列表
- `passive_usage`: 内功被动已触发次数
- `special_usage`: 轻功特殊效果已触发次数
- `weapon_ready`: 是否能正常出招，`缴械` 会让它变成 `False`

## 4. 战斗主循环

### 4.1 行动条推进

战斗不是轮流制，而是行动条制。

每个 tick，双方都会累积行动条：

```text
ag += effective_spd
```

当：

```text
ag >= 100
```

角色就获得出手机会。

### 4.2 多人同时可出手时的处理

如果同一个 tick 里双方都 `ag >= 100`，会按这两个键排序：

1. `ag` 更高者优先
2. 如果 `ag` 一样，再用随机数打破平手

出手后会扣：

```text
ag -= 100
```

所以 `spd` 的本质不是“加一点手感”，而是直接决定单位时间内出多少手。

## 5. 一手行动的真实结算顺序

一次完整出手，当前代码按下面顺序执行：

1. 输出这手的起手文本
2. 结算回合开始状态
3. 如果武器未就绪，则本手先捡武器
4. 随机抽一个招式
5. 判定目标是否闪避
6. 选择命中部位
7. 计算伤害
8. 判定暴击
9. 结算吸血 / 反震 / 残血被动
10. 结算招式附带状态
11. 扣减本手结束时需要衰减的状态
12. 清理过期状态

下面逐项拆开。

## 6. 回合开始状态

### 6.1 眩晕

如果当前存在 `stunned`：

- 本手直接被跳过
- `duration -= 1`

也就是说，眩晕的效果是“让目标白白浪费这一手”。

### 6.2 流血

如果当前存在 `bleeding`，会在出手前先掉血：

```text
BleedDamage = max(1, round(source_atk x atk_scale - effective_def x 0.25))
```

然后：

- 目标扣血
- `duration -= 1`

所以流血不是固定数值，而是：

- 跟施加者当时的攻击有关
- 跟当前受击者的有效防御也有关

### 6.3 回春类被动

如果内功有 `regeneration`，会在回合开始回血。

当前回血量是：

```text
Heal = max(1, int(max_hp x heal_ratio))
```

再封顶到当前缺失血量。

## 7. 缴械与武器状态

如果角色当前：

```text
weapon_ready = False
```

那么这一手不会攻击，而是先恢复武器状态：

```text
weapon_ready = True
```

然后本手结束。

这就是 `缴械` 在当前引擎里的真实效果：

- 不是直接减数值
- 而是强行浪费目标下一手

## 8. 招式选择

当前实现里，每次出手都会从这门武学的 `moves` 里随机抽一招：

```text
move = random.choice(martial_art.moves)
```

目前没有单独的招式冷却、优先级或连段机制。

## 9. 闪避判定

命中不是单独算“命中率”，而是只看目标有没有闪开。

当前判定：

```text
if random(0, 100) < effective_eva:
    闪避成功
else:
    命中
```

其中：

```text
effective_eva = 0, if stunned
effective_eva = stats.eva, otherwise
```

这意味着：

- `eva` 就是直接的百分比闪避率
- 目标被眩晕时，无法闪避

## 10. 命中部位选择

### 10.1 招式写了 `target_weights`

如果招式自己写了 `target_weights`，优先按该招式的权重抽取。

例如：

```text
target_weights = {
  胸口: 60,
  手臂: 40
}
```

就会按这个比例抽。

### 10.2 招式没写 `target_weights`

如果招式没有单独写，就走全局部位表，并叠加武学 / 招式偏好：

```text
final_weight
+= base_body_part_weight
x martial.target_bias
x move.target_bias
```

### 10.3 主要部位倍率

当前系统里的主要部位倍率是：

- `head`: 权重 `0.13`，伤害 `x1.35`
- `chest`: 权重 `0.24`，伤害 `x1.20`
- `arm`: 权重 `0.21`，伤害 `x0.90`
- `abdomen`: 权重 `0.24`，伤害 `x1.00`
- `leg`: 权重 `0.18`，伤害 `x0.85`

另外，像 `双眼`、`双耳`、`面门`、`天灵` 等中文文本，会先映射到统一的部位键。

## 11. 伤害计算公式

这是当前项目里最核心的直伤公式。

### 11.1 有效攻击

```text
effective_atk = stats.atk
effective_atk *= atk_multiplier, if weakened
```

### 11.2 有效防御

```text
effective_def = stats.def
effective_def *= def_multiplier, if armor_broken
effective_def *= (1 + def_bonus_ratio), if crisis_defense
```

### 11.3 招式倍率

如果招式写了 `damage_multiplier`，直接用它。

```text
move_multiplier = damage_multiplier
```

如果是旧式写法，则用：

```text
move_multiplier = random(power_min, power_max)
```

### 11.4 部位防护

内功可以通过 `part_guard` 对特定部位再做修正：

```text
guard_multiplier = neigong.part_guard[part_key]
```

如果该部位没有写保护值，则默认：

```text
guard_multiplier = 1.0
```

### 11.5 主公式

```text
raw_damage =
    effective_atk
    x move_multiplier
    x random_variance
    x body_part_multiplier
    - effective_def x 0.5
```

然后乘部位防护：

```text
reduced_damage = raw_damage x guard_multiplier
```

再做保底：

```text
minimum_damage = max(1, int(effective_atk x 0.1))
final_damage = max(minimum_damage, round(reduced_damage))
```

随机波动当前是：

```text
random_variance = 0.92 ~ 1.08
```

### 11.6 暴击

暴击判定是：

```text
if random(0, 100) < effective_crt:
    final_damage x= 2
```

其中：

```text
effective_crt = stats.crt
```

也就是说，暴击是：

- 单独百分比判定
- 触发后直接让最终伤害翻倍

## 12. 吸血、反震、残血被动

命中后，会继续结算内功和阈值机制。

### 12.1 吸血

如果攻击方有 `vampirism`：

```text
heal = min(int(damage x leech_ratio), missing_hp)
```

### 12.2 反震

如果受击方有 `thorns`：

```text
reflect = max(1, int(damage x reflect_ratio))
```

然后攻击方会受到这段反伤。

### 12.3 残血爆发回血

如果内功被动是 `burst_heal`，并且：

```text
hp / max_hp <= trigger_hp_ratio
```

则会触发一次性回血：

```text
heal = max(1, int(max_hp x heal_ratio))
```

### 12.4 残血防御提升

如果内功被动是 `crisis_defense`，并且：

```text
hp / max_hp <= trigger_hp_ratio
```

则会给自己挂一个持续状态：

```text
state = {
  type: crisis_defense,
  def_bonus_ratio: ...
}
```

之后防御就会按加成后的值继续结算。

### 12.5 开场绝对先手

如果轻功特殊效果是 `battle_start_first_strike`：

- 战斗开始时直接把 `ag` 提到 `100`
- 等于开场抢先出手

### 12.6 残血额外行动

如果轻功特殊效果是 `low_hp_extra_action`，且血量比例低于阈值：

```text
ag = max(ag, 1000)
```

这会让角色立刻拿到额外行动机会。

## 13. 招式状态附加

每个招式的 `effects` 都会单独判一次。

真实触发率：

```text
actual_chance = effect.chance + effect.part_bonus[part_key]
```

如果判定通过，就把状态挂到目标身上。

当前常见状态含义如下：

- `stunned`: 下一手直接不能动
- `bleeding`: 回合开始掉血
- `weakened`: 攻击乘 `atk_multiplier`
- `slowed`: 速度乘 `spd_multiplier`
- `armor_broken`: 防御乘 `def_multiplier`
- `disarmed`: 下手先捡武器

如果同类状态重复命中，当前实现不是简单叠多层，而是：

- 更新状态内容
- `duration` 取更长的那个

## 14. 状态持续时间怎么掉

当前状态衰减不是统一在一个地方，而是分类型处理：

- `stunned`: 在它真正让目标失去行动时 `duration -= 1`
- `bleeding`: 在它真正跳血时 `duration -= 1`
- `weakened`: 攻击手结束后 `duration -= 1`
- `slowed`: 攻击手结束后 `duration -= 1`
- `disarmed`: 攻击手结束后 `duration -= 1`
- `armor_broken`: 攻击手结束后 `duration -= 1`

最后统一清理：

```text
duration <= 0 -> 移除
```

## 15. 战斗如何结束

### 15.1 直接击杀

如果有人 `hp <= 0`，战斗立即结束。

### 15.2 到达战斗上限

当前主循环有两个上限：

- `max_ticks = 100`
- `max_actions = 50`

如果拖到上限，就按血量比例判胜负：

```text
hp_ratio = hp / max_hp
```

规则是：

- 如果双方比例差 `< 0.01`，判平
- 否则血量比例更高的一方胜

## 16. 单回合手算样例

下面给一个完整、可复核的单手样例。

这不是固定剧情，而是“按当前真实公式手算”的演示。为了让每一步可见，样例中的随机结果会被显式写出来。

### 16.1 样例前提

攻击方 `A` 当前状态：

```text
hp  = 420 / 460
atk = 110
def = 48
spd = 50.8
crt = 17.0
eva = 36.4
ag  = 68.4
states = []
weapon_ready = True
```

防守方 `B` 当前状态：

```text
hp  = 462 / 462
atk = 98
def = 52
spd = 44.2
crt = 22.0
eva = 22.0
ag  = 31.0
states = []
weapon_ready = True
part_guard.chest = 0.9
```

攻击方这一手抽到的招式设定：

```text
move_name = 风起云涌
damage_multiplier = 1.15
effects = [
  weakened: chance 0.30, duration 2, atk_multiplier 0.75
]
target_weights = {
  胸口: 60,
  腰腹: 40
}
```

本手假定随机结果如下：

- 本 tick 结束后，`A` 先拿到出手机会
- 闪避判定随机数：`47.6`
- 招式部位抽到：`胸口`
- 伤害波动：`1.03`
- 暴击判定随机数：`12.4`
- 状态判定随机数：`0.26`

### 16.2 行动条推进

本 tick 时：

```text
A.ag = 68.4 + 50.8 = 119.2
B.ag = 31.0 + 44.2 = 75.2
```

因此：

- `A` 达到出手门槛
- `B` 还没有

`A` 出手前先扣行动条：

```text
A.ag = 119.2 - 100 = 19.2
```

### 16.3 回合开始状态

`A` 当前：

- 没有 `stunned`
- 没有 `bleeding`
- 没有 `weapon_ready = False`

所以可以正常出招。

### 16.4 闪避判定

防守方 `B` 当前：

```text
effective_eva = 22.0
```

本次随机数：

```text
47.6
```

因为：

```text
47.6 < 22.0
```

不成立，所以：

```text
闪避失败，命中继续
```

### 16.5 部位判定

这招只在：

- `胸口: 60`
- `腰腹: 40`

之间抽取。

这次抽到：

```text
part_key = chest
body_part_multiplier = 1.20
guard_multiplier = 0.90
```

### 16.6 计算有效攻击和有效防御

攻击方 `A` 没有 `weakened`：

```text
effective_atk = 110
```

防守方 `B` 没有 `armor_broken`、没有 `crisis_defense`：

```text
effective_def = 52
```

### 16.7 计算基础伤害

已知：

```text
atk = 110
move_multiplier = 1.15
variance = 1.03
part_multiplier = 1.20
def = 52
guard_multiplier = 0.90
```

先算乘区：

```text
110 x 1.15 x 1.03 x 1.20
= 156.354
```

再减防御项：

```text
raw_damage = 156.354 - (52 x 0.5)
= 156.354 - 26
= 130.354
```

再乘部位防护：

```text
reduced_damage = 130.354 x 0.90
= 117.3186
```

### 16.8 保底伤害

当前保底：

```text
minimum_damage = max(1, int(110 x 0.1))
= 11
```

四舍五入后的主伤害：

```text
round(117.3186) = 117
```

所以未暴击前：

```text
damage = max(11, 117) = 117
```

### 16.9 暴击判定

攻击方：

```text
effective_crt = 17.0
```

本次暴击随机数：

```text
12.4
```

因为：

```text
12.4 < 17.0
```

成立，所以触发暴击：

```text
final_damage = 117 x 2 = 234
```

### 16.10 扣血结果

防守方原本：

```text
B.hp = 462
```

受击后：

```text
B.hp = 462 - 234 = 228
```

### 16.11 吸血与反震

如果这一手里，`A` 具有吸血内功：

```text
leech_ratio = 0.08
```

则回血：

```text
heal = int(234 x 0.08) = 18
```

假设 `A` 当前缺失气血超过 18，则：

```text
A.hp = 420 + 18 = 438
```

如果 `B` 具有反震内功：

```text
reflect_ratio = 0.03
```

则反伤：

```text
reflect = max(1, int(234 x 0.03))
= 7
```

于是：

```text
A.hp = 438 - 7 = 431
```

### 16.12 招式状态判定

这一手携带：

```text
weakened: chance 0.30
```

假设这招在胸口没有额外 `part_bonus`，则：

```text
actual_chance = 0.30
```

本次随机数：

```text
0.26
```

因为：

```text
0.26 <= 0.30
```

成立，所以成功挂上：

```text
state = {
  type: weakened,
  duration: 2,
  atk_multiplier: 0.75
}
```

### 16.13 本手结束后的结果总表

这一手打完后，关键内部变量会变成：

攻击方 `A`：

```text
hp  = 431
ag  = 19.2
states = []
```

防守方 `B`：

```text
hp  = 228
ag  = 75.2
states = [
  weakened(duration=2, atk_multiplier=0.75)
]
```

也就是说，这一手实际上完成了这些事：

1. `A` 因为速度更高先出手
2. `B` 没闪开
3. 命中胸口，吃到高部位倍率
4. 因为暴击，伤害从 `117` 翻到 `234`
5. 命中后又触发了 `虚弱`

这就是一手在当前引擎里的完整计算链。

## 17. 属性作用总结

如果只从公式角度看，这 6 项属性的职责可以概括成：

- `hp`
  - 决定总气血上限
  - 影响残局容错
  - 影响残血被动触发区间

- `atk`
  - 决定大部分直伤
  - 决定最低保底伤害
  - 决定流血来源强度

- `def`
  - 在线性层面减直伤
  - 在线性层面减流血
  - 与残局防御类被动叠加

- `spd`
  - 决定行动条推进速度
  - 决定先手和多动

- `crt`
  - 决定暴击概率
  - 暴击时让最终伤害翻倍

- `eva`
  - 直接决定闪避概率
  - 闪开就整手伤害和状态都取消

## 18. 一句话记忆版

如果以后要快速复盘一场战斗，可以直接用这四句：

```text
先算面板，再累行动条。
出手先看状态，再看闪避。
打中之后按 攻击 x 招式 x 波动 x 部位 - 0.5 x 防御 算伤害。
最后再结算暴击、吸血、反震和附加状态。
```
