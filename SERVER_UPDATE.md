# Web 和 AstrBot 服务器更新指南

本指南适用于本仓库的 Web 端和 AstrBot 插件端。服务器整合版本以 `main` 为发布基线，`dev-web` 作为上游开发来源；更新必须先遵循 [UPDATE_POLICY.md](UPDATE_POLICY.md) 并在隔离分支整合验证，不能直接用 `dev-web` 覆盖服务器功能。 服务器路径, 服务名称, 反向代理和 Python 环境以实际部署为准.

## 本次更新内容

- 新增玄墨剑典, 赤霄断魂刀及配套内功和轻功, 以及 Web 演武和逐招拆解页面.
- 更新共享动作和 Web 专属水墨素材及特效, 包括白蟒软鞭. Bot GIF 使用共享动画模块, Web 专属增强效果不会自动使 Bot 画面与 Web 完全一致.
- 包含相关战斗配置和测试. `dev-web` 也包含之前已在提交 `2472de4` 中发布的 Web 和 PVE 更新.
- 动画源素材在 `web_animation/battle/assets/`. `web/frontend/dist/` 是服务器上生成的前端构建产物, Git 不跟踪该目录.

## 1. 确认安装位置并备份

1. 确认实际仓库目录, AstrBot 插件安装目录, Web 后端和前端发布位置, 以及各自使用的 Python 环境和服务名称. 如果 Web 和插件使用不同的仓库副本, 需要分别更新和验证.
2. 更新前备份数据库, 头像, 服务器配置及其他自有数据, 备份放在 Git 仓库目录之外. 使用 SQLite 一致性备份, 或先停止所有写入数据库的进程再复制.
3. 默认数据库位于仓库内的 `name_fight_data/fighters.db`. 如果仓库直接位于 AstrBot 的 `plugins` 目录下, 默认数据目录则位于 `plugins` 同级. 实际备份前请确认服务器上的数据库位置及自定义配置.
4. 在每个仓库副本中记录当前状态:

```sh
git status --short --branch
git rev-parse HEAD
git remote -v
```

如果存在本地修改, 可能冲突的未跟踪文件, 意外的远端地址或不清楚的部署布局, 应先保存并核实, 再切换分支或拉取. 不要将 `git reset --hard` 或 `git clean` 当成常规更新步骤.

## 2. 对比 GitHub 并更新仓库

在实际仓库目录执行:

```sh
git fetch origin
git log --oneline --left-right HEAD...origin/main
git diff --stat HEAD origin/main
git status --short --branch
```

先检查差异. 如果服务器已有本地 `main` 分支, 并确认工作区可以安全切换, 执行:

```sh
git switch main
git pull --ff-only origin main
git rev-parse HEAD
```

如果没有本地 `main` 分支, 且获取后存在 `origin/main`, 可先执行 `git switch --track origin/main`, 再执行上面的 `git pull --ff-only` 和版本检查. 如果切换或快进拉取失败, 停下来检查本地修改和分支历史, 不要强行覆盖. Web 和插件使用不同仓库副本时, 每份都需单独对比.

## 3. 更新 Web 端

- 使用现有后端 Python 环境, 按需安装 `web/backend/requirements.txt` 中的依赖. 仓库提供的后端启动器会优先检查 `web/.python-packages`, 请先确认运行中的服务实际使用哪套环境.
- 在 Web 仓库中使用 Node 和 npm 构建前端:

```sh
cd web/frontend
npm ci
npm run build
```

- 按服务器现有方式发布 `web/frontend/dist/`, 并按实际部署方式重启 Web 后端及前端服务. 不要猜测服务名称. 生产环境要继续将 `/api` 请求代理到后端.
- 打开 Web 应用及 `/motion-preview.html`, 检查新武学和白蟒软鞭的 Web 增强特效. 发布后如页面仍显示旧内容, 按现有部署方式刷新浏览器或处理缓存.

## 4. 更新 AstrBot 插件端

- 确认第 2 步已更新实际的插件仓库, 并确认 AstrBot 使用的 Python 环境已安装仓库根目录 `requirements.txt` 的依赖. 保留现有环境和服务器配置.
- Bot GIF 渲染器从插件仓库加载 `web_animation`, 需要兼容的 Chrome 或 Chromium. 如有需要, 可用 `NAME_FIGHT_CHROME` 指定浏览器可执行文件.
- 按服务器现有方式重启实际的 AstrBot 服务, 然后进行一次不破坏数据的测试对战, 检查 GIF 与服务日志. Web 专属增强特效不保证在 Bot GIF 中呈现相同画面.

## 5. 验证和回退

- 在各仓库执行 `git rev-parse HEAD`, 检查 Web 前后端, 分别测试一次 Web 对战和 Bot 对战, 并查看服务日志.
- 如更新或验证失败, 暂停后续操作, 保留数据库备份和此前记录的版本号. 按服务器既有回退流程恢复旧版本. 只有确实需要时才恢复数据库, 并先停止所有数据库写入进程. 强制切换或重置可能丢失本地工作, 选择回退命令前必须先检查服务器状态.
