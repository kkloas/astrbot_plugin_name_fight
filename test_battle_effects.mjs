// Run with: node test_battle_effects.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const load = async (name) => import(`data:text/javascript;base64,${Buffer.from(await readFile(new URL(`./web_animation/battle/${name}.js`, import.meta.url))).toString('base64')}`);
const { stateAt } = await load('replay');
const { drawAura, drawTrigger } = await load('inkEffects');
const battle = {
    attacker: { currentHp: 100, stats: { hp: 100 } },
    defender: { currentHp: 100, stats: { hp: 100 } },
    events: [
        { type: 'status_apply', time: 100, target: 'b', status: 'disarmed' },
        { type: 'status_apply', time: 140, target: 'b', status: 'bleeding' },
        { type: 'status_apply', time: 180, target: 'a', status: 'stacking_defense', stacks: 3 },
        { type: 'damage', time: 220, target: 'b', hpAfter: 0 },
        { type: 'heal', time: 260, target: 'b', hpAfter: 1, cause: 'fatal_block' },
        { type: 'turn_end', time: 500, states: { a: [{ type: 'stacking_defense', duration: 9999 }], b: [] }, weaponsReady: { a: true, b: true } },
    ],
};
assert.equal(stateAt(battle, 120).weaponsReady.b, false);
assert.deepEqual(stateAt(battle, 150).states.b, ['disarmed', 'bleeding']);
assert.equal(stateAt(battle, 200).stacks.a, 3);
assert.equal(stateAt(battle, 240).hp.b, 0);
assert.equal(stateAt(battle, 280).hp.b, 1);
assert.equal(stateAt(battle, 500).weaponsReady.b, true);
assert.deepEqual(stateAt(battle, 500).states.b, []);

function drawingContext() {
    const calls = [];
    const ctx = new Proxy({}, {
        get(_target, method) {
            return (...args) => {
                for (const value of args)
                    if (typeof value === 'number') assert.ok(Number.isFinite(value), `${method} received a non-finite coordinate`);
                calls.push(method);
            };
        },
    });
    return { ctx, marks: () => calls.filter(name => ['stroke', 'fill', 'fillRect'].includes(name)).length };
}
const triggers = [
    { type: 'heal', cause: 'fatal_block', sourceSkill: { id: 'shenzhao_jing' } },
    { type: 'guard', multiplier: .5, sourceSkill: { id: 'jinzhong_zhao' } },
    { type: 'guard', multiplier: 1.5, sourceSkill: { id: 'jinzhong_zhao' } },
    { type: 'status_apply', effect: 'damage_defer' },
    { type: 'damage', cause: 'deferred_damage' },
    { type: 'status_apply', status: 'stacking_defense', stacks: 5 },
    { type: 'damage', cause: 'part_counter' },
    { type: 'heal', cause: 'regeneration' },
    { type: 'heal', cause: 'burst_heal' },
    { type: 'heal', cause: 'vampirism' },
    { type: 'damage', cause: 'thorns' },
    { type: 'status_apply', status: 'crisis_defense' },
    { type: 'passive_trigger', effect: 'battle_start_first_strike' },
    { type: 'passive_trigger', effect: 'low_hp_extra_action' },
    { type: 'passive_trigger', effect: 'action_spd_stack' },
    { type: 'passive_trigger', effect: 'dodge_damage_boost' },
];
for (const event of triggers) {
    const { ctx, marks } = drawingContext();
    drawTrigger(ctx, event, 200, 600, 350);
    assert.ok(marks() > 0, `No visual for ${JSON.stringify(event)}`);
}
for (const status of ['bleeding', 'poisoned', 'stunned', 'slowed', 'weakened', 'armor_broken', 'crisis_defense', 'stacking_defense', 'deferred_damage']) {
    const { ctx, marks } = drawingContext();
    drawAura(ctx, 200, 324, [status], 350, 3);
    assert.ok(marks() > 0, `No persistent aura for ${status}`);
}
console.log('Replay state, weapon recovery, fatal survival, 16 trigger visuals, and 9 persistent auras passed.');
