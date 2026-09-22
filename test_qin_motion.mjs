import assert from 'node:assert/strict';
import { draw, poseAt } from './web_animation/battle/InkStage.js';
import { names, qinFX, qinTime } from './web_animation/battle/qinMotion.js';

function context() {
    const calls = [];
    const state = { globalAlpha: 1 };
    const ctx = new Proxy(state, {
        get(target, key) {
            if (key in target) return target[key];
            return (...args) => {
                assert.ok(args.every(value => typeof value !== 'number' || Number.isFinite(value)), String(key));
                calls.push([key, ...args]);
                if (key === 'createRadialGradient' || key === 'createLinearGradient') return { addColorStop() {} };
                if (key === 'measureText') return { width: 30 };
            };
        },
    });
    return { ctx, calls };
}

function sample(move, side, miss, lethal = false) {
    const fighter = { name: 'Qin', stats: { hp: 1000, spd: 60 }, martialArt: { id: 'zither_duanzhi', type: 'musical_instrument' } };
    const target = side === 'a' ? 'b' : 'a';
    const turn = { type: 'turn_start', time: 300, actor: side, action: 1 };
    return { attacker: fighter, defender: fighter, events: [
        { type: 'battle_start', time: 0 }, turn,
        { type: 'attack', time: 850, actor: side, target, action: 1, martialArtId: 'zither_duanzhi', move },
        miss ? { type: 'dodge', time: 1250, actor: side, target, action: 1 } :
            { type: 'damage', time: 1250, actor: side, target, action: 1, cause: 'strike', amount: lethal ? 1000 : 180, hpAfter: lethal ? 0 : 820 },
        { type: 'turn_end', time: 2100, action: 1 }, { type: 'battle_end', time: 2500 },
    ] };
}

for (const contact of [700, 950, 1100]) {
    assert.equal(qinTime(contact, contact), 950);
    assert.equal(qinTime(contact + 150, contact), 1100);
}
let frames = 0;
for (const move of names) for (const side of ['a', 'b']) for (const miss of [false, true]) {
    const battle = sample(move, side, miss), original = JSON.stringify(battle);
    for (const mode of ['legacy', 'current', 'mixed']) for (const time of [0, 300, 840, 1100, 1250, 1350, 1600, 2050, 2500]) {
        draw(context().ctx, battle, time, 1000, false, true, mode);
        frames++;
    }
    assert.equal(JSON.stringify(battle), original, 'Rendering must not mutate combat events');
    const target = side === 'a' ? 'b' : 'a', turn = battle.events[1];
    const rest = poseAt(battle, target, 800, 1000, turn, 'current');
    const reaction = poseAt(battle, target, 1390, 1000, turn, 'current');
    assert.notDeepEqual(rest.pose.points, reaction.pose.points, 'Qin victim must still react');
    const deadBattle = sample(move, side, false, true);
    const fallen = poseAt(deadBattle, target, 1900, 1000, turn, 'current');
    assert.ok(fallen.pose.points[0][1] > -50, 'Qin victim must still fall');
}
for (let index = 0; index < names.length; index++) {
    const a = context(), b = context(), miss = context();
    qinFX(a.ctx, index, 1080, 275, 765, true);
    qinFX(b.ctx, index, 1080, 275, 765, true);
    qinFX(miss.ctx, index, 1080, 275, 765, false);
    assert.deepEqual(a.calls, b.calls, 'Seeking must reproduce the same frame');
    assert.ok(a.calls.length > miss.calls.length, 'Misses must omit impact bursts');
}
console.log(`Qin: ${frames} frames, hit/miss, both sides, all modes, death and deterministic effects passed.`);
