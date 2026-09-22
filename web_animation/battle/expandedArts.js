import { serpentMotion, serpentEffects } from './serpentMotion.js';
import { phoenixMotion, phoenixEffects } from './phoenixMotion.js';
import { twoBone } from './sampleMotion.js';
import { ease } from './choreography.js';
import { holyMotion, holyEffects } from './holyMotion.js';
import { heavyMotion, heavyEffects } from './heavyMotion.js';

// Cosmetic scores only. Multi-stroke choreography never adds combat hits.
const m = (name, style, power, angle, lift = 0, strokes = 1, accent = 'edge') =>
    ({ name, style, power, angle, lift, strokes, accent, ultimate: name.startsWith('绝技') });
export const expandedArts = {
    staff_bainiaochaofeng: { name: '百鸟朝凤枪', type: 'staff', weapon: 'spear', color: '#b99b4c', moves: [
        m('凤点头', 'thrust', .9, -.22), m('穿林打叶', 'sweep', .85, .15, 0, 2, 'feather'),
        m('鸟鸣涧', 'rise', 1, -.35), m('百鸟入林', 'flurry', .85, -.1, 0, 3, 'feather'),
        m('有凤来仪', 'dive', 1.1, .45, 64, 1, 'feather'), m('乱花迷眼', 'flurry', .85, -.25, 0, 4, 'spark'),
        m('凤翔九天', 'rise', 1.2, -.58, 35, 2, 'feather'), m('绝技·百鸟朝凤', 'flurry', 1.35, -.08, 28, 5, 'phoenix'),
    ] },
    short_shenghuoling: { name: '圣火令', type: 'short_weapon', weapon: 'tokens', color: '#ca6035', moves: [
        m('诡步欺身', 'blink', .95, .35, 12), m('火树银花', 'cross', 1.05, -.15, 0, 2, 'spark'),
        m('夺刃式', 'hook', .8, -.65), m('影不留踪', 'blink', .95, -.3, 40),
        m('焚心似火', 'dive', .85, .3, 38, 1, 'fire'), m('绊马索', 'sweep', .85, .62),
        m('圣火燎原', 'cross', 1.1, .2, 20, 3, 'fire'), m('绝技·明王降世', 'dive', 1.35, .38, 72, 3, 'fire'),
    ] },
    sword_xuantie: { name: '玄铁重剑', type: 'sword', weapon: 'heavy_sword', color: '#525f6a', moves: [
        m('举重若轻', 'rise', 1.1, -.3), m('大巧不工', 'crush', 1.08, .08),
        m('铁锁横江', 'sweep', 1.08, .02), m('拍击', 'crush', 1.15, .36, 12, 1, 'stone'),
        m('顺水推舟', 'thrust', 1.12, -.05), m('泰山压顶', 'dive', 1.15, .56, 43, 1, 'stone'),
        m('横扫千军', 'sweep', 1.2, .18, 0, 2, 'stone'), m('绝技·破天', 'dive', 1.3, .36, 65, 1, 'rift'),
    ] },
    fist_qishang: { name: '七伤拳', type: 'unarmed', weapon: 'unarmed', color: '#95788f', moves: [
        m('损心诀', 'punch', .9, -.08, 0, 1, 'pulse'), m('伤肺诀', 'cross', 1, -.2, 0, 2, 'pulse'),
        m('摧肝肠诀', 'hook', 1.05, .18, 0, 2, 'pulse'), m('藏离诀', 'blink', 1, .22, 15, 1, 'pulse'),
        m('精失诀', 'punch', 1.1, .48, 0, 1, 'pulse'), m('意恍惚诀', 'hook', 1.05, -.4, 0, 3, 'pulse'),
        m('气浮躁诀', 'flurry', 1.1, -.15, 0, 4, 'pulse'), m('绝技·七者皆伤', 'punch', 1.12, 0, 0, 7, 'seven'),
    ] },
    whip_baimang: { name: '白蟒软鞭', type: 'flexible_weapon', weapon: 'whip', color: '#a9bdb5', moves: [
        m('银蛇吐信', 'lash', .72, -.18), m('灵蛇缠腕', 'bind', .76, -.25),
        m('毒龙卷柱', 'sweep', .8, .55, 0, 1, 'coil'), m('鳞片倒割', 'hook', .86, .12, 0, 2),
        m('狂蟒翻江', 'lash', .82, -.3, 20, 3), m('千丝万缕', 'lash', .9, -.12, 0, 5),
        m('嗜血蟒绞', 'bind', .9, -.18, 0, 2, 'coil'), m('绝技·白蟒索命', 'dive', 1.08, .15, 54, 3, 'coil'),
    ] },
};
export const expandedMoves = Object.entries(expandedArts).flatMap(([id, art]) =>
    art.moves.map(move => ({ id, name: art.name, type: art.type, move: move.name, power: move.power })));
export const expandedMoveFor = event => expandedArts[event?.martialArtId]?.moves.find(m => m.name === event?.move);
export const isExpandedArt = id => Boolean(expandedArts[id]);
export function expandedTechnique(event, fighter) {
    const id = event?.martialArtId || fighter?.martialArt?.id;
    const art = expandedArts[id], move = expandedMoveFor({ ...event, martialArtId: id });
    if (!move) return undefined;
    const motions = { dive: 'leap', crush: 'cleave', cross: 'slash', blink: 'draw', hook: 'slash', punch: 'palm', lash: 'sweep', bind: 'slash' };
    return { motion: motions[move.style] || move.style, trail: art.weapon === 'unarmed' ? 'wave' : 'edge',
        weight: move.ultimate ? 1.85 : move.power, color: art.color, pattern: 'direct' };
}

export function expandedMotion(event, time, travel) {
    if (event.martialArtId === 'whip_baimang') return serpentMotion(event, time, travel);
    if (event.martialArtId === 'staff_bainiaochaofeng') return phoenixMotion(event, time, travel);
    if (event.martialArtId === 'short_shenghuoling') return holyMotion(event, time, travel);
    if (event.martialArtId === 'sword_xuantie') return heavyMotion(event, time, travel);
    const move = expandedMoveFor(event);
    if (!move) return undefined;
    const weapon = expandedArts[event.martialArtId].weapon;
    const clamp = n => Math.max(0, Math.min(1, n));
    const prep = ease((time - 100) / 360), launch = ease((time - 470) / 480);
    const recover = ease((time - 1130) / 580);
    const strike = clamp((time - 610) / 340);
    const active = Math.sin(strike * Math.PI);
    // Independent extension/retraction beats, with final contact at 950 ms.
    const beat = move.strokes > 1 ? Math.pow(Math.abs(Math.cos((1 - strike) * Math.PI * move.strokes)), 3) : ease(strike);
    let angle = -2.3 * prep + (2.3 + move.angle) * ease(strike);
    let arm = angle, reach = 52 + 25 * beat * launch, height = 78, lean = -10 * prep + 31 * launch;
    if (['thrust', 'flurry', 'punch'].includes(move.style)) {
        angle = move.angle;
        arm = .55 - .45 * beat + move.angle;
        reach = 46 + 32 * beat;
    } else if (['rise', 'hook'].includes(move.style)) {
        angle = .9 - (1.6 - move.angle) * strike;
        arm = .9 - 1.15 * strike;
        height = 73 + 8 * strike;
    } else if (['sweep', 'lash', 'bind'].includes(move.style)) {
        angle = -2.7 + (2.7 + move.angle) * strike;
        if (move.style === 'lash') angle += Math.sin(strike * Math.PI * move.strokes * 2) * .38 * active;
        if (move.style === 'bind') angle += Math.sin(strike * Math.PI * 2) * .75;
        arm = angle * .45 + .2;
    } else if (move.style === 'cross') {
        angle = -1.8 + 2.1 * strike + Math.sin(strike * Math.PI * move.strokes) * 1.1 * active;
        arm = angle * .8;
    }
    let lift = -move.lift * Math.sin(Math.PI * clamp((time - 440) / 650));
    let progress = launch * (1 - recover);
    const blink = move.style === 'blink' && time > 510 && time < 690 ? Math.sin((time - 510) / 180 * Math.PI) : 0;
    if (move.style === 'blink') progress = ease((time - 520) / 220) * (1 - recover);
    angle = angle * (1 - recover) - .45 * recover;
    arm = arm * (1 - recover) + .48 * recover;
    reach = reach * (1 - recover) + 54 * recover;
    lean *= 1 - recover;
    const hip = [0, -height], neck = [lean, -height - Math.sqrt(52 * 52 - lean * lean)];
    const shoulders = [[neck[0] - 10, neck[1] + 6], [neck[0] + 10, neck[1] + 6]];
    let front = [shoulders[1][0] + Math.cos(arm) * reach, shoulders[1][1] + Math.sin(arm) * reach];
    let rear = [shoulders[0][0] - 55, shoulders[0][1] + 8 - 30 * active];
    if (weapon === 'tokens' || weapon === 'unarmed')
        rear = [shoulders[0][0] + Math.cos(-arm - .8) * (42 + 28 * active), shoulders[0][1] + Math.sin(-arm - .8) * (42 + 28 * active)];
    if (weapon === 'spear' || weapon === 'heavy_sword') {
        const gap = weapon === 'spear' ? 60 : 16;
        // Project the handle into both arm reach discs before solving elbows.
        for (let i = 0; i < 12; i++) {
            for (const [root, offset] of [[shoulders[1], 0], [shoulders[0], gap]]) {
                const dx = front[0] - offset * Math.cos(angle) - root[0];
                const dy = front[1] - offset * Math.sin(angle) - root[1];
                const d = Math.hypot(dx, dy);
                if (d > 77) { front[0] -= dx * (1 - 77 / d); front[1] -= dy * (1 - 77 / d); }
            }
        }
        rear = [front[0] - gap * Math.cos(angle), front[1] - gap * Math.sin(angle)];
    }
    const [elbow, hand] = twoBone(shoulders[1], front, 40, 1);
    const [backElbow, backHand] = twoBone(shoulders[0], rear, 40, -1);
    const stride = 36 + 19 * Math.sin(launch * Math.PI) + 16 * launch * (1 - recover);
    const footLift = lift < -5 ? -23 : 0;
    const [backKnee, backFoot] = twoBone(hip, [-stride, footLift], 48, -1);
    const [knee, foot] = twoBone(hip, [stride, footLift], 48, -1);
    const length = { spear: 140, heavy_sword: 110, tokens: 42, whip: 180, unarmed: 0 }[weapon];
    if (weapon !== 'whip' && angle > 0 && angle < Math.PI / 2 && length)
        angle = Math.min(angle, Math.asin(clamp((-hand[1] - 8) / length)));
    const stop = weapon === 'whip' ? 118 : weapon === 'spear' ? 30 : weapon === 'heavy_sword' ? 32 : 0;
    return { x: Math.max(0, travel - stop) * progress, lift, opacity: 1 - blink * .94, blink,
        pose: { points: [[neck[0], neck[1] - 21], neck, hip, backElbow, backHand, elbow, hand, backKnee, backFoot, knee, foot],
            shoulders, sword: angle, lean: 0 } };
}

export function drawExpandedEffects(ctx, event, local, sampleAt, target, dir, impactAge, hit) {
    if (event.martialArtId === 'whip_baimang') return serpentEffects(ctx, event, local, sampleAt, target, dir, impactAge, hit);
    if (event.martialArtId === 'staff_bainiaochaofeng') return phoenixEffects(ctx, event, local, sampleAt, target, dir, impactAge, hit);
    if (event.martialArtId === 'short_shenghuoling') return holyEffects(ctx, event, local, sampleAt, target, dir, impactAge, hit);
    if (event.martialArtId === 'sword_xuantie') return heavyEffects(ctx, event, local, sampleAt, target, dir, impactAge, hit);
    const move = expandedMoveFor(event), art = expandedArts[event?.martialArtId];
    if (!move || local < 440 || local > 1480) return;
    const fade = Math.max(0, Math.min(1, (1480 - local) / 300));
    const strength = move.ultimate ? 1.6 : .7 + move.power * .25;
    ctx.save(); ctx.lineCap = 'round'; ctx.strokeStyle = art.color;
    // Trails sample the actual held weapon, not a detached screen-space slash.
    for (let i = 0; i < (move.ultimate ? 18 : 11); i++) {
        const t = local - i * 12, a = sampleAt(t), b = sampleAt(t - 12);
        if (t < 560 || t > 1130) continue;
        ctx.globalAlpha = fade * (1 - i / 20) * .45;
        ctx.lineWidth = (1 - i / 21) * 5 * strength;
        ctx.beginPath(); ctx.moveTo(...a.tip); ctx.lineTo(...b.tip); ctx.stroke();
    }
    const source = sampleAt(Math.min(local, 950));
    const count = move.ultimate ? 32 : move.strokes * 3 + 5;
    for (let i = 0; i < count; i++) {
        const age = local - 580 - i * (move.ultimate ? 10 : 23);
        if (age < 0 || age > 510) continue;
        const f = age / 510, angle = i * 2.399;
        const x = source.tip[0] + dir * f * (30 + i % 5 * 10);
        const y = source.tip[1] + Math.sin(angle) * (12 + f * 30) - Math.sin(f * Math.PI) * 18;
        ctx.globalAlpha = fade * (1 - f) * .75;
        ctx.fillStyle = art.color; ctx.strokeStyle = art.color; ctx.lineWidth = 1.3;
        ctx.beginPath();
        if (art.weapon === 'spear') {
            ctx.moveTo(x - dir * 8, y + 5); ctx.quadraticCurveTo(x, y - 6, x + dir * 12, y - 2);
            ctx.stroke();
        } else {
            ctx.ellipse(x, y, art.weapon === 'heavy_sword' ? 3 : 1.7, 1.4, angle, 0, Math.PI * 2); ctx.fill();
        }
    }
    // Impact-only rings do not appear on misses or before the recorded hit.
    if (hit && impactAge >= 0 && impactAge < 500) {
        const f = impactAge / 500;
        ctx.globalAlpha = (1 - f) * .7;
        const rings = move.accent === 'seven' ? 7 : move.ultimate ? 4 : art.weapon === 'unarmed' ? 3 : 1;
        for (let i = 0; i < rings; i++) {
            const radius = 10 + f * (30 + i * 8) + i * 4;
            ctx.strokeStyle = art.color; ctx.lineWidth = (1 - f) * (move.ultimate ? 3 : 1.6);
            ctx.beginPath(); ctx.ellipse(target[0], target[1], radius * .65, radius, 0, 0, Math.PI * 2); ctx.stroke();
        }
        if (move.accent === 'rift' || move.accent === 'stone') {
            ctx.beginPath(); ctx.moveTo(target[0] - 55 * f, 327);
            for (let i = 0; i < 8; i++) ctx.lineTo(target[0] + (i - 4) * 16 * f, 327 - (i % 2) * 9);
            ctx.stroke();
        }
        if (move.accent === 'coil') {
            ctx.strokeStyle = '#b7c5bb'; ctx.lineWidth = 2.3 * (1 - f);
            for (let i = 0; i < (move.ultimate ? 4 : 2); i++) {
                ctx.beginPath();
                ctx.ellipse(target[0], target[1] - 12 + i * 15, 22 + f * 25, 8, -.25, f * 4, f * 4 + Math.PI * 1.7);
                ctx.stroke();
            }
        }
        if (move.accent === 'fire' || move.accent === 'phoenix') {
            for (const side of [-1, 1]) {
                ctx.beginPath(); ctx.moveTo(target[0], target[1] + 22);
                ctx.bezierCurveTo(target[0] + side * 90 * f, target[1] - 65, target[0] + side * 110 * f, target[1] - 70, target[0] + side * 32, target[1] - 6);
                ctx.stroke();
            }
        }
    }
    ctx.restore();
}
