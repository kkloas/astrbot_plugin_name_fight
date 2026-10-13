# Name Fight

![Name Fight Logo](./logo.png)

Name Fight 是由 kkloas 开发的 AstrBot 群聊武侠对战插件.用姓名生成角色, 通过对战, 签到和世界 BOSS 获取资源, 培养星级, 调整武学与三人阵容.

当前插件版本为 **1.4.1**, 默认分支为 `release-plugin-1-4-1`.本版提供 Bot 插件, Web 应用在 `dev-web` 分支单独开发.

## 功能

- 姓名生成角色, 每位玩家最多保留 5 名角色, 支持角色卡和自定义头像.
- 1v1 挑战, 3v3 队伍对战, 出战顺序调整和群排行榜.
- 每日签到, 积分赠送, 商店, 背包, 星经验培养和六星突破.
- 武功, 内功, 轻功洗练, 支持随机更换和三选一.
- 群内两阶段世界 BOSS, 共享血量, 贡献榜和队伍演练.
- 对战文字播报与 GIF 回放, 日榜自动结算及管理员手动结算.

## 安装

| 项目 | 要求 |
| --- | --- |
| AstrBot | `>=4.23.2,<5`, 验证基线为 4.23.2 |
| Python | 验证环境为 3.12 |
| 消息平台 | OneBot v11, AstrBot 适配器标识为 `aiocqhttp` |
| Python 依赖 | 见 [requirements.txt](./requirements.txt) |
| GIF 回放 | 运行 AstrBot 的环境中有可执行的 Chrome 或 Chromium |

在 AstrBot 插件管理中使用以下 GitHub 地址安装:

```text
https://github.com/kkloas/astrbot_plugin_name_fight
```

仓库默认分支已指向插件发布版.需要明确指定分支时使用:

```text
https://github.com/kkloas/astrbot_plugin_name_fight/tree/release-plugin-1-4-1
```

安装后打开插件配置面板, 按需设置管理员名单和 GIF 开关.以下示例使用 `/` 作为命令前缀; 如果 AstrBot 配置了其他唤醒方式, 请按实际设置发送命令.群聊中的 `@玩家` 应使用平台真实的 @ 消息.

GIF 使用随包提供的 `web_animation/` 动画资源, 不需要 Node 或前端构建.可通过环境变量 `NAME_FIGHT_CHROME` 指定浏览器可执行文件.浏览器不可用, 渲染繁忙或超时时会回退文字结果.Cloud 是否能生成 GIF 取决于实际运行环境是否提供浏览器; 可先关闭 `enable_gif` 使用文字对战.

## 新玩家上手

1. 发送 `/create 角色名` 创建角色.
2. 用 `/roster` 查看角色栏, 用 `/use 角色名` 切换出战角色.
3. 用 `/c 对方角色名` 发起 1v1, 对方发送 `/a` 接受.
4. 用 `/signin` 签到, `/wallet` 查看积分, `/shop` 查看道具.
5. 用 `/buy 道具名 数量` 购买道具, `/bag` 查看背包.
6. 用 `/feed 角色名 道具名 [数量]` 培养到 5.0 星, 再用 `/break 角色名` 突破六星.
7. 拥有至少 3 名角色后, 用 `/team3` 查看队伍, `/t3 @玩家` 发起 3v3.

群内可随时发送 `/fhelp` 查看帮助, `/fguide` 查看培养教程, `/bosshelp` 查看 BOSS 说明.

角色名限制为 1 到 32 个可打印字符.角色栏满员时, 创建的新角色进入候选替换流程, 用 `/choose 序号` 确认替换栏位.

## 玩家命令

### 角色与队伍

| 命令 | 用途 |
| --- | --- |
| `/fhelp`, `/fguide`, `/bosshelp` | 命令帮助, 培养教程和 BOSS 帮助 |
| `/create 角色名` | 创建角色 |
| `/choose 序号` | 确认候选角色替换栏位 |
| `/roster` | 查看角色栏 |
| `/use 角色名` | 切换 1v1 出战角色 |
| `/profile [角色名]` | 查看角色卡 |
| `/textprofile [角色名]` | 查看文字档案 |
| `/avatar 角色名` | 设置自己的角色头像, 随命令附图或按提示随后上传 |
| `/team3` | 查看三人队伍 |
| `/teamorder 2 1 3` | 从角色栏选 3 个不同栏位, 按输入顺序出战 |
| `/specialsummon 角色名` | 消耗特殊召唤令创建角色 |

头像只接受真实图片消息, 不接受文本伪造的图片标记.下载来源必须是公网 HTTP/HTTPS 地址或 AstrBot 临时目录中的文件, 并受大小和图片校验限制.

### 对战与排行榜

| 命令 | 用途 |
| --- | --- |
| `/c 对方角色名` | 发起 1v1 挑战 |
| `/a`, `/r` | 接受或拒绝 1v1 挑战 |
| `/t3 @玩家` | 发起 3v3 挑战 |
| `/a3`, `/r3` | 接受或拒绝 3v3 挑战 |
| `/fc 对方角色名` | 无需确认的 1v1 强制对战 |
| `/fc3 @玩家` | 无需确认的 3v3 强制对战 |
| `/rank`, `/rank3` | 查看本群 1v1, 3v3 排行榜 |

正常接受后的挑战发放对战积分.`/fc` 和 `/fc3` 用于娱乐或阵容验证, 不发放积分与道具.同群同时只进行一场战斗, 不同群可分别进行.

### 积分与培养

| 命令 | 用途 |
| --- | --- |
| `/signin` | 每日签到 |
| `/wallet` | 查看积分 |
| `/gift @玩家 数量` | 赠送积分 |
| `/shop`, `/bag` | 查看商店与背包 |
| `/buy 道具名 数量` | 购买道具 |
| `/feed 角色名 道具名 [数量]` | 使用星经验道具 |
| `/break 角色名` | 消耗破境丹, 将 5.0 星角色突破到 6.0 星 |
| `/randommartial 角色名` | 消耗洗髓符随机换武功, 中文别名为 `/随机换武学` |
| `/swapneigong 角色名` | 消耗换宗令换内功, 中文别名为 `/换内功` |
| `/swapqinggong 角色名` | 消耗换宗令换轻功, 中文别名为 `/换轻功` |
| `/swapmartial 角色名` | 消耗换宗令换武功, 中文别名为 `/换武功` |
| `/secttoken 内功或轻功或武功 角色名` | 按指定类型随机更换, 中文别名为 `/换宗令` |
| `/reroll 角色名 初级或中级` | 随机洗武功, 初级消耗洗髓符, 中级消耗换宗令 |
| `/reroll3 角色名` | 消耗天机残卷, 生成 3 个武功候选 |
| `/rerollneigong3 角色名` | 消耗天机残卷, 生成 3 个内功候选 |
| `/rerollqinggong3 角色名` | 消耗天机残卷, 生成 3 个轻功候选 |
| `/choicecroll 武功或内功或轻功 角色名` | 指定类型进行三选一洗练 |
| `/pick 1`, `/pick 2`, `/pick 3` | 确认洗练候选 |

上表中的 "或" 表示任选一个参数, 例如 `/secttoken 内功 张三`, `/reroll 张三 初级`, `/choicecroll 轻功 张三`.三选一也可使用 `/高级洗内功 角色名`, `/高级洗轻功 角色名` 或 `/天机残卷自选 类型 角色名`.

普通创建有 0.3% 概率获得天然六星.低星角色可培养到 5.0 星后突破, 当前上限为 6.0 星.洗练不会清除补星和突破进度.具体道具价格与当前库存以 `/shop` 和 `/bag` 为准.

### 世界 BOSS

| 命令 | 用途 |
| --- | --- |
| `/boss` | 查看本群 BOSS 状态 |
| `/bossfight` | 使用三人队伍挑战 BOSS |
| `/bossquick` | 快速挑战, 仍计入挑战次数与活动进度 |
| `/bossrank` | 查看贡献榜 |
| `/bosssim [phase1或phase2]` | 详细演练, 可指定阶段 |
| `/bosssimquick [phase1或phase2]` | 快速演练, 可指定阶段 |

管理员先开启本群活动.正式挑战需要先通过一阶段, 进入二阶段后的伤害才计入共享血量和贡献榜.默认每人每天可正式挑战 3 次.演练不扣次数, 不写入共享血量.

击杀后的奖励按贡献结算.如果未击杀就关闭活动, 不发击杀参与奖, 管理员仍可结算未击杀版贡献排名奖励.

## 管理员权限与结算

| 命令 | 用途 |
| --- | --- |
| `/bossopen` | 开启本群 BOSS 活动 |
| `/bossclose` | 关闭本群 BOSS 活动 |
| `/bosssettle` | 结算 BOSS 奖励 |
| `/daysettle [1v1或3v3或all]` | 手动结算昨天的日榜 |
| `/weeksettle [1v1或3v3或all]` | 手动结算已结束的上一周 |

例如 `/daysettle all` 或 `/weeksettle 3v3`, 不填榜单时默认 `all`.

以上操作需要管理员权限.`boss_admin_user_ids` 非空时, 只有名单内用户可以操作; 为空时, 允许 AstrBot 管理员或平台消息中可信的 QQ 群管理员, 群主.无法确认身份时拒绝操作.

结算使用 `Asia/Shanghai` 时区.插件运行期间会在每天零点自动结算已记录群的上一日日榜; 周榜由管理员手动结算.停机期间错过的历史周期不提供任意日期补结算.

排行榜是累计 Elo 榜, 奖励按结算时排名计算, 不提供历史排名快照.同群, 同榜, 同周期只发放一次, 奖励, 道具与结算记录在同一事务中提交, 失败整体回滚.

## 插件配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `boss_admin_user_ids` | `[]` | 管理员用户 ID 列表, 非空时优先于平台管理员身份 |
| `broadcast_delay` | `1.6` | 对战消息间隔, 单位秒, 范围 0 到 10 |
| `enable_gif` | `true` | 是否启用 GIF 回放 |
| `render_concurrency` | `1` | GIF 渲染并发上限, 范围 1 到 4 |
| `render_timeout` | `120` | GIF 等待超时, 单位秒, 范围 5 到 300 |
| `avatar_max_mb` | `5` | 头像下载上限, 单位 MiB, 范围 1 到 20 |

GIF 渲染超时后返回文字结果; 后台工作尚未结束时仍占用渲染名额, 防止重复请求持续启动浏览器.

## 存档与更新

玩家存档位于 AstrBot 数据目录中的 `name_fight_data/`:

```text
name_fight_data/
  fighters.db
  avatars/
```

代码更新保留原存档位置.升级前使用 SQLite backup API 备份数据库, 并备份 `avatars/`; 或先停止 AstrBot, 再完整备份该目录.角色卡和 GIF 临时输出写入 AstrBot 临时目录, 发送后清理.

## 分支与版本

| 分支 | 用途 |
| --- | --- |
| `release-plugin-1-4-1` | 当前默认分支, 1.4.1 插件发布线 |
| `dev-web` | Bot/Web 开发线 |
| `archive-bot-baseline-20260922` | 2026-09-22 的旧 Bot 基线 |
| `main` | 保留的旧 Bot/Web 混合代码 |

版本标签 `v1.2.1`, `v1.4.0`, `v1.4.1` 标记各自的固定提交.安装当前插件请使用默认发布分支.更新记录见 [CHANGELOG.md](./CHANGELOG.md).

## 开发与资源许可

从 Git 克隆源码后, 安装运行依赖并运行 `python -m unittest discover`.测试使用临时数据库.真实浏览器回放验证可运行 `python verify_bot_gif.py`, 输出位于 `output/`.

分发 ZIP 使用 `git archive --format=zip --prefix=astrbot_plugin_name_fight/ HEAD` 构建, `.gitattributes` 排除测试与开发资料, 发布包需小于 16 MB.

插件代码采用 [MIT License](./LICENSE).Noto Sans SC 字体使用 SIL Open Font License 1.1, logo 和三张卡图模板已获作者允许随插件分发.资源与字体的独立许可说明见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).
