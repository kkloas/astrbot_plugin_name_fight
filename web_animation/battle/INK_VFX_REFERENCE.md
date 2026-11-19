# 水墨武学动画与特效统一制作标准（V2）

本规范是项目内 **Web 端增强水墨剧场** 与 **Bot 端 20fps GIF 导出** 的统一动画/特效制作与验收标准，适用于后续所有新增武学、翻新旧武学及外部协作参考。

---

## 1. 核心视觉方向与对比度规范

- **墨韵为骨，门派色为魂**：以灰黑淡墨（`rgb(26,31,33)` ~ `rgb(28,34,38)`）、干笔飞白、虚实留白为主体，门派主题色（如降龙琥珀金 `#d97706`、白蟒苍翠玉 `#10b981`、赤霄朱砂红 `#dc2626`、玄墨青霜 `#0ea5e9`）只做点缀、内劲丝缕或锋芒边缘，禁止大面积高饱和荧光块。
- **严禁的视觉伪影**：禁止规则实心尖锥、均匀粗度扁平管线、死板鱼骨折线、贯穿全程的纯色高亮直线。
- **白色毒液/浅色主题物的双向可读性（如《白蟒软鞭》青色鞭影 + 白色毒液）**：凡是设定为乳白色毒液、白蟒或亮白气劲的特效主体，**禁止使用重黑墨块压盖**，也**禁止只用无衬底纯白直接绘制**（在浅色宣纸上会失去边界）。必须采用 **“外层冷青碧色（`#0d9488` / `#14b8a6`）护边与毒雾衬底 + 内部高不透明度乳白/珍珠白（`#f8fafc` / `#ecfeff`）毒液核心与飞溅液滴”**，确保在 `素宣原卷 / 残阳竹林 / 寒江孤雪 / 朱砂血月` 四套画境及 Bot 静态宣纸底图上都呈现清爽的「青鞭白毒」质感。

---

## 2. 素材生成与无损去背标准管线

### 2.1 纯白底水墨去背（`white-to-alpha`）与纯黑底亮色/白色毒液去背（`black-to-alpha`）
1. **原始素材要求**：
   - **传统水墨/重墨类（如降龙、刀剑裂地）**：使用生图工具生成严格 **纯白底（`#FFFFFF`）** 特效图。
   - **白色毒液/亮色能量类（如白蟒软鞭的乳白毒液巨蟒与青鞭白毒弧光）**：使用生图工具生成严格 **纯黑底（`#000000`）** 特效图（若用白底去背会把白色毒液当成背景抠空；纯黑底才能保留高不透明度的乳白毒液与青碧流光）。
   - 所有原图禁带杂景、人物、文字与印章，四周保留充足纯色边距，统一留档在 `web_animation/battle/assets/raw/`。
2. **无损 Alpha 剥离**：运行本地管线脚本 [tools/ink_asset_pipeline.py](file:///D:/NFIGHTPLUS/tools/ink_asset_pipeline.py)：
   ```powershell
   # 纯白底水墨类 -> 透明 RGBA
   py -3.10 tools/ink_asset_pipeline.py white-to-alpha <raw_white.png> <output_rgba.png> --max-width 1800

   # 纯黑底白色毒液/亮色气劲类 -> 透明 RGBA（保留乳白核心并锚定 #0d9488 青碧外廓）
   py -3.10 tools/ink_asset_pipeline.py black-to-alpha <raw_black.png> <output_rgba.png> --black-threshold 14 --gamma 0.90 --max-width 1800
   ```
   - `white-to-alpha` 按通道反相提取连续 Alpha 并剥离白底残色；`black-to-alpha` 按亮度提取不透明乳白毒液核心，同时将中暗部过渡边缘锚定为高对比青碧色（`#0d9488`），避免白色毒液在浅色宣纸上发白消失，且在暗底上无任何黑边。
   - 自动裁剪多余透明区并统一补齐 `32px` 透明边距。
3. **可选：图生视频序列帧打包**：若某招式升级为固定机位视频短片（FFmpeg 按 12~16 FPS 抽帧），可用同一工具合成横向雪碧图带：
   ```powershell
   py -3.10 tools/ink_asset_pipeline.py pack-sheet <frames_dir> <sheet.png> --mode white --frame-width 480
   ```
   （黑底发光层用 `--mode black`，在运行时可配合 `ctx.globalCompositeOperation = 'lighter'` 叠加）。

---

## 3. Canvas 绘制原语与防伪影规范

- **条带切片波动（`drawStripSlicedImage`，见 [xianglongArts.js](file:///D:/NFIGHTPLUS/web_animation/battle/xianglongArts.js)）**：
  - 对单张水墨长图（如《亢龙有悔》游龙、《绝技·白蟒索命》白蟒、`ink-whip-sweep.png` 挥鞭墨浪），将图像纵向切分为多条带并按绝对时间做正弦波浪偏移。
  - **严禁切片重叠（overlap）**：半透明水墨条带若重叠哪怕 `0.75px`，叠加处就会出现明显的黑色竖条纹网格！必须使用严丝合缝的连续边界 `u0 -> u1`（零重叠）绘制。
  - **刚体头部保护（`rigidFrom`）**：龙首、蟒首等精密五官结构区域（如 `u >= 0.62`）不得被切片上下错位，必须通过 `rigidFrom` 作为一整块连续贴图直接锚定绘制，仅对躯干/尾部做波动。
  - **柔性渐进显现（`featherRight`）**：地面裂痕或冲击波向前推进时，禁止用生硬的 `ctx.rect().clip()` 切出一道垂直刀切边，应通过 `featherRight`（如 `0.20~0.24`）对推进前沿做透明羽化渐变。
- **程序化毛笔笔触（`brushPoly`）**：所有程序线条、剑气、鞭影、气浪统一使用两端出锋的 `brushPoly` 变宽多边形与飞白断笔，不再使用等宽 `ctx.lineWidth = 30` 的硬边管线。

---

## 4. 三层舞台架构与四段打击感节奏

- **严格三层绘制顺序（见 [InkStage.js](file:///D:/NFIGHTPLUS/web_animation/battle/InkStage.js)）**：
  1. **底层**：动态画境 / 地面战斗墨渍 / 脚底影圈 / 阵法裂地光环
  2. **中层**：多姿态残影 / 11 点固定骨长 IK 人物 / 飘带 / 兵刃与软鞭本体
  3. **顶层**：招式水墨贴图与游龙大招 / 命中溅墨与冲击波 / 浮动伤害字与篆印 / 前景风动飘叶雪星
- **四段发力节奏（以标准单回合 `0~1740ms`、命中点 `950ms` 为基准）**：
  1. **蓄力前摇（慢）**：前约 30% 时长（`0~600ms`），沉胯拉肘收肩，配合聚气粒子与脚下气环；
  2. **爆发推进（脆）**：使用高次方缓出曲线（如 `snap(t, 600, 185, 3.2)`）在极短窗口内甩出全身动作与招式主贴图；
  3. **命中顿帧（重）**：命中时通过 `contactTime()` 触发 **48~88ms** 人物顿帧定格，同时粒子飞溅、墨浪翻涌与震屏持续推进；
  4. **收招余韵（稳）**：`1160~1740ms` 自然缓冲回位，墨迹逐渐消散。
- **篆印开关与命中红线**：
  - 4 套新武学（`sword_xuanmo`、`blade_chixiao`、`palm_xianglong`、`whip_baimang`）的绝技方形文字印章（「霜寒」「断魂」「亢龙」「白蟒」）绘制函数均完整保留在各自模块中，当前统一通过模块顶部的 `const SHOW_ULTIMATE_SEALS = false;` **默认隐藏**；后续若需恢复或做配置化展示，只需将该布尔开关改回 `true`。
  - **闪避（`hit === false`）时严禁绘制命中爆点、碎石溅墨、毒液炸裂与绝技印章**，招式轨迹应自然穿过目标原站位。

---

## 5. 双端同源、Bot/Web 特效对齐与确定性红线

- **绝对确定性**：所有动作与特效必须是绝对回放时间 `time` 的纯函数，**禁止 `Math.random()`、`Date.now()` 或帧间累加器**；需要随机感一律使用确定性哈希 `seed(n)`，确保暂停、0.25x 慢放、任意拖动进度条 100% 可复现。
- **Bot 端与 Web 端招式特效对齐架构（`{ webEnhanced: true, sceneTheme: 'classic', battleStains: false }`）**：
  - **为什么早先 Bot 与 Web 特效不一致**：并非 Canvas 绘制招式贴图的性能瓶颈，而是因为 **GIF 帧间差分压缩对全屏动态背景极度敏感**（一旦绘制全屏动态渐变、飘落竹叶/风雪或持续累积的地面残迹，GIF 每一帧的大面积像素都在变化，文件体积会暴涨数倍），而旧逻辑把「全屏动态风景」和「招式级 PNG 贴图/切片特效」绑在了同一个 `webEnhanced` 开关上；此外无头导出时 `document.images` 不会自动等待 JS `new Image()` 异步贴图解码。
  - **现在的解耦对齐方案**：
    1. 在 [InkStage.js](file:///D:/NFIGHTPLUS/web_animation/battle/InkStage.js) 中将「招式特效增强（`webEnhanced: true`）」与「画境背景（`sceneTheme`）/地面残迹（`battleStains`）」解耦；
    2. 在 [capture.js](file:///D:/NFIGHTPLUS/web_animation/capture.js) 中传入 `{ webEnhanced: true, sceneTheme: 'classic', battleStains: false }`，并在 `prepareExport()` 中 `await waitForBattleAssets()` 等待全部招式 PNG 贴图预解码完毕；
    3. 这样 Bot 端**既拥有与 Web 端 100% 对齐的招式贴图、22~30 条带正弦波浪游动、多姿态残影与高分段软鞭特效**，又**保持纯静态 `ink-bg.png` 宣纸背景（零 `createLinearGradient`、零全屏动态噪点）**，兼顾满配特效表现与轻量 GIF 体积。
  - 当显式传入 `webEnhanced === false` 或极端离线环境下贴图未就绪时，仍保留高对比度的纯 Canvas 程序化主视觉回退。
- **表现不改规则**：残影、多段连挥与特效粒子均为纯视觉表现，不产生额外攻击或状态事件。

---

## 6. 本地标杆案例与验证工作流

- **推荐对照源码**：
  - **《降龙十八掌》（`palm_xianglong`）**：[xianglongArts.js](file:///D:/NFIGHTPLUS/web_animation/battle/xianglongArts.js) — 完整的「纯白底去背 + 四段脆快节奏 + 条带波浪游龙 + 羽化震地裂纹 + Bot 程序墨龙回退」标杆实现。
  - **《白蟒软鞭》（`whip_baimang`）**：[serpentMotion.js](file:///D:/NFIGHTPLUS/web_animation/battle/serpentMotion.js) — 复用 `drawStripSlicedImage` 与 `brushPoly` 改造旧武学的标杆（重墨白蟒首+游动躯干+鞭梢扫浪贴图，并保持软鞭收招连续性）。
  - **《玄墨剑典》/《赤霄断魂刀》**：[wuxiaMasterArts.js](file:///D:/NFIGHTPLUS/web_animation/battle/wuxiaMasterArts.js) — 兵器挥斩丝带、多姿态残影与太极阵法标杆。
- **本地交互预览**：
  ```powershell
  python tools/local_preview_server.py --port 0
  ```
  同时展示 **Web 增强特效** 与 **Bot 素底对照** 双画布，支持 `0.25x~2x` 变速、毫秒级拖动、四套画境与左右镜像检查。
- **提交前必跑检查**：
  - `node test_master_arts.mjs`、`node test_serpent_motion.mjs`、`node test_inner_light_effects.mjs`、`node test_battle_effects.mjs`
  - `python -m unittest test_new_martial_arts test_shared_release test_battle_visuals test_battle_events test_action_gauge -q`
  - `cd web/frontend && npm run build`
