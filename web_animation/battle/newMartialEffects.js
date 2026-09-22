import { ease, unit } from './choreography.js';
const noise = (i) => { const n = Math.sin(i * 127.1 + 31.7) * 43758.5453; return n - Math.floor(n); };
const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
function featherParticle(ctx, x, y, angle, size, accent) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    const fill = ctx.createLinearGradient(-size, 0, size, 0);
    fill.addColorStop(0, '#252c29');
    fill.addColorStop(.65, accent);
    fill.addColorStop(1, '#e5d9bc');
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.moveTo(-size, 0);
    ctx.quadraticCurveTo(-size * .15, -size * .42, size, 0);
    ctx.quadraticCurveTo(-size * .25, size * .22, -size, 0);
    ctx.fill();
    ctx.strokeStyle = '#e1ccaf';
    ctx.lineWidth = .65;
    ctx.beginPath();
    ctx.moveTo(-size * .7, 0);
    ctx.quadraticCurveTo(0, -size * .06, size * .85, 0);
    ctx.stroke();
    ctx.restore();
}
function line(ctx, points, width, color) {
    ctx.beginPath();
    ctx.moveTo(...points[0]);
    for (const point of points.slice(1))
        ctx.lineTo(...point);
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.stroke();
}
// Absolute-time particles and historical pose samples remain identical after seek.
// No stored trails, frame-count aging, RNG calls or synthetic damage events.
export function drawNewMartialEffects(ctx, feather, local, sample, dir, hitAge, hit, force, target, definition) {
    if (local < 180 || local > 1640)
        return;
    ctx.save();
    ctx.lineCap = 'round';
    const accent = feather ? '#9f4237' : '#81999c', f = sample(local);
    const signature = !definition || definition.signature;
    const budget = signature ? 1 : definition.power >= 1.3 ? 1.05 : .42 + (definition.power - .9) * .9;
    const kind = definition?.kind || (feather ? 'phoenix' : 'divide');
    if (local < 790) {
        const gather = ease((local - 200) / 220) * (1 - ease((local - 640) / 150));
        for (let i = 0; i < Math.round(11 * budget); i++) {
            const q = noise(i), a = q * Math.PI * 2 + local * .002;
            const radius = (1 - ease((local - 250) / 500)) * (24 + q * 24) + 7;
            ctx.globalAlpha = gather * (.25 + q * .35);
            featherParticle(ctx, f.hand[0] + Math.cos(a) * radius, f.hand[1] + Math.sin(a) * radius * .55, a, 3 + q * 4, accent);
        }
    }
    if (local > 470 && local < 980 && (signature || kind === 'dive' || kind === 'cascade')) {
        const takeoff = ease((local - 470) / 180) * (1 - ease((local - 820) / 160));
        const ground = sample(420).root;
        for (let i = 0; i < 4; i++) {
            ctx.globalAlpha = takeoff * (.18 - i * .025);
            ctx.strokeStyle = i % 2 ? accent : '#39433c';
            ctx.lineWidth = 1.2 + i * .25;
            ctx.beginPath();
            ctx.moveTo(ground[0] - dir * (30 + i * 14), 327 - i * 3);
            ctx.bezierCurveTo(ground[0] + dir * 50, 285 - i * 6, f.root[0] - dir * 60, f.root[1] - 20 - i * 12, f.root[0] + dir * 20, f.root[1] - 70 - i * 8);
            ctx.stroke();
        }
    }
    for (const [start, end] of definition?.strokes || [[760, 1180]])
        if (local > start && local < end + 60) {
            const opacity = signature ? ease((local - 760) / 90) * (1 - ease((local - 1030) / 150)) :
                ease((local - start) / 55) * (1 - ease((local - (end - 55)) / 115));
            const tail = Math.min(feather ? 125 : 175, end - start);
            const frames = Array.from({ length: 15 }, (_, i) => sample(Math.max(start - 30, local - tail + i * tail / 14)));
            ctx.globalAlpha = opacity * .25 * budget;
            ctx.fillStyle = accent;
            ctx.beginPath();
            ctx.moveTo(...frames[0].hand);
            for (const frame of frames)
                ctx.lineTo(...frame.tip);
            for (const frame of [...frames].reverse())
                ctx.lineTo(...mix(frame.hand, frame.tip, .55));
            ctx.closePath();
            ctx.fill();
            for (let i = 1; i < frames.length; i++) {
                ctx.globalAlpha = opacity * (i / frames.length) * .8;
                line(ctx, [frames[i - 1].tip, frames[i].tip], (feather ? 5 : 8) * i / frames.length * budget, accent);
                line(ctx, [frames[i - 1].tip, frames[i].tip], 1.2, '#fcf5df');
            }
            const angle = Math.atan2(f.tip[1] - f.hand[1], f.tip[0] - f.hand[0]);
            for (let i = 0; i < Math.round(18 * budget); i++) {
                const q = noise(i + 20), phase = (local / 310 + q) % 1;
                const at = mix(f.hand, f.tip, phase), spread = Math.sin(phase * Math.PI) * (5 + q * 10);
                ctx.globalAlpha = opacity * (1 - phase) * .65;
                featherParticle(ctx, at[0] - Math.sin(angle) * spread, at[1] + Math.cos(angle) * spread, angle, 3 + q * 7, accent);
            }
            if (!signature) {
                // Named accents follow each stroke, not a second fake hit or damage burst.
                const phase = unit((local - start) / (end - start)), tip = f.tip;
                ctx.globalAlpha = opacity * .55 * budget;
                if (kind === 'point' || kind === 'flurry') {
                    const core = mix(f.hand, tip, .6), endPoint = [tip[0] + Math.cos(angle) * 22, tip[1] + Math.sin(angle) * 22];
                    line(ctx, [core, endPoint], 3, accent);
                    line(ctx, [core, endPoint], .8, '#fff5df');
                    for (const sign of [-1, 1]) {
                        ctx.beginPath();
                        ctx.moveTo(core[0] - Math.sin(angle) * sign * 7, core[1] + Math.cos(angle) * sign * 7);
                        ctx.quadraticCurveTo(tip[0], tip[1], endPoint[0], endPoint[1]);
                        ctx.strokeStyle = accent;
                        ctx.lineWidth = .8;
                        ctx.stroke();
                    }
                }
                else if (kind === 'skim' || kind === 'sweep' || kind === 'undertow' || kind === 'surge') {
                    const layers = kind === 'surge' ? 3 : kind === 'undertow' ? 2 : 1;
                    for (let j = 0; j < layers; j++) {
                        const origin = sample(start + j * 16).root;
                        const y = kind === 'skim' ? 321 - j * 5 : tip[1] + 15 + j * 10;
                        ctx.beginPath();
                        ctx.moveTo(origin[0] - dir * 16, y + 6);
                        ctx.bezierCurveTo(origin[0] + dir * 40, y - 24 - j * 4, tip[0] - dir * 22, y + 12, tip[0] + dir * (24 + phase * 28), y - 8);
                        ctx.lineWidth = 1.8 - j * .4;
                        ctx.strokeStyle = j % 2 ? '#e5e9df' : accent;
                        ctx.stroke();
                    }
                }
                else if (kind === 'rise' || kind === 'cascade') {
                    const past = sample(start).tip;
                    for (const sign of [-1, 1]) {
                        ctx.beginPath();
                        ctx.moveTo(past[0] + dir * sign * 9, past[1]);
                        ctx.quadraticCurveTo(tip[0] - dir * (35 + sign * 8), past[1], tip[0] + dir * sign * 12, tip[1]);
                        ctx.strokeStyle = sign === 1 ? accent : '#ebeddf';
                        ctx.lineWidth = sign === 1 ? 2 : 1;
                        ctx.stroke();
                    }
                }
                else {
                    // Turning cuts and crossing cuts shed leaves tangential to the edge.
                    for (let i = 0; i < 6; i++) {
                        const q = noise(i + start), at = sample(Math.max(start, local - i * 13)).tip;
                        featherParticle(ctx, at[0] - dir * (8 + i * 4), at[1] + (q - .5) * 24, angle + q - .5, 4 + q * 7, accent);
                    }
                }
            }
        }
    // The finishing bloom is fixed at the struck body part, never at a moving hand.
    if (hit && hitAge >= 0 && hitAge < 490) {
        const age = unit(hitAge / 490), spread = ease(age), fade = (1 - age) ** 1.7;
        const strength = (.75 + force * .45) * Math.sqrt(budget);
        for (let i = 0; i < Math.round((feather ? 17 : 23) * budget); i++) {
            const q = noise(i + 61), angle = (q - .5) * Math.PI * 1.5;
            const distance = (24 + noise(i + 130) * (feather ? 90 : 112)) * spread * strength;
            const x = target[0] + dir * Math.cos(angle) * distance, y = target[1] + Math.sin(angle) * distance * .72 + age * age * 32;
            ctx.globalAlpha = fade * (.45 + q * .45);
            if (feather)
                featherParticle(ctx, x, y, angle + (dir < 0 ? Math.PI : 0) + age * .8, 5 + q * 9, accent);
            else {
                line(ctx, [[x - dir * 5 * (1 - age), y - 3], [x + dir * (6 + q * 8) * (1 - age), y + 2]], 1 + q * 2.8, i % 3 ? accent : '#2b3936');
            }
        }
        if (!feather && (signature || kind === 'surge'))
            for (const sign of [-1, 1]) {
                ctx.globalAlpha = fade * .6;
                ctx.strokeStyle = accent;
                ctx.lineWidth = 2.2 * (1 - age) + .3;
                ctx.beginPath();
                ctx.moveTo(target[0] + dir * spread * 8, target[1]);
                ctx.quadraticCurveTo(target[0] + dir * spread * 60, target[1] + sign * spread * 65, target[0] + dir * spread * 130, target[1] + sign * spread * 48);
                ctx.stroke();
                ctx.globalAlpha = fade * .8;
                ctx.strokeStyle = '#eeeede';
                ctx.lineWidth = .8;
                ctx.stroke();
            }
    }
    if (local > 1110 && local < 1530) {
        const age = unit((local - 1110) / 420), root = sample(1140).root;
        ctx.globalAlpha = (1 - age) * .22 * budget;
        ctx.strokeStyle = accent;
        for (let i = 0; i < 2; i++) {
            ctx.lineWidth = 1.2 - i * .3;
            ctx.beginPath();
            ctx.ellipse(root[0], 329, 18 + age * (64 + i * 18), 2 + age * (6 + i * 2), 0, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
    ctx.restore();
}
