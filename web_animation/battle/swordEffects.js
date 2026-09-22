import { unit } from './choreography.js';
import { swordSequenceFor } from './swordSequences.js';
// A move's standing within its own art is separate from rolled impact force.
// Huashan's configured multipliers: Qing Shan 1.5, Luo Mu 1.4.
export function swordEmphasis(event) {
    if (!swordSequenceFor(event))
        return 0;
    return event.move === '青山隐隐' ? 2 : event.move === '无边落木' || event.move === '回风斩' ? 1 : 0;
}
export function drawSwordSequenceEffects(ctx, event, local, tipAt, dir, impact) {
    if (!swordSequenceFor(event) || local < 400 || local > 1380)
        return;
    const name = event.move, tier = swordEmphasis(event), fade = 1 - unit((local - 1100) / 280);
    const pulses = name === '无边落木' ? [550, 735, 950] : name === '回风斩' ? [620, 950] : [950];
    const color = name === '回风斩' ? '#8b8fa7' : name === '无边落木' ? '#6d8869' : name === '金雁横空' ? '#b19855' : '#73aabd';
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = color;
    for (const pulse of pulses) {
        const age = local - pulse;
        if (age < -125 || age > 230)
            continue;
        const end = Math.min(local, pulse + 35), alpha = unit((age + 125) / 75) * (1 - unit((age - 45) / 185));
        ctx.globalAlpha = alpha * .75 * fade;
        for (const width of [7 + tier * 3, 2]) {
            ctx.strokeStyle = width === 2 ? '#f7f9ec' : color;
            ctx.lineWidth = width;
            ctx.beginPath();
            for (let i = 0; i < 14; i++) {
                const p = tipAt(end - 125 + i * 125 / 13);
                if (i === 0)
                    ctx.moveTo(...p);
                else
                    ctx.lineTo(...p);
            }
            ctx.stroke();
        }
        const tip = tipAt(Math.min(local, pulse));
        if (name === '无边落木' || name === '回风斩')
            for (let i = 0; i < 16 + tier * 5; i++) {
                const a = i * 2.399, flight = unit((age + 70) / 300);
                ctx.save();
                ctx.translate(tip[0] + Math.cos(a) * (12 + flight * 64) * dir, tip[1] + Math.sin(a) * 28 + flight * 42);
                ctx.rotate(a + flight * 3);
                ctx.fillStyle = color;
                ctx.globalAlpha = alpha * .6 * fade;
                ctx.beginPath();
                ctx.moveTo(-5, 0);
                ctx.quadraticCurveTo(1, -5, 8, 0);
                ctx.quadraticCurveTo(0, 5, -5, 0);
                ctx.fill();
                ctx.restore();
            }
    }
    if (name === '青山隐隐') {
        const tip = tipAt(Math.min(local, 950)), gather = unit((local - 600) / 220) * (1 - unit((local - 870) / 70));
        ctx.strokeStyle = color;
        for (let i = 0; i < 7; i++) {
            const a = i * 2.399, r = 12 + (1 - gather) * 45;
            ctx.globalAlpha = gather * .5;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(tip[0] + Math.cos(a) * r, tip[1] + Math.sin(a) * r);
            ctx.lineTo(tip[0] + Math.cos(a) * r * .5, tip[1] + Math.sin(a) * r * .5);
            ctx.stroke();
        }
        const flash = unit((local - 880) / 65) * (1 - unit((local - 990) / 170));
        for (let i = 0; i < 3; i++) {
            ctx.globalAlpha = flash * (.7 - i * .15);
            ctx.lineWidth = i === 0 ? 8 : 2;
            ctx.beginPath();
            ctx.moveTo(tip[0] - dir * (150 + i * 25), tip[1] + (i - 1) * 12);
            ctx.quadraticCurveTo(tip[0] - dir * 65, tip[1], tip[0] + dir * 20, tip[1]);
            ctx.stroke();
        }
    }
    // Extra visual weight belongs to the move, but contact sparks remain hit-only.
    if (tier && impact.hit && local >= 950 && local < 1150) {
        const p = tipAt(950), phase = (local - 950) / 200;
        ctx.globalAlpha = (1 - phase) * .6;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        for (let i = 0; i < 16; i++) {
            const a = i * 2.399, r = (15 + phase * 50) * (1 + impact.force * .3);
            ctx.beginPath();
            ctx.moveTo(p[0] + Math.cos(a) * r * .4, p[1] + Math.sin(a) * r * .4);
            ctx.lineTo(p[0] + Math.cos(a) * r, p[1] + Math.sin(a) * r);
            ctx.stroke();
        }
    }
    ctx.restore();
}
