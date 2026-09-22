const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../..');
const base = process.env.NAME_FIGHT_WEB_URL || 'http://127.0.0.1:5173';
const output = path.join(root, 'output/playwright/shared-runtime');

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1500, height: 960 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(base + '/motion-preview.html?art=staff_bainiaochaofeng');
    await page.getByRole('button', { name: '暂停', exact: true }).click();
    const arts = JSON.parse(fs.readFileSync(path.join(root, 'configs/martial_arts.json'), 'utf8'));
    assert.equal(await page.getByLabel('招式', { exact: true }).locator('option').count(), 126);
    const metrics = await page.evaluate(async ({ arts, runtime }) => {
      const web = await import('/src/battle/InkStage.tsx');
      const source = await (await fetch('/src/battle/InkStage.tsx')).text();
      const imported = source.match(/from "([^"]+web_animation\/battle\/InkStage\.js[^"]*)"/)?.[1];
      if (!imported?.startsWith(runtime + '/InkStage.js')) throw Error('Not using Bot runtime');
      const bot = await import(imported);
      const { stateAt } = await import(runtime + '/replay.js');
      const { techniques, weaponFor } = await import(runtime + '/martialVisuals.js');
      const { expandedMoveFor, expandedArts } = await import(runtime + '/expandedArts.js');
      if (web.draw !== bot.draw || web.poseAt !== bot.poseAt) throw Error('Runtime fork');
      let frames = 0, boneError = 0, nonblank = 0;
      const signatures = new Set(), shots = [];
      const canvas = document.createElement('canvas');
      canvas.width = 1000; canvas.height = 430;
      const ctx = canvas.getContext('2d');
      const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
      for (const art of arts) for (const move of art.moves) {
        if (!techniques[art.id]?.[move.name]) throw Error('Unmapped: ' + art.id + '/' + move.name);
        const signature = [];
        for (const side of ['a', 'b']) for (const miss of [false, true]) {
          const target = side === 'a' ? 'b' : 'a';
          const actor = { name: art.name, stats: { hp: 1000, spd: 60 }, martialArt: art };
          const turn = { type: 'turn_start', time: 300, action: 1, actor: side };
          const attack = { type: 'attack', time: 850, action: 1, actor: side, target, martialArtId: art.id, move: move.name, weaponType: art.type };
          const battle = { attacker: actor, defender: actor, winner: null, events: [
            { type: 'battle_start', time: 0 }, turn, attack,
            miss ? { type: 'dodge', time: 1250, action: 1, actor: side, target } :
              { type: 'damage', time: 1250, action: 1, actor: side, target, cause: 'strike', amount: 320, hpBefore: 1000, hpAfter: 680, maxHp: 1000 },
            { type: 'turn_end', time: 2100, action: 1 }, { type: 'battle_end', time: 2500 },
          ] };
          for (const time of [300, 780, 990, 1120, 1250, 1410, 1800]) {
            const frame = web.poseAt(battle, side, time, 1000, stateAt(battle, time).turn, 'current');
            const p = frame.pose.points, s = frame.pose.shoulders;
            const measurements = [[p[0], p[1], 21], [p[1], p[2], 52], [s[0], p[3], 40], [p[3], p[4], 40],
              [s[1], p[5], 40], [p[5], p[6], 40], [p[2], p[7], 48], [p[7], p[8], 48], [p[2], p[9], 48], [p[9], p[10], 48]];
            for (const [a, b, length] of measurements) {
              const error = Math.abs(dist(a, b) - length);
              if (!Number.isFinite(error)) throw Error('Nonfinite pose: ' + move.name);
              boneError = Math.max(boneError, error);
            }
            web.draw(ctx, battle, time, 1000, false, true, 'current');
            const pixels = ctx.getImageData(0, 0, 1000, 430).data;
            let count = 0; for (let i = 3; i < pixels.length; i += 4) if (pixels[i]) count++;
            if (count < 1000) throw Error('Blank frame: ' + move.name);
            nonblank++; frames++;
            if (side === 'a' && !miss && expandedMoveFor(attack)) signature.push(frame);
            if (side === 'a' && !miss && time === 1250 && expandedMoveFor(attack)?.ultimate)
              shots.push({ title: art.name + ' / ' + move.name, image: canvas.toDataURL() });
          }
          if (weaponFor(actor) !== (expandedArts[art.id]?.weapon || weaponFor(actor))) throw Error('Wrong weapon');
        }
        if (signature.length) signatures.add(JSON.stringify(signature));
      }
      window.__shots = shots;
      return { frames, boneError, nonblank, distinctNewMoves: signatures.size };
    }, { arts, runtime: '/@fs/' + root.replaceAll('\\', '/') + '/web_animation/battle' });
    assert.ok(metrics.boneError < 1e-6, JSON.stringify(metrics));
    assert.equal(metrics.distinctNewMoves, 40);
    assert.deepEqual(errors, []);
    await page.getByLabel('动作进度').fill('1250');
    await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.setViewportSize({ width: 1100, height: 2300 });
    await page.evaluate(() => {
      const main = document.createElement('main');
      main.style.cssText = 'background:#eeeae0;padding:20px;color:#222';
      for (const shot of window.__shots) {
        const h = document.createElement('h2'); h.textContent = shot.title;
        const img = document.createElement('img'); img.src = shot.image; img.style.width = '100%';
        main.append(h, img);
      }
      document.body.replaceChildren(main);
    });
    await page.screenshot({ path: path.join(output, 'new-ultimates.png'), fullPage: true });
    console.log(JSON.stringify(metrics));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
