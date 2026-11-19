# -*- coding: utf-8 -*-
"""Standalone local developer server for interactive animation preview."""

from __future__ import annotations

import argparse
import http.server
import socket
import socketserver
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
WEB_ANIMATION_DIR = ROOT / "web_animation"

PREVIEW_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>降龙十八掌 · 本地交互预览台</title>
  <style>
    @font-face { font-family: STKaiti; src: url('/STKAITI.TTF') format('truetype'); }
    @font-face { font-family: STXingkai; src: url('/STXINGKA.TTF') format('truetype'); }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 18px 22px 28px;
      background: #efeadf;
      color: #252822;
      font-family: STKaiti, KaiTi, "Microsoft YaHei", serif;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 12px;
      max-width: 1120px;
      margin: 0 auto 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid #bdb7a7;
    }
    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      color: #231e17;
      letter-spacing: 1px;
    }
    .subtitle {
      font-size: 14px;
      color: #6b5e4c;
    }
    .controls {
      max-width: 1120px;
      margin: 0 auto 14px;
      padding: 12px 14px;
      background: rgba(250, 247, 239, 0.92);
      border: 1px solid #c3bca9;
      border-radius: 6px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 16px;
      font-size: 15px;
    }
    label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    select, button {
      font-family: inherit;
      font-size: 14px;
      padding: 4px 10px;
      border: 1px solid #9e9684;
      border-radius: 4px;
      background: #faf8f2;
      color: #252822;
      cursor: pointer;
    }
    button:hover {
      background: #ede6d6;
    }
    .timeline {
      max-width: 1120px;
      margin: 0 auto 16px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .timeline input[type="range"] {
      flex: 1;
      accent-color: #b45309;
      cursor: pointer;
    }
    .timeline output {
      min-width: 72px;
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: #5c4f3d;
    }
    .stages {
      max-width: 1120px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }
    .stage-card {
      background: #faf8f2;
      border: 1px solid #b5ae9c;
      border-radius: 6px;
      padding: 10px 12px 12px;
    }
    .stage-card h2 {
      margin: 0 0 8px;
      font-size: 16px;
      color: #3d352a;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .stage-card h2 span {
      font-size: 13px;
      font-weight: normal;
      color: #7c6f5c;
    }
    .canvas-wrap {
      width: 100%;
      border: 1px solid #c9c3b4;
      overflow: hidden;
      background: #f5f1e6;
    }
    .canvas-wrap.bot {
      background: linear-gradient(rgba(250, 250, 245, 0.48), rgba(247, 248, 243, 0.08)), url('/ink-bg.png') center/100% 100% no-repeat;
    }
    .canvas-wrap.web-sunset { background: linear-gradient(180deg, #efe5d5 0%, #f6f1e6 100%); }
    .canvas-wrap.web-snow { background: linear-gradient(180deg, #dfe9f1 0%, #eff4f8 100%); }
    .canvas-wrap.web-bloodmoon { background: linear-gradient(180deg, #2a181b 0%, #3d2426 100%); }
    .canvas-wrap.web-classic { background: #f5f2e8; }
    canvas {
      display: block;
      width: 100%;
      height: auto;
      aspect-ratio: 1000 / 430;
    }
  </style>
</head>
<body>
  <header>
    <h1>丐帮宗师套装 · 本地水墨动画拆解台</h1>
    <div class="subtitle">降龙十八掌 + 擒龙混元功 + 游龙踏步（双端同源实时渲染）</div>
  </header>

  <div class="controls">
    <label>招式
      <select id="move-select" aria-label="招式"></select>
    </label>
    <label>画境
      <select id="theme-select" aria-label="画境">
        <option value="sunset" selected>残阳竹林</option>
        <option value="snow">寒江孤雪</option>
        <option value="bloodmoon">朱砂血月</option>
        <option value="classic">素宣原卷</option>
      </select>
    </label>
    <label>出招方
      <select id="side-select" aria-label="出招方">
        <option value="a" selected>左方</option>
        <option value="b">右方</option>
      </select>
    </label>
    <label><input type="checkbox" id="missed-check"> 闪避</label>
    <label><input type="checkbox" id="inner-check" checked> 擒龙混元功</label>
    <label><input type="checkbox" id="light-check" checked> 游龙踏步</label>
    <label><input type="checkbox" id="loop-check" checked> 循环播放</label>
    <button id="play-btn" type="button">暂停</button>
    <button id="replay-btn" type="button">重播</button>
    <label>倍速
      <select id="speed-select" aria-label="倍速">
        <option value="0.25">0.25x</option>
        <option value="0.5">0.5x</option>
        <option value="1" selected>1x</option>
        <option value="2">2x</option>
      </select>
    </label>
  </div>

  <div class="timeline">
    <input id="scrubber" type="range" min="0" max="2400" step="1" value="0" aria-label="动作进度">
    <output id="time-out">0 ms</output>
  </div>

  <div class="stages">
    <section class="stage-card">
      <h2>Web 增强特效 <span id="active-label"></span></h2>
      <div id="wrap-web" class="canvas-wrap web-sunset">
        <canvas id="canvas-web" width="1000" height="430"></canvas>
      </div>
    </section>
    <section class="stage-card">
      <h2>Bot 宣纸对齐模式（无头 Chrome GIF 实际输出）<span>静态宣纸底图 + 与 Web 对齐的完整招式贴图特效，不含动态背景以保住 GIF 体积</span></h2>
      <div class="canvas-wrap bot">
        <canvas id="canvas-bot" width="1000" height="430"></canvas>
      </div>
    </section>
  </div>

  <script type="module">
    import { draw } from '/battle/InkStage.js';
    import { masterMoves, masterMoveFor } from '/battle/wuxiaMasterArts.js';
    import { expandedMoves, expandedMoveFor } from '/battle/expandedArts.js';

    const DURATION = 2400;
    const orderedMoves = [
      ...masterMoves.filter((m) => m.id === 'palm_xianglong'),
      ...expandedMoves.filter((m) => m.id === 'whip_baimang'),
      ...masterMoves.filter((m) => m.id !== 'palm_xianglong'),
    ];

    const moveSelect = document.getElementById('move-select');
    orderedMoves.forEach((item, idx) => {
      const opt = document.createElement('option');
      opt.value = String(idx);
      opt.textContent = `${item.name} / ${item.move}`;
      moveSelect.appendChild(opt);
    });
    const qs = new URLSearchParams(location.search);
    const qArt = qs.get('art');
    const qMove = qs.get('move');
    let defaultIdx = orderedMoves.findIndex((m) => (!qArt || m.id === qArt) && (!qMove || m.move === qMove));
    if (defaultIdx < 0 && qArt) defaultIdx = orderedMoves.findIndex((m) => m.id === qArt);
    if (defaultIdx < 0) defaultIdx = orderedMoves.findIndex((m) => m.id === 'palm_xianglong' && m.move === '绝技·亢龙有悔');
    moveSelect.value = String(Math.max(0, defaultIdx));

    const themeSelect = document.getElementById('theme-select');
    const sideSelect = document.getElementById('side-select');
    const missedCheck = document.getElementById('missed-check');
    const innerCheck = document.getElementById('inner-check');
    const lightCheck = document.getElementById('light-check');
    const loopCheck = document.getElementById('loop-check');
    const playBtn = document.getElementById('play-btn');
    const replayBtn = document.getElementById('replay-btn');
    const speedSelect = document.getElementById('speed-select');
    const scrubber = document.getElementById('scrubber');
    const timeOut = document.getElementById('time-out');
    const wrapWeb = document.getElementById('wrap-web');
    const activeLabel = document.getElementById('active-label');

    const ctxWeb = document.getElementById('canvas-web').getContext('2d');
    const ctxBot = document.getElementById('canvas-bot').getContext('2d');

    const preload = Promise.all(
      ['dragon-surge', 'palm-burst', 'ground-quake', 'crescent', 'fissure', 'python-wash', 'whip-sweep'].map(
        (n) => new Promise((res) => {
          const im = new Image();
          im.onload = im.onerror = () => res();
          im.src = `/battle/assets/ink-${n}.png`;
        }),
      ),
    );

    const state = {
      time: 0,
      playing: true,
      speed: 1,
      lastStamp: null,
    };

    function buildBattle() {
      const art = orderedMoves[Number(moveSelect.value)] || orderedMoves[0];
      const side = sideSelect.value === 'b' ? 'b' : 'a';
      const target = side === 'a' ? 'b' : 'a';
      const master = masterMoveFor({ martialArtId: art.id, move: art.move });
      const exp = expandedMoveFor({ martialArtId: art.id, move: art.move });
      const damage = master ? (master.ultimate ? 380 : Math.round(185 * master.power)) : exp ? (exp.ultimate ? 360 : Math.round(180 * exp.power)) : 200;
      const missed = missedCheck.checked;

      const actor = {
        name: art.id === 'palm_xianglong' ? '洪七公' : art.name,
        stats: { hp: 1000, spd: 60 },
        currentHp: 1000,
        martialArt: { id: art.id, name: art.name, type: art.type },
        neigong: innerCheck.checked ? { id: 'xianglong_hunyuan_gong', name: '擒龙混元功' } : { id: '', name: '' },
        qinggong: lightCheck.checked ? { id: 'youlong_tabu', name: '游龙踏步' } : { id: '', name: '' },
      };
      const opponent = {
        name: '试招对手',
        stats: { hp: 1000, spd: 55 },
        currentHp: 1000,
        martialArt: {
          id: art.id === 'sword_xuanmo' ? 'blade_chixiao' : 'sword_xuanmo',
          name: art.id === 'sword_xuanmo' ? '赤霄断魂刀' : '玄墨剑典',
          type: art.id === 'sword_xuanmo' ? 'blade' : 'sword',
        },
        neigong: { id: 'taiji_xuanmo_gong', name: '太极玄墨功' },
        qinggong: { id: 'taxue_wuhen', name: '踏雪无痕' },
      };

      const events = [{ type: 'battle_start', time: 0 }];
      if (innerCheck.checked) {
        events.push({
          type: 'status_apply',
          time: 220,
          action: 1,
          actor: side,
          target: side,
          status: 'crisis_defense',
          effect: 'crisis_defense',
          duration: 9999,
          sourceSkill: { category: 'neigong', id: 'xianglong_hunyuan_gong', name: '擒龙混元功' },
        });
      }
      if (lightCheck.checked) {
        events.push({
          type: 'passive_trigger',
          time: 280,
          action: 1,
          actor: side,
          target: side,
          effect: 'dodge_damage_boost',
          status: 'next_attack_bonus',
          sourceSkill: { category: 'qinggong', id: 'youlong_tabu', name: '游龙踏步' },
        });
      }
      events.push(
        { type: 'turn_start', time: 200, action: 1, actor: side },
        { type: 'attack', time: 750, action: 1, actor: side, target, martialArtId: art.id, move: art.move, weaponType: art.type, moveIndex: 7 },
        missed
          ? { type: 'dodge', time: 1150, action: 1, actor: side, target }
          : {
              type: 'damage',
              time: 1150,
              action: 1,
              actor: side,
              target,
              cause: 'strike',
              amount: damage,
              hpAfter: 1000 - damage,
              maxHp: 1000,
              crit: Boolean(master?.ultimate || exp?.ultimate),
              bodyPartKey: 'chest',
            },
        { type: 'turn_end', time: 1950, action: 1 },
        { type: 'battle_end', time: 2600 },
      );
      events.sort((a, b) => a.time - b.time);

      activeLabel.textContent = `${art.name} · ${art.move}`;
      return {
        attacker: side === 'a' ? actor : opponent,
        defender: side === 'b' ? actor : opponent,
        winner: null,
        events,
      };
    }

    let currentBattle = buildBattle();

    function refreshBattle() {
      currentBattle = buildBattle();
      wrapWeb.className = `canvas-wrap web-${themeSelect.value}`;
      render();
    }

    function render() {
      const theme = themeSelect.value;
      draw(ctxWeb, currentBattle, state.time, 1000, false, true, 'current', { webEnhanced: true, sceneTheme: theme });
      draw(ctxBot, currentBattle, state.time, 1000, false, true, 'current', { webEnhanced: true, sceneTheme: 'classic', battleStains: false });
      scrubber.value = String(Math.round(state.time));
      timeOut.textContent = `${Math.round(state.time)} ms`;
    }

    function tick(stamp) {
      if (state.lastStamp !== null && state.playing) {
        const dt = Math.min(80, Math.max(0, stamp - state.lastStamp)) * state.speed;
        state.time += dt;
        if (state.time >= DURATION) {
          if (loopCheck.checked) {
            state.time = 0;
          } else {
            state.time = DURATION;
            state.playing = false;
            playBtn.textContent = '播放';
          }
        }
        render();
      }
      state.lastStamp = stamp;
      requestAnimationFrame(tick);
    }

    [moveSelect, themeSelect, sideSelect, missedCheck, innerCheck, lightCheck].forEach((el) => {
      el.addEventListener('change', refreshBattle);
    });
    speedSelect.addEventListener('change', () => {
      state.speed = Number(speedSelect.value) || 1;
    });
    playBtn.addEventListener('click', () => {
      if (!state.playing && state.time >= DURATION) state.time = 0;
      state.playing = !state.playing;
      playBtn.textContent = state.playing ? '暂停' : '播放';
    });
    replayBtn.addEventListener('click', () => {
      state.time = 0;
      state.playing = true;
      playBtn.textContent = '暂停';
      render();
    });
    scrubber.addEventListener('input', () => {
      state.time = Number(scrubber.value) || 0;
      state.playing = false;
      playBtn.textContent = '播放';
      render();
    });

    await Promise.all([document.fonts.ready, preload]);
    refreshBattle();
    document.body.dataset.ready = '1';
    requestAnimationFrame(tick);
  </script>
</body>
</html>
"""


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ttf": "font/ttf",
        ".TTF": "font/ttf",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ANIMATION_DIR), **kwargs)

    def do_GET(self):
        if urlsplit(self.path).path in ("/", "/preview.html", "/index"):
            data = PREVIEW_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def log_message(self, format, *args):
        pass


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local standalone animation preview server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()

    with ThreadingServer((args.host, args.port), PreviewHandler) as httpd:
        print(f"Preview server listening on http://{args.host}:{httpd.server_address[1]}/", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
