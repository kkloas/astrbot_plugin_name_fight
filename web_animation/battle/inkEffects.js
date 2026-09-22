const clamp = (v) => Math.max(0, Math.min(1, v));
function arc(ctx, x, y, r, start, end, color, width = 1) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.arc(x, y, r, start, end);
    ctx.stroke();
}
function line(ctx, a, b, color, width = 1) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(...a);
    ctx.lineTo(...b);
    ctx.stroke();
}
export function drawAura(ctx, x, y, states, time, stacks = 1) {
    ctx.save();
    ctx.globalAlpha = .5;
    ctx.lineCap = 'round';
    if (states.includes('crisis_defense')) {
        ctx.save();
        ctx.translate(x, y - 75);
        ctx.scale(.78, 1.15);
        for (let i = 0; i < 3; i++)
            arc(ctx, 0, 0, 62 + i * 3, -1.25 + i * 2.1 + Math.sin(time / 900) * .1, .2 + i * 2.1, '#7b7758', 1.6);
        ctx.restore();
        ctx.strokeStyle = '#8c8b68';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.ellipse(x, y - 3, 48, 8, 0, 0, Math.PI * 2);
        ctx.stroke();
    }
    if (states.includes('stacking_defense')) {
        const layers = Math.max(1, Math.min(5, stacks));
        for (let i = 0; i < layers; i++) {
            const phase = time / 1300 + i * 1.25;
            arc(ctx, x, y - 76, 36 + i * 6, phase, phase + 2.8, '#795387', 1.8);
        }
        ellipse(ctx, x, y - 2, 34 + layers * 5, 7, '#906b9a', 1.5);
    }
    if (states.includes('deferred_damage')) {
        for (let i = 0; i < 3; i++) {
            const phase = time / 700 + i * 2.094;
            arc(ctx, x, y - 72, 19 + i * 7, phase, phase + 1.9, '#a45942', 2);
        }
    }
    if (states.includes('stunned')) {
        ctx.strokeStyle = '#65583e';
        ctx.beginPath();
        ctx.ellipse(x, y - 164, 21, 5, 0, 0, Math.PI * 2);
        ctx.stroke();
        for (let i = 0; i < 3; i++) {
            const a = time / 150 + i * 2.094;
            ctx.fillStyle = '#736143';
            ctx.beginPath();
            ctx.arc(x + Math.cos(a) * 21, y - 164 + Math.sin(a) * 5, 2.6, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    if (states.includes('slowed')) {
        for (let i = 0; i < 2; i++) {
            ctx.strokeStyle = '#636d6c';
            ctx.beginPath();
            ctx.ellipse(x, y - 8 - i * 13, 36 - i * 10, 6, 0, .2, 5.8);
            ctx.stroke();
        }
    }
    if (states.includes('armor_broken')) {
        line(ctx, [x - 14, y - 111], [x - 2, y - 89], '#8b5848', 1.5);
        line(ctx, [x - 2, y - 89], [x - 11, y - 80], '#8b5848', 1.5);
        line(ctx, [x - 11, y - 80], [x + 5, y - 57], '#8b5848', 1.5);
    }
    if (states.includes('weakened')) {
        for (let i = 0; i < 3; i++)
            line(ctx, [x - 32 + i * 29, y - 97], [x - 35 + i * 29, y - 72], '#80778a', 1.3);
    }
    for (const kind of ['bleeding', 'poisoned'])
        if (states.includes(kind)) {
            ctx.fillStyle = kind === 'bleeding' ? '#8c453a' : '#586b4f';
            for (let i = 0; i < 3; i++) {
                const fall = ((time / 14 + i * 19) % 55);
                ctx.beginPath();
                ctx.ellipse(x + 18 + i * 5, y - 79 + fall, 1.4, 2.8, 0, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    ctx.restore();
}
function ellipse(ctx, x, y, rx, ry, color, width = 1.5) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
    ctx.stroke();
}
function lotus(ctx, x, y, size, phase) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(size, size * .5);
    ctx.strokeStyle = '#50796d';
    ctx.fillStyle = 'rgba(113,150,125,.17)';
    ctx.lineWidth = 1.4 / size;
    for (let i = 0; i < 7; i++) {
        ctx.save();
        ctx.rotate((i - 3) * .38);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.bezierCurveTo(-12, -15, -7, -28 * phase, 0, -34 * phase);
        ctx.bezierCurveTo(7, -28 * phase, 12, -15, 0, 0);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
    }
    ctx.restore();
}
function cloud(ctx, x, y, width, color, phase) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(x - width, y);
    ctx.bezierCurveTo(x - width * .65, y - 12 * phase, x - width * .45, y + 5, x - width * .15, y - 7 * phase);
    ctx.bezierCurveTo(x + width * .05, y - 20 * phase, x + width * .4, y - 19 * phase, x + width * .43, y - 3);
    ctx.bezierCurveTo(x + width * .65, y - 10, x + width * .75, y + 1, x + width, y);
    ctx.stroke();
}
export function drawTrigger(ctx, event, x, otherX, age) {
    if (age < 0 || age > 1150)
        return;
    const p = clamp(age / 1150), open = clamp(age / 260);
    const fade = Math.min(1, age / 100, (1150 - age) / 350);
    const id = event.sourceSkill?.id;
    const effect = event.effect || event.cause || event.status;
    ctx.save();
    ctx.globalAlpha = fade * .85;
    ctx.lineCap = 'round';
    if (effect === 'fatal_block') {
        const color = '#b38a38';
        for (let i = 0; i < 3; i++) {
            ellipse(ctx, x, 248, 18 + open * 31 + i * 9, 30 + open * 45 + i * 9, color, 2.4 - i * .5);
        }
        ctx.fillStyle = 'rgba(233,204,115,.25)';
        ctx.beginPath();
        ctx.ellipse(x, 246, 16 + open * 13, 24 + open * 26, 0, 0, Math.PI * 2);
        ctx.fill();
        for (let i = 0; i < 12; i++) {
            const angle = i * Math.PI / 6;
            const radius = 24 + open * 45;
            line(ctx, [x + Math.cos(angle) * radius, 247 + Math.sin(angle) * radius],
                [x + Math.cos(angle) * (radius + 10), 247 + Math.sin(angle) * (radius + 10)], color, 2);
        }
        lotus(ctx, x, 324, 1.3 + open, open);
    }
    else if (event.type === 'guard' && id === 'jinzhong_zhao') {
        const vulnerable = (event.multiplier || 1) > 1;
        const color = vulnerable ? '#aa4436' : '#9b813e';
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(x - 48, 311);
        ctx.quadraticCurveTo(x - 36, 276, x - 36, 228);
        ctx.quadraticCurveTo(x - 34, 190, x, 186);
        ctx.quadraticCurveTo(x + 34, 190, x + 36, 228);
        ctx.quadraticCurveTo(x + 36, 276, x + 48, 311);
        ctx.stroke();
        ellipse(ctx, x, 311, 48, 9, color, 2.5);
        if (vulnerable) {
            line(ctx, [x - 15, 245], [x + 6, 258], color, 4);
            line(ctx, [x + 6, 258], [x - 7, 274], color, 4);
            ellipse(ctx, x, 260, 12 + open * 16, 10 + open * 12, color, 2);
        } else {
            for (let i = 0; i < 3; i++)
                ellipse(ctx, x, 316 + i * 3, 49 + open * (12 + i * 11), 9 + i * 3, color, 1.3);
        }
    }
    else if (effect === 'damage_defer' || effect === 'deferred_damage') {
        const release = effect === 'deferred_damage';
        const color = release ? '#a13c36' : '#a46642';
        for (let i = 0; i < 9; i++) {
            const phase = clamp((age - i * 18) / 650);
            const radius = release ? 15 + phase * 65 : 65 - phase * 46;
            const angle = i * 2.399 + phase * 3;
            arc(ctx, x, 257, radius, angle, angle + .8, color, 2.7);
        }
        ellipse(ctx, x, 257, 24 + open * 9, 35 + open * 13, color, 2);
    }
    else if (effect === 'stacking_defense') {
        const layers = Math.max(1, Math.min(5, event.stacks || 1));
        for (let i = 0; i < layers; i++)
            cloud(ctx, x, 310 - i * 23 - p * 12, 25 + open * (25 + i * 4), '#85588f', open);
        ellipse(ctx, x, 324, 30 + open * 44, 8, '#936ea0', 2);
    }
    else if (effect === 'part_counter') {
        const color = '#526f80';
        for (let i = 0; i < 2; i++)
            arc(ctx, x, 253, 32 + i * 10, p * 7 + i * Math.PI, p * 7 + i * Math.PI + 2.5, color, 2.5);
        for (let i = 0; i < 4; i++) {
            const phase = clamp((age - i * 65) / 620);
            const px = x + (otherX - x) * phase;
            const py = 253 - Math.sin(phase * Math.PI) * (24 + i * 10);
            ellipse(ctx, px, py, 5 + phase * 8, 3 + phase * 4, color, 2);
        }
    }
    else if (event.type === 'heal' && effect === 'vampirism') {
        const golden = id === 'golden_wind_record';
        const color = '#8a3d41';
        for (let i = 0; i < 19; i++) {
            const local = age - i * 16;
            if (local < 0)
                continue;
            const scatter = clamp(local / 180), flight = clamp((local - 150) / 610);
            const angle = i * 2.399, radius = 14 + (i % 5) * 6;
            const sx = otherX + Math.cos(angle) * radius * scatter;
            const sy = 245 + Math.sin(angle) * radius * .8 * scatter;
            const px = sx + (x - sx) * flight;
            const py = sy + (253 - sy) * flight - Math.sin(flight * Math.PI) * (18 + i % 4 * 9);
            ctx.globalAlpha = fade * (1 - flight * .7) * (.55 + i % 3 * .15);
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.ellipse(px, py, 1.8 + i % 3, 1.1 + i % 2, angle + flight, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalAlpha = fade * .55;
        if (golden)
            for (let i = 0; i < 3; i++)
                arc(ctx, x, 257, 21 + i * 8, p * 5 + i, p * 5 + i + 2.2, color, 1.5);
        else {
            arc(ctx, x, 252, 32, -1.3, 1.3, color, 4);
            arc(ctx, x - 7, 252, 32, -1.15, 1.15, '#c1a398', 1.2);
        }
    }
    else if (event.type === 'heal') {
        const burst = effect === 'burst_heal';
        const color = burst ? '#437f79' : '#557948';
        ellipse(ctx, x, 322, 24 + open * (burst ? 62 : 26), 4 + open * 8, color);
        for (let i = 0; i < (burst ? 10 : 6); i++) {
            const phase = clamp((age - i * 30) / 800);
            const angle = i * 2.399 + phase * 1.6;
            const radius = (burst ? 42 : 24) * (1 - phase * .7);
            const px = x + Math.cos(angle) * radius, py = 314 - phase * 115;
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.6;
            ctx.beginPath();
            ctx.moveTo(px, py + 18);
            ctx.quadraticCurveTo(px + Math.sin(angle) * 15, py + 5, px + 4, py - 4);
            ctx.stroke();
            if (!burst) {
                ctx.fillStyle = 'rgba(86,124,70,.6)';
                ctx.beginPath();
                ctx.ellipse(px + 5, py - 1, 5, 2.2, -.7, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        if (burst) {
            for (let i = 0; i < 3; i++)
                cloud(ctx, x, 295 - i * 35 - p * 10, 25 + open * 38, color, open);
            ctx.save();
            ctx.translate(x, 256);
            ctx.scale(.8, 1);
            arc(ctx, 0, 0, 30 + open * 43, -2.8, -.3, color, 2.5);
            arc(ctx, 0, 0, 30 + open * 43, .3, 2.8, color, 2.5);
            ctx.restore();
        }
    }
    else if (effect === 'thorns' || event.type === 'guard' || effect === 'crisis_defense') {
        const vulnerable = event.type === 'guard' && (event.multiplier || 1) > 1;
        const iron = id === 'iron_wall_art';
        const color = vulnerable ? '#914f42' : iron ? '#657773' : id === 'xiantian_qigong' ? '#8a8054' : '#877552';
        if (vulnerable) {
            const y = event.bodyPartKey === 'chest' ? 235 : 263;
            for (let i = 0; i < 3; i++) {
                line(ctx, [x - 22 + i * 19, y - 23], [x - 10 + i * 15, y], color, 2);
                line(ctx, [x - 10 + i * 15, y], [x - 23 + i * 20, y + 17], color, 1.5);
            }
        }
        else if (iron) {
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            for (let i = 0; i < 5; i++) {
                const angle = (i - 2) * .4, px = x + Math.sin(angle) * (30 + open * 15), py = 247 + (i % 2) * 17;
                ctx.beginPath();
                ctx.moveTo(px - 10, py - 35);
                ctx.lineTo(px + 10, py - 35);
                ctx.lineTo(px + 13, py + 9);
                ctx.lineTo(px, py + 20);
                ctx.lineTo(px - 13, py + 9);
                ctx.closePath();
                ctx.fillStyle = 'rgba(123,144,135,.12)';
                ctx.fill();
                ctx.stroke();
            }
        }
        else {
            ctx.save();
            ctx.translate(x, 253);
            ctx.scale(.8, 1);
            for (let i = 0; i < 3; i++)
                arc(ctx, 0, 0, 37 + open * 22 + i * 6, -2.9 + i * .4, 2.9 - i * .4, color, 2 - i * .4);
            ctx.restore();
            ellipse(ctx, x, 323, 38 + open * 32, 7 + open * 5, color, 1.2);
        }
        if (effect === 'thorns') {
            const direction = otherX >= x ? 1 : -1;
            for (let i = 0; i < 3; i++) {
                const t = clamp((age - 70 * i) / 470), px = x + (otherX - x) * t;
                ctx.save();
                ctx.translate(px, 251);
                ctx.scale(direction, 1);
                arc(ctx, -18, 0, 20 + i * 7, -1.05, 1.05, color, 2.5 - i * .5);
                ctx.restore();
            }
            if (!iron) {
                for (let i = 0; i < 8; i++) {
                    const a = i * Math.PI / 4;
                    line(ctx, [x + Math.cos(a) * 25, 255 + Math.sin(a) * 28], [x + Math.cos(a) * (40 + open * 27), 255 + Math.sin(a) * (40 + open * 27)], color, 1.5);
                }
            }
        }
    }
    else if (event.type === 'passive_trigger') {
        const strong = effect === 'low_hp_extra_action';
        const color = strong ? '#685166' : '#55716c';
        ellipse(ctx, x, 323, 28 + open * 46, 5 + open * 7, color, 1.4);
        for (let i = 0; i < 6; i++) {
            const phase = strong ? (p < .35 ? 1 - p / .35 : (p - .35) / .65) : open;
            const a = i * 2.399 + p * 3, r = 18 + phase * 58;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.ellipse(x + Math.cos(a) * r, 257 + Math.sin(a) * r, 5, 1.8, a, 0, Math.PI * 2);
            ctx.fill();
        }
        if (strong) {
            for (let i = 0; i < 3; i++)
                arc(ctx, x, 258, 25 + open * 30 + i * 8, p * 5 + i * 2, p * 5 + i * 2 + 1.7, color, 2);
        }
        else {
            for (const direction of [-1, 1]) {
                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x, 264);
                ctx.bezierCurveTo(x + direction * 20, 225, x + direction * 45, 216, x + direction * 72, 215 + open * 22);
                ctx.stroke();
                for (let i = 0; i < 4; i++)
                    line(ctx, [x + direction * (23 + i * 9), 233 - i * 3], [x + direction * (35 + i * 12), 250 - i * 2], color, 1);
            }
        }
    }
    ctx.restore();
}
export function drawFootwork(ctx, id, x, dir, phase, time, trace = []) {
    if (phase <= 0)
        return;
    ctx.save();
    ctx.globalAlpha = phase * .72;
    ctx.lineCap = 'round';
    const trail = trace.length ? trace : [{ x: x - dir * 25, y: 324 }, { x: x - dir * 50, y: 324 }];
    if (id === 'phantom_lotus') {
        for (let i = trail.length - 1; i >= 0; i--) {
            ctx.globalAlpha = phase * (.55 - i * .08);
            lotus(ctx, trail[i].x, 326, .6 + (trail.length - i) * .14, .8);
            ellipse(ctx, trail[i].x, 327, 25 + i * 8, 4 + i, '#6e9685', 1);
        }
    }
    else if (id === 'lightning_flash') {
        for (let j = 0; j < 3; j++) {
            ctx.strokeStyle = j === 0 ? '#96834c' : '#b2a16b';
            ctx.lineWidth = j === 0 ? 2.2 : 1;
            ctx.beginPath();
            ctx.moveTo(x, 313 - j * 12);
            for (let i = 0; i < trail.length; i++) {
                ctx.lineTo(trail[i].x + dir * (i % 2 ? 10 : -10), 311 - j * 12 + (i % 2 ? 5 : -7));
                ctx.lineTo(trail[i].x, 309 - j * 12);
            }
            ctx.stroke();
        }
    }
    else if (id === 'earth_root') {
        for (let i = 0; i < 7; i++) {
            const drift = ((time / 60 + i * 7) % 15);
            ctx.fillStyle = '#81755f';
            ctx.beginPath();
            ctx.moveTo(x - 40 + i * 13, 325 - drift * .25);
            ctx.lineTo(x - 36 + i * 13, 320 - drift * .6);
            ctx.lineTo(x - 33 + i * 13, 326);
            ctx.closePath();
            ctx.fill();
        }
        ellipse(ctx, x, 326, 42, 5, '#887e67', 1);
    }
    else if (id === 'shadow_drift') {
        for (let i = 0; i < trail.length; i++) {
            const pos = trail[i];
            ctx.globalAlpha = phase * (.35 - i * .045);
            ctx.strokeStyle = '#4c6266';
            ctx.lineWidth = 4 - i * .6;
            ctx.beginPath();
            ctx.moveTo(pos.x - dir * 25, pos.y - 40);
            ctx.quadraticCurveTo(pos.x - dir * 42, pos.y - 18, pos.x + dir * 12, pos.y - 5);
            ctx.stroke();
        }
    }
    else if (id === 'swan_shadow') {
        for (let i = 0; i < trail.length; i++) {
            const pos = trail[i];
            ctx.globalAlpha = phase * (.45 - i * .07);
            ctx.strokeStyle = '#607d77';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(pos.x - dir * 20, pos.y - 3);
            ctx.bezierCurveTo(pos.x - dir * 55, pos.y - 30, pos.x - dir * 70, pos.y - 45, pos.x - dir * 92, pos.y - 34);
            ctx.stroke();
            for (let j = 0; j < 3; j++)
                line(ctx, [pos.x - dir * (37 + j * 13), pos.y - 20 - j * 5], [pos.x - dir * (45 + j * 16), pos.y - 5 - j * 5], '#607d77', 1.2);
        }
    }
    else if (id === 'shadow_fragrance') {
        for (let i = 0; i < trail.length; i++) {
            ctx.globalAlpha = phase * (.45 - i * .065);
            const pos = trail[i];
            cloud(ctx, pos.x, pos.y - 5, 22 + i * 8, '#65566b', .8);
            ctx.fillStyle = '#6e596b';
            ctx.beginPath();
            ctx.ellipse(pos.x - dir * 18, pos.y - 19 - Math.sin(time / 230 + i) * 8, 4, 1.8, i, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    else {
        for (let i = 0; i < trail.length; i++) {
            ctx.globalAlpha = phase * (.5 - i * .07);
            cloud(ctx, trail[i].x, 326 - i % 2 * 4, 30 + i * 4, '#6b8178', .8 + Math.sin(time / 400 + i) * .1);
        }
    }
    ctx.restore();
}
