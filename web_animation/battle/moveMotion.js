import { ease, unit } from './choreography.js';
import { sampleMotion, sampleMove, twoBone, rigLengths } from './sampleMotion.js';
import { profileFor } from './moveProfiles.js';
import { swordSequence } from './swordSequences.js';
import { newMartialMotion } from './newMartialMotion.js';
import { expandedMotion } from './expandedArts.js';
const pt = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
const beat = (front, rear, angle, tilt = 8) => ({ front, rear, angle, tilt });
function arc(a, b, t, root) {
    const start = Math.atan2(a[1] - root[1], a[0] - root[0]), end = Math.atan2(b[1] - root[1], b[0] - root[0]);
    const delta = Math.atan2(Math.sin(end - start), Math.cos(end - start));
    const radius = Math.max(18, Math.hypot(a[0] - root[0], a[1] - root[1]) * (1 - t) + Math.hypot(b[0] - root[0], b[1] - root[1]) * t);
    return [root[0] + Math.cos(start + delta * t) * radius, root[1] + Math.sin(start + delta * t) * radius];
}
function between(a, b, t) {
    return { front: arc(a.front, b.front, t, [10, 6]), rear: arc(a.rear, b.rear, t, [-10, 6]), angle: a.angle + (b.angle - a.angle) * t, tilt: a.tilt + (b.tilt - a.tilt) * t };
}
function sample(keys, t) {
    for (let i = 1; i < keys.length; i++)
        if (t < keys[i][0])
            return between(keys[i - 1][1], keys[i][1], ease((t - keys[i - 1][0]) / (keys[i][0] - keys[i - 1][0])));
    return keys[keys.length - 1][1];
}
// Every style has a readable preparation, contact and follow-through. The named
// profile chooses its timing, variant and amplitude rather than random poses.
function score(p, t) {
    const v = p.variation, a = p.anticipation;
    const guard = beat([54, 22], [-48, 22], -.4);
    const thrust = beat([84, 20 - v * 6], [-62, 4], -.03, 22);
    const overhead = beat([18, -54], [-36, 8], -2.15, -8);
    const low = beat([12, 62], [-54, 16], .38, -5);
    const back = beat([-24, 38], [-49, -5], -2.6, -12);
    const slash = beat([76, 20 + v * 7], [-59, -4], .05 + v * .15, 22);
    const high = beat([48, -46], [-57, 16], -.95, 16);
    let prep = back, contact = slash, follow = beat([56, 53], [-40, 18], .6, 12);
    switch (p.style) {
        case 'thrust':
            prep = beat([-18, 37], [-60, 12], -.1, -7);
            contact = thrust;
            follow = thrust;
            break;
        case 'cross':
            prep = v === 1 ? low : overhead;
            contact = slash;
            break;
        case 'rise':
            prep = low;
            contact = beat([78, 28], [-62, 10], -.13, 20);
            follow = high;
            break;
        case 'cleave':
            prep = overhead;
            contact = beat([75, 13], [-46, -8], .04, 23);
            break;
        case 'sweep':
            prep = beat([-25, 40], [-40, 8], -2.85, -10);
            contact = beat([77, 56], [-65, 5], .02, 19);
            follow = beat([52, 47], [-40, 15], .4, 7);
            break;
        case 'spin':
            prep = back;
            contact = beat([78, 14 + v * 9], [-67, -5], .12, 20);
            break;
        case 'flurry':
            prep = beat([16, -44], [-45, 15], -1.8, -8);
            contact = v === 2 ? thrust : slash;
            follow = high;
            break;
        case 'leap':
            prep = beat([28, -40], [-63, 12], -1.85, -9);
            contact = v === 1 ? thrust : slash;
            follow = high;
            break;
        case 'draw':
            prep = beat([-14, 51], [-36, 50], -2.8, -12);
            contact = beat([83, 10], [-66, -7], -.06, 22);
            follow = slash;
            break;
        case 'palm':
        case 'shock':
            prep = beat([-18, 50], [-48, 24], 0, -7);
            contact = beat([84, 22], [-66, -3], 0, 24);
            follow = contact;
            break;
        case 'kick':
            prep = guard;
            contact = beat([47, -28], [-72, -12], 0, -20);
            follow = guard;
            break;
        case 'hook':
            prep = beat([-18, 40], [-50, 20], -2.2, -5);
            contact = beat([70, 10 + v * 8], [-59, 10], -.16, 18);
            follow = beat([40, 44], [-45, 8], 1, 8);
            break;
        case 'coil':
            prep = beat([12, -36], [-58, 18], -1.8, -7);
            contact = beat([72, 28], [-58, 8], .25, 18);
            follow = beat([-18, 46], [-45, 20], -2.6, -6);
            break;
        case 'fan':
            prep = beat([48, -30], [-58, -26], -.4, -4);
            contact = beat([80, 18], [-69, 17], 0, 12);
            follow = guard;
            break;
        case 'needle':
            prep = beat([-24, 40], [-52, 25], 0, -9);
            contact = beat([83, 8 - v * 8], [-60, 10], 0, 15);
            follow = guard;
            break;
        case 'rain':
            prep = beat([48, -43], [-60, -24], 0, -6);
            contact = beat([79, 9], [-66, 10], 0, 14);
            follow = guard;
            break;
        case 'pluck':
            prep = beat([10, 47], [-35, 42], 0, -3);
            contact = beat([43 + v * 7, 40], [-35, 42], 0, 6);
            follow = prep;
            break;
        case 'strum':
            prep = beat([-15, 20], [-36, 42], 0, -8);
            contact = beat([64, 46], [-36, 42], 0, 13);
            follow = guard;
            break;
        case 'crescendo':
            prep = beat([7, -25], [-36, 42], 0, -10);
            contact = beat([72, 30], [-36, 42], 0, 19);
            follow = beat([45, 52], [-36, 42], 0, 7);
            break;
    }
    const keys = [[0, guard], [260, guard], [a, prep]];
    if (p.style === 'flurry') {
        keys.push([a + (950 - a) * .35, v === 2 ? thrust : slash], [a + (950 - a) * .65, v === 1 ? high : prep]);
    }
    else if (p.style === 'spin' || p.style === 'coil') {
        keys.push([a + (950 - a) * .48, overhead]);
    }
    else if (p.style === 'rain' || p.style === 'fan') {
        keys.push([a + (950 - a) * .45, contact], [a + (950 - a) * .68, beat([22, -35], [-60, -15], 0, -3)]);
    }
    else if (p.style === 'crescendo' && v === 1) {
        keys.push([690, contact], [760, prep], [825, contact], [875, prep]);
    }
    keys.push([950, contact], [1040, contact], [1140, follow], [1240, guard], [1740, guard]);
    return sample(keys, t);
}
export function moveMotion(event, t, travel, weapon, missed = false) {
    const expanded = expandedMotion(event, t, travel);
    if (expanded) return expanded;
    const candidate = newMartialMotion(event, t, travel);
    if (candidate)
        return candidate;
    const sword = swordSequence(event, t, travel, missed);
    if (sword)
        return sword;
    const named = sampleMove(event);
    if (named)
        return sampleMotion(named, t, travel, missed);
    const profile = profileFor(event);
    if (!profile)
        return undefined;
    const ranged = weapon === 'needles' || weapon === 'zither';
    const base = sampleMotion('sword', t, ranged ? 0 : travel, missed);
    const original = base.pose;
    const b = score(profile, t);
    const weight = ease((t - 150) / 150) * (1 - ease((t - 1240) / 130));
    const hip = [original.points[2][0], ranged ? -75 : original.points[2][1]];
    const sweep = event.weaponType === 'leg' && profile.style === 'sweep' ? ease((t - 760) / 150) * (1 - ease((t - 1050) / 150)) : 0;
    hip[1] += 24 * sweep;
    const rotation = b.tilt * weight;
    const neck = [hip[0] + rotation, hip[1] - Math.sqrt(52 * 52 - rotation * rotation)];
    const shoulders = [[neck[0] - 10, neck[1] + 6], [neck[0] + 10, neck[1] + 6]];
    let front = [neck[0] + b.front[0], neck[1] + b.front[1]];
    let rear = [neck[0] + b.rear[0], neck[1] + b.rear[1]];
    let angle = b.angle;
    let feet = [[...original.points[8]], [...original.points[10]]];
    if (ranged) {
        base.x = 0;
        base.lift = 0;
        feet = [[-41, 0], [41, 0]];
    }
    if (profile.style === 'draw' && t < 1240) {
        base.x = Math.max(0, travel - 28) * ease((t - 760) / 190);
        if (t < 760) {
            base.lift = 0;
            feet = [[-41, 0], [41, 0]];
        }
        else {
            base.lift = -24 * Math.sin(Math.PI * unit((t - 760) / 190));
            const fold = ease((t - 760) / 90);
            feet = [pt([-41, 0], [-68, -10], fold), pt([41, 0], [47, -7], fold)];
        }
        const landing = ease((t - 950) / 120);
        feet = feet.map((f, i) => pt(f, [i === 0 ? -47 : 42, 0], landing));
    }
    if (profile.style === 'leap') {
        const flight = unit((t - 580) / 590), fold = ease((t - 580) / 100) * (1 - ease((t - 1090) / 80));
        base.lift -= Math.sin(Math.PI * flight) * 70 * profile.amplitude;
        feet = [pt(feet[0], [-73, -34], fold), pt(feet[1], [51, -44], fold)];
    }
    if (event.weaponType === 'leg' && profile.style === 'sweep') {
        feet = [pt(feet[0], [-40, 0], sweep), pt(feet[1], [94, -12], sweep)];
    }
    angle = original.sword + (angle - original.sword) * weight;
    front = arc(original.points[6], front, weight, shoulders[1]);
    rear = arc(original.points[4], rear, weight, shoulders[0]);
    if (weapon === 'spear') {
        const thrust = profile.style === 'thrust' ? 1 : profile.style === 'flurry' ? ease((t - 770) / 100) : 0;
        const push = ease((t - profile.anticipation) / (950 - profile.anticipation)) * (1 - ease((t - 1070) / 150));
        const overhead = profile.style === 'cleave' ? ease((t - 300) / (profile.anticipation - 300)) * (1 - ease((t - profile.anticipation) / (950 - profile.anticipation))) : 0;
        const center = [neck[0] + 12 + (40 * push - 12) * thrust, neck[1] + 36 - 20 * push - 62 * overhead];
        // Keep both grips on one shaft and inside both arms' reach.
        for (let i = 0; i < 8; i++)
            for (const sign of [-1, 1]) {
                const root = shoulders[sign === 1 ? 1 : 0];
                const dx = center[0] + sign * 34 * Math.cos(angle) - root[0], dy = center[1] + sign * 34 * Math.sin(angle) - root[1];
                const distance = Math.hypot(dx, dy);
                if (distance > 77) {
                    center[0] -= dx * (1 - 77 / distance);
                    center[1] -= dy * (1 - 77 / distance);
                }
            }
        front = [center[0] + 34 * Math.cos(angle), center[1] + 34 * Math.sin(angle)];
        rear = [center[0] - 34 * Math.cos(angle), center[1] - 34 * Math.sin(angle)];
    }
    else if ((weapon === 'blade' || weapon === 'katana') && profile.style === 'cleave') {
        rear = [front[0] - 16 * Math.cos(angle), front[1] - 16 * Math.sin(angle)];
    }
    const [backElbow, backHand] = twoBone(shoulders[0], rear, rigLengths.arm, -1);
    const [elbow, hand] = twoBone(shoulders[1], front, rigLengths.arm, 1);
    const [backKnee, backFoot] = twoBone(hip, feet[0], 48, -1);
    const [knee, foot] = twoBone(hip, feet[1], 48, -1);
    const bladeLength = { sword: 99, blade: 107, katana: 112, spear: 140, brush: 45 }[weapon];
    if (bladeLength && weapon !== 'spear' && angle > 0 && angle < Math.PI / 2)
        angle = Math.min(angle, Math.asin(unit((-hand[1] - 5) / bladeLength)));
    const pose = { points: [[neck[0], neck[1] - 21], neck, hip, backElbow, backHand, elbow, hand, backKnee, backFoot, knee, foot], shoulders, sword: angle, lean: 0 };
    return { ...base, pose };
}
