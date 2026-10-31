// Run with: node test_master_arts.mjs
import assert from 'node:assert/strict';
import { draw, poseAt } from './web_animation/battle/InkStage.js';
import { masterArts } from './web_animation/battle/wuxiaMasterArts.js';

function context() {
    const calls = [];
    const ctx = new Proxy({ globalAlpha: 1, globalCompositeOperation: 'source-over' }, {
        get(o, k) {
            if (k in o) return o[k];
            return (...args) => {
                for (const n of args) if (typeof n === 'number') assert.ok(Number.isFinite(n), `${String(k)} got ${n}`);
                calls.push([k, ...args]);
                if (k === 'measureText') return { width: 30 };
                if (String(k).startsWith('create')) return { addColorStop() {} };
            };
        },
        set(o, k, v) { if (typeof v === 'number') assert.ok(Number.isFinite(v), String(k)); o[k] = v; return true; },
    });
    return { ctx, calls };
}
const fighter = (art) => ({ name: art.name, stats: { hp: 1000, spd: 60 }, martialArt: { id: art.id, name: art.name, type: art.type } });
let frames = 0;
for (const [id, art] of Object.entries(masterArts)) {
    for (const [index, move] of art.moves.entries()) {
        for (const missed of [false, true]) {
            const battle = {
                attacker: fighter({ id, ...art }), defender: fighter({ id: 'palm_crushing_wave', name: '碎浪掌', type: 'palm' }), winner: null,
                events: [
                    { type: 'battle_start', time: 0 },
                    { type: 'turn_start', time: 0, action: 1, actor: 'a' },
                    { type: 'attack', time: 550, action: 1, actor: 'a', target: 'b', martialArtId: id, move: move.name, weaponType: art.type, moveIndex: index },
                    missed ? { type: 'dodge', time: 950, action: 1, actor: 'a', target: 'b' }
                        : { type: 'damage', time: 950, action: 1, actor: 'a', target: 'b', cause: 'strike', amount: 200, hpAfter: 800, maxHp: 1000, bodyPartKey: 'chest' },
                    { type: 'turn_end', time: 1600, action: 1 },
                    { type: 'battle_end', time: 2000 },
                ],
            };
            const before = JSON.stringify(battle);
            for (let t = 0; t <= 2000; t += 40) {
                for (const options of [undefined, { webEnhanced: true, sceneTheme: 'snow' }, { webEnhanced: true, sceneTheme: 'bloodmoon' }]) {
                    const a = context(), b = context();
                    draw(a.ctx, battle, t, 1000, false, true, 'mixed', options);
                    draw(b.ctx, battle, t, 1000, false, true, 'mixed', options);
                    assert.deepEqual(a.calls, b.calls, `${move.name} t=${t} must be deterministic`);
                    frames++;
                }
            }
            // Bot path (no options) must not paint the Web-only scenery gradient.
            const bot = context();
            draw(bot.ctx, battle, 1000, 1000, false, true, 'mixed');
            assert.ok(!bot.calls.some((c) => c[0] === 'createLinearGradient'), 'Bot render must stay on the static background');
            assert.equal(JSON.stringify(battle), before);
            const frame = poseAt(battle, 'a', 800, 1000, battle.events[1]);
            assert.ok(frame.pose.points.every((p) => p.every(Number.isFinite)));
        }
    }
}
console.log(`Master arts: ${frames} deterministic frames across 16 moves, hit and dodge, Bot and Web modes passed.`);
