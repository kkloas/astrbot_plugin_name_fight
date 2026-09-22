import { isNewArt } from './newMartialMotion.js';
const seeds = new WeakMap();
function hash(text, seed = 2166136261) {
    let n = seed;
    for (let i = 0; i < text.length; i++)
        n = Math.imul(n ^ text.charCodeAt(i), 16777619);
    n = Math.imul(n ^ (n >>> 16), 0x85ebca6b);
    n = Math.imul(n ^ (n >>> 13), 0xc2b2ae35);
    return (n ^ (n >>> 16)) >>> 0;
}
// Recorded combat already contains randomness. A cosmetic hash gives each action
// a 50/50 choice without combat RNG calls or frame-dependent random selection.
// Equal recordings retain their choices even after JSON round trips.
export function motionVariantFor(battle, event, mode = 'mixed') {
    if (isNewArt(event?.martialArtId))
        return 'current';
    if (mode !== 'mixed')
        return mode;
    if (!event)
        return 'current';
    let seed = seeds.get(battle);
    if (seed === undefined) {
        seed = hash(JSON.stringify([battle.attacker, battle.defender, battle.events]));
        seeds.set(battle, seed);
    }
    const key = JSON.stringify([event.action, event.actor, event.time, event.martialArtId, event.move]);
    return hash(key, seed) < 0x80000000 ? 'legacy' : 'current';
}
