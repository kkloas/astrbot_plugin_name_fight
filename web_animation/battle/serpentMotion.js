import { twoBone } from './sampleMotion.js';
import { drawStripSlicedImage } from './xianglongArts.js';

const pythonHead = typeof Image === 'undefined' ? null : new Image();
if (pythonHead) pythonHead.src = new URL('./assets/ink-python-wash.png', import.meta.url).href;
const whipSweep = typeof Image === 'undefined' ? null : new Image();
if (whipSweep) whipSweep.src = new URL('./assets/ink-whip-sweep.png', import.meta.url).href;

export function waitForSerpentAssets() {
    const imgs = [pythonHead, whipSweep].filter(Boolean);
    if (!imgs.length) return Promise.resolve();
    return Promise.all(
        imgs.map((img) => {
            if (img.complete && img.naturalWidth > 0) return Promise.resolve();
            if (typeof img.decode === 'function') {
                return img.decode().catch(() => {});
            }
            return new Promise((resolve) => {
                img.addEventListener('load', () => resolve(), { once: true });
                img.addEventListener('error', () => resolve(), { once: true });
            });
        }),
    ).then(() => {});
}

export const names = ['银蛇吐信', '灵蛇缠腕', '毒龙卷柱', '鳞片倒割', '狂蟒翻江', '千丝万缕', '嗜血蟒绞', '绝技·白蟒索命'];
export const notes = [
    '腕抖弹梢 / 银蛇吐信 / 毒珠飞溅',
    '绕腕成环 / 沉肩回拽 / 蛇牙倒钩',
    '贴地游走 / 螺旋攀升 / 蟒柱封步',
    '三番送鞭 / 连抽倒割 / 飞鳞逆割',
    '连续抡抽 / 延长鞭打 / 翻江白浪',
    '高速连抽 / 细影交织 / 毒雨千丝',
    '合围成圈 / 两段收紧 / 拧转回扯',
    '腾空掷鞭 / 白蟒扑咬 / 锁身绞杀',
];

const clamp = (x) => Math.max(0, Math.min(1, x));
const ease = (x) => {
    const v = clamp(x);
    return v * v * (3 - 2 * v);
};
const snap = (t, start, dur, power = 2.8) => 1 - Math.pow(1 - clamp((t - start) / Math.max(1, dur)), power);
const mix = (a, b, u) => a + (b - a) * u;
const end = (i) => (i === 4 ? 2180 : i >= 3 && i <= 6 ? 1860 : 1340);
const beat = (i, t) => {
    const period = i === 3 ? 280 : i === 4 ? 310 : 180;
    return (1 - Math.cos(((clamp((t - 600) / (end(i) - 600)) * (end(i) - 600)) / period) * Math.PI * 2)) / 2;
};
const seed = (n) => {
    const x = Math.sin(n * 127.1) * 43758.5453;
    return x - Math.floor(x);
};

const CYAN_DEEP_RGB = '13,148,136';
const CYAN_BRIGHT_RGB = '20,184,166';
const CYAN_GLOW_RGB = '45,212,191';
const VENOM_WHITE_RGB = '248,250,252';
const VENOM_MIST_RGB = '236,254,255';
const JADE_BRIGHT = '#5eead4';
const JADE_COLOR = '#14b8a6';
const SEAL_COLOR = '#14b8a6';
const SHOW_ULTIMATE_SEALS = false;

const brushProfile = (u) => Math.pow(Math.sin(Math.PI * Math.pow(clamp(u), 0.72)), 0.78);
const whipProfile = (u) => Math.max(0.14, (1 - Math.pow(clamp(u), 1.45)) * (0.45 + 0.55 * Math.sin(Math.min(1, u * 4) * Math.PI * 0.5)));

function brushPoly(ctx, pts, wMax, rgb, alpha, profile = brushProfile) {
    const n = pts.length;
    if (n < 2 || alpha <= 0.008 || wMax <= 0.05) return;
    const left = [];
    const right = [];
    for (let i = 0; i < n; i++) {
        const a = pts[Math.max(0, i - 1)];
        const b = pts[Math.min(n - 1, i + 1)];
        let dx = b[0] - a[0];
        let dy = b[1] - a[1];
        const len = Math.hypot(dx, dy) || 1;
        dx /= len;
        dy /= len;
        const w = wMax * profile(i / (n - 1)) * 0.5;
        left.push([pts[i][0] - dy * w, pts[i][1] + dx * w]);
        right.push([pts[i][0] + dy * w, pts[i][1] - dx * w]);
    }
    ctx.globalAlpha = clamp(alpha);
    ctx.fillStyle = `rgb(${rgb})`;
    ctx.beginPath();
    ctx.moveTo(left[0][0], left[0][1]);
    for (let i = 1; i < n; i++) ctx.lineTo(left[i][0], left[i][1]);
    for (let i = n - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]);
    ctx.closePath();
    ctx.fill();
}

function drawSerpentSeal(ctx, cx, cy, chars, color, progress) {
    if (progress <= 0 || progress >= 1) return;
    const slam = progress < 0.18 ? mix(2.1, 1.0, ease(progress / 0.18)) : 1.0;
    const alpha = progress > 0.72 ? (1 - progress) / 0.28 : Math.min(1, progress / 0.12);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(slam, slam);
    ctx.rotate(-0.07);
    ctx.globalAlpha = clamp(alpha * 0.9);
    ctx.strokeStyle = color;
    ctx.fillStyle = 'rgba(15, 118, 110, 0.14)';
    ctx.lineWidth = 2.6;
    ctx.beginPath();
    ctx.rect(-24, -24, 48, 48);
    ctx.fill();
    ctx.stroke();

    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.strokeRect(-20, -20, 40, 40);

    ctx.fillStyle = color;
    ctx.font = 'bold 19px "STXingkai", "STKaiti", "KaiTi", serif';
    ctx.textAlign = 'center';
    ctx.fillText(chars[0] || '白', 0, -3);
    ctx.fillText(chars[1] || '蟒', 0, 17);
    ctx.restore();
}

function drawVenomDroplets(ctx, cx, cy, dir, progress, count, maxRadius, seedBase = 1, alphaScale = 1) {
    const p = clamp(progress);
    const fade = (1 - p) * alphaScale;
    if (fade <= 0.01) return;
    for (let j = 0; j < count; j++) {
        const a = j * 2.39996 + seedBase * 0.7 + dir * 0.25;
        const speed = (22 + seed(j * 13 + seedBase) * maxRadius) * ease(Math.min(1, p * 1.25));
        const x = cx + Math.cos(a) * speed;
        const y = cy + Math.sin(a) * speed * 0.78 + p * p * 26;
        const r = (1.8 + seed(j + 44 + seedBase) * 2.9) * (1 - p * 0.45);

        // Cyan-teal venom rim so milky-white droplets stand out crisply on pale rice paper
        ctx.globalAlpha = clamp(fade * 0.68);
        ctx.fillStyle = `rgb(${CYAN_DEEP_RGB})`;
        ctx.beginPath();
        ctx.ellipse(x, y, r * 1.95, r * 1.12, a, 0, Math.PI * 2);
        ctx.fill();

        // Creamy opaque milky-white venom core
        ctx.globalAlpha = clamp(fade * 0.96);
        ctx.fillStyle = j % 4 === 0 ? `rgb(${VENOM_MIST_RGB})` : `rgb(${VENOM_WHITE_RGB})`;
        ctx.beginPath();
        ctx.ellipse(x - Math.cos(a) * 0.35, y - Math.sin(a) * 0.35, r * 1.42, r * 0.76, a, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawProceduralInkPython(ctx, startX, startY, endX, endY, time, alpha, webEnhanced) {
    if (alpha <= 0.01) return;
    const dx = endX - startX;
    const dy = endY - startY;
    const len = Math.max(40, Math.hypot(dx, dy));
    const ang = Math.atan2(dy, dx);
    const pts = [];
    const bellyPts = [];
    const segs = 30;
    for (let i = 0; i <= segs; i++) {
        const u = i / segs;
        const sway = Math.sin(u * Math.PI * 3.0 - time * 0.013) * 24 * Math.sin(u * Math.PI) * (1 - u * 0.2);
        pts.push([u * len, sway]);
        bellyPts.push([u * len, sway + 4.0]);
    }
    ctx.save();
    ctx.translate(startX, startY);
    ctx.rotate(ang);
    const spineProfile = (u) => (0.24 + 0.76 * Math.sin(u * Math.PI * 0.88)) * (u > 0.86 ? 1 - (u - 0.86) * 3.0 : 1);
    // Cyan-teal outer venom aura & contour
    brushPoly(ctx, pts, 32, CYAN_DEEP_RGB, alpha * 0.38, spineProfile);
    brushPoly(ctx, pts, 21, CYAN_BRIGHT_RGB, alpha * 0.76, spineProfile);
    // Thick opaque milky-white venom python body
    brushPoly(ctx, pts, 14.5, VENOM_WHITE_RGB, alpha * 0.95, spineProfile);
    brushPoly(ctx, bellyPts, 6.8, VENOM_MIST_RGB, alpha * 0.88, spineProfile);
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, pts, 3.2, CYAN_GLOW_RGB, alpha * 0.48, spineProfile);
    ctx.globalCompositeOperation = 'source-over';

    const head = pts[pts.length - 1];
    ctx.translate(head[0], head[1]);
    // Cyan-teal head silhouette rim
    ctx.fillStyle = `rgb(${CYAN_DEEP_RGB})`;
    ctx.globalAlpha = clamp(alpha * 0.88);
    ctx.beginPath();
    ctx.moveTo(28, -1);
    ctx.quadraticCurveTo(7, -18, -25, -12);
    ctx.lineTo(-15, -2);
    ctx.lineTo(-25, 12);
    ctx.quadraticCurveTo(7, 17, 26, 4);
    ctx.closePath();
    ctx.fill();

    // Milky-white venom python head
    ctx.fillStyle = `rgb(${VENOM_WHITE_RGB})`;
    ctx.globalAlpha = clamp(alpha * 0.96);
    ctx.beginPath();
    ctx.moveTo(25, -1);
    ctx.quadraticCurveTo(6, -15, -22, -10);
    ctx.lineTo(-13, -2);
    ctx.lineTo(-22, 10);
    ctx.quadraticCurveTo(6, 14, 23, 3);
    ctx.closePath();
    ctx.fill();

    // Pearlescent white fangs & venom spray
    ctx.fillStyle = '#ffffff';
    ctx.globalAlpha = clamp(alpha * 0.94);
    ctx.beginPath();
    ctx.moveTo(18, -3);
    ctx.lineTo(13, 6);
    ctx.lineTo(10, -2);
    ctx.closePath();
    ctx.fill();

    // Glowing cyan-white venom tongue & jade eye
    ctx.strokeStyle = JADE_BRIGHT;
    ctx.lineWidth = 1.6;
    ctx.globalAlpha = clamp(alpha * 0.92);
    ctx.beginPath();
    ctx.moveTo(22, 2);
    ctx.lineTo(36, 3);
    ctx.lineTo(44, -2);
    ctx.moveTo(36, 3);
    ctx.lineTo(44, 8);
    ctx.stroke();

    ctx.fillStyle = `rgb(${CYAN_DEEP_RGB})`;
    ctx.beginPath();
    ctx.ellipse(4, -5, 4.0, 2.1, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ecfeff';
    ctx.beginPath();
    ctx.ellipse(4.4, -5, 2.2, 1.1, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
}

export function serpentMotion(event, time, travel, webEnhanced = false) {
    const i = names.indexOf(event.move);
    if (i < 0) return;
    const prep = ease((time - 160) / 340);
    const go = ease((time - 480) / 460);
    const lash = snap(time, 520, 260, 2.7);
    const back = ease((time - end(i)) / 340);
    const active = prep * (1 - back);
    const strike = clamp((time - 520) / 430);
    const snapSin = Math.sin(strike * Math.PI);
    const pull = ease((time - 950) / 260) * (1 - back);

    let x = Math.max(0, travel - 140) * go * (1 - back);
    let lift = 0;
    let lean = -18 * prep + 42 * lash - 23 * pull;
    let h = 68;
    let gx = 24 + 52 * lash - 44 * pull;
    let gy = -108;
    let angle = -0.12;

    if (i === 0) {
        gx += Math.sin(strike * Math.PI * 4) * 14 * snapSin;
        lean += snapSin * 5;
    }
    if (i === 1) {
        gy = -100 + Math.sin(strike * Math.PI * 2) * 26;
        gx -= pull * 26;
        lean -= pull * 16;
    }
    if (i === 2) {
        h = 47 + 20 * go;
        gy = -55 - 60 * go;
        angle = 0.65 - 1.2 * go;
        lean = 14 * active;
    }
    if (i === 3) {
        const b = beat(i, time);
        gx = 12 + 62 * b;
        gy = -96 - 20 * (1 - b);
        lean = -22 + 49 * b;
        x -= 25 * (1 - b) * active;
    }
    if (i === 4) {
        const a = ((time - 600) / 310) * Math.PI * 2;
        gx = 24 - Math.cos(a) * 48 * active;
        gy = -112 + Math.sin(a) * 43 * active;
        lean = -Math.cos(a) * 29 * active;
        h = 55;
    }
    if (i === 5) {
        const b = beat(i, time);
        gx = 15 + 49 * b;
        gy = -155 + 38 * b;
        lean = -14 + 29 * b;
    }
    if (i === 6) {
        const squeeze = ease((time - 950) / 230) * 0.5 + ease((time - 1270) / 240) * 0.5;
        const twist = Math.sin(clamp((time - 1510) / 350) * Math.PI);
        gx = 55 * go - 55 * squeeze;
        gy = -102 + squeeze * 18 - twist * 25;
        h = 52;
        lean = 22 * go - 47 * squeeze;
        x -= twist * 28;
    }
    if (i === 7) {
        lift = -94 * Math.sin(Math.PI * clamp((time - 400) / 900));
        gx = 24 + 50 * lash - 22 * pull;
        gy = -134 + 26 * lash;
        lean = -14 * prep * (1 - lash) + 26 * lash - 18 * pull;
        h = 70;
        x += 45 * go * (1 - back);
    }
    if (webEnhanced && i >= 3 && i <= 5) {
        const cast = snap(time, 430, 340, 2.5);
        const follow = ease((time - 850) / 260);
        const retract = ease((time - 1130) / 320);
        gx = mix(-10, i === 4 ? 68 : 60, cast) - retract * 24;
        gy = mix(i === 5 ? -145 : -120, i === 4 ? -76 : -96, cast) + follow * 8;
        lean = mix(-18, i === 4 ? 25 : 19, cast) - retract * 12;
        h = i === 4 ? 61 : 68;
    }

    lean *= 1 - back;
    h = mix(74, h, active);
    gx = mix(34, gx, active);
    gy = mix(-105, gy, active);
    lean = Math.max(-38, Math.min(38, lean));

    const hip = [0, -h];
    const neck = [lean, -h - Math.sqrt(2704 - lean * lean)];
    const shoulders = [[neck[0] - 10, neck[1] + 6], [neck[0] + 10, neck[1] + 6]];
    const [fe, fh] = twoBone(shoulders[1], [gx, gy], 40, 1);
    const [be, bh] = twoBone(shoulders[0], [-35 - 20 * active, -90 + 25 * active], 40, -1);
    const stride = 34 + 18 * active;
    const feet = lift < -8 ? [[-34, -25], [31, -32]] : [[-stride, 0], [stride, 0]];
    const [bk, bf] = twoBone(hip, feet[0], 48, -1);
    const [fk, ff] = twoBone(hip, feet[1], 48, -1);
    const target = [travel + 165 - x, -95 - lift];
    const points = whipPath(i, time, fh, target, active);
    return {
        x,
        lift,
        opacity: 1,
        blink: 0,
        pose: { points: [[neck[0], neck[1] - 21], neck, hip, be, bh, fe, fh, bk, bf, fk, ff], shoulders, sword: angle, lean: 0, whip: points },
    };
}

function whipPath(i, time, hand, target, active) {
    const launch = ease((time - 470) / 460);
    const pull = ease((time - 980) / 270);
    const recover = ease((time - end(i)) / 340);
    const reach = launch * (1 - recover) * (i >= 3 && i <= 5 ? 0.48 + 0.52 * beat(i, time) : 1);
    const tx = mix(hand[0] + 110, target[0], reach);
    const ty = mix(hand[1] + 55, target[1], reach);
    const pts = [];
    for (let j = 0; j <= 90; j++) {
        const u = j / 90;
        const s = Math.sin(Math.PI * u);
        let x = mix(hand[0], tx, u);
        let y = mix(hand[1], ty, u);
        if (i === 0) {
            y += Math.sin(u * 10 - time * 0.017) * s * 22 * (1 - launch * 0.7);
            x -= Math.sin(u * Math.PI) * 20 * (1 - launch);
        }
        if (i === 1 || i === 6 || i === 7) {
            const start = i === 1 ? 0.66 : 0.43;
            if (u > start) {
                const v = (u - start) / (1 - start);
                const turns = i === 1 ? 1.25 : i === 6 ? 2.7 : 3.2;
                const r = (i === 1 ? 31 : i === 7 ? 92 : 75) * (1 - (i === 6 ? 0.28 * ease((time - 950) / 230) + 0.36 * ease((time - 1270) / 240) : pull * 0.45)) * reach;
                const a = v * Math.PI * 2 * turns - (i === 6 ? ease((time - 1510) / 350) * Math.PI * 1.7 : time * 0.002);
                const f = ease(v / 0.18);
                x = mix(x, tx + Math.cos(a) * r, f);
                y = mix(y, ty + Math.sin(a) * r * 0.48 + (i === 1 ? 0 : (v - 0.5) * 106), f);
            } else {
                y -= s * 45 * active;
            }
        }
        if (i === 2) {
            const a = u * Math.PI * 7 - time * 0.003;
            x += Math.sin(a) * s * 45 * launch;
            y = mix(hand[1], -2, u) + Math.cos(a) * s * 18 - launch * u * 125;
        }
        if (i === 3) {
            y += s * Math.sin(u * 8) * 20;
            x -= pull * s * 55;
        }
        if (i === 4) {
            y += Math.sin(u * Math.PI * 3 - time * 0.012) * s * 95 * active;
        }
        if (i === 5) {
            y -= s * 135 * active;
            y += Math.sin(u * 34 - time * 0.065) * s * 13 * active;
        }
        pts.push([x, y]);
    }
    for (let pass = 0; pass < 2; pass++) {
        const old = pts.map((p) => [...p]);
        for (let j = 1; j < pts.length - 1; j++) {
            pts[j] = old[j].map((v, k) => (old[j - 1][k] + 2 * v + old[j + 1][k]) / 4);
        }
    }
    return pts;
}

export function inkPythonPath(time, hand, target) {
    const launch = ease((time - 430) / 470);
    const coil = ease((time - 700) / 350);
    const tighten = ease((time - 950) / 320);
    const recover = ease((time - 1340) / 340);
    const reach = launch * (1 - recover);
    const tx = mix(hand[0] + 100, target[0], reach);
    const ty = mix(hand[1] + 45, target[1], reach);
    const radius = mix(74, 47, tighten);
    const pts = [];
    for (let j = 0; j <= 90; j++) {
        const u = j / 90;
        const s = Math.sin(Math.PI * u);
        const straightX = mix(hand[0], tx, u);
        const straightY = mix(hand[1], ty, u) - s * 30 * reach;
        let x = straightX;
        let y = straightY + Math.sin(u * 7 - time * 0.006) * s * 18 * reach * (1 - coil);
        if (u > 0.52) {
            const v = (u - 0.52) / 0.48;
            const a = -Math.PI * 0.8 + v * Math.PI * 2.7;
            const blend = coil * ease(v / 0.18);
            x = mix(x, tx + Math.cos(a) * radius, blend);
            y = mix(y, ty + Math.sin(a) * radius * 0.48 + (v - 0.5) * 62, blend);
        }
        pts.push([x, y]);
    }
    return pts;
}

export function inkWhipPath(move, time, hand, target) {
    const i = names.indexOf(move);
    if (i === 7) return inkPythonPath(time, hand, target);
    const cast = ease((time - 400) / 470);
    const recover = ease((time - end(i)) / 340);
    const active = cast * (1 - recover);
    const tx = mix(hand[0] + 95, target[0], active);
    const ty = mix(hand[1] + 45, target[1], active);
    const loop = ease((time - 650) / 400) * (1 - recover);
    const tighten = ease((time - 980) / 400);
    const pts = [];
    const amp = [28, 28, 48, 38, 65, 30, 30][i] || 28;
    for (let j = 0; j <= 90; j++) {
        const u = j / 90;
        const delay = ease((time - 350 - u * 240) / 420);
        const envelope = Math.sin(Math.PI * u);
        const x = mix(hand[0], tx, u);
        const baseY = mix(hand[1], ty, u);
        let px = x;
        let py = baseY + Math.sin(u * 8 - time * 0.009) * envelope * amp * active * (1 - 0.65 * delay);
        py -= envelope * amp * 0.55 * active;
        if (i === 2) {
            const spiral = u * 12 - time * 0.006;
            py = mix(py, mix(hand[1], ty + 55 - u * 95, u), active) + Math.cos(spiral) * envelope * 17 * active;
            px += Math.sin(spiral) * envelope * 29 * active;
        }
        if (i === 3 || i === 5) {
            const cycle = ((time - 500) / (i === 3 ? 310 : 180)) * Math.PI * 2;
            px -= u * active * (i === 3 ? 32 : 16) * (0.5 + 0.5 * Math.sin(cycle));
            py += Math.sin(cycle - u * 5) * envelope * active * (i === 3 ? 22 : 14);
        }
        if ((i === 1 || i === 6) && u > 0.56) {
            const v = (u - 0.56) / 0.44;
            const a = -Math.PI * 0.85 + v * Math.PI * (i === 6 ? 3 : 2.2);
            const r = (i === 6 ? 65 : 30) * (1 - tighten * (i === 6 ? 0.35 : 0.15));
            const f = loop * ease(v / 0.2);
            px = mix(px, tx + Math.cos(a) * r, f);
            py = mix(py, ty + Math.sin(a) * r * 0.48 + (v - 0.5) * (i === 6 ? 55 : 15), f);
        }
        pts.push([px, py]);
    }
    return pts;
}

export function drawSerpentWhip(ctx, pts) {
    if (!pts || pts.length < 2) return;
    ctx.save();
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    const first = pts[0];
    const next = pts[1];
    if (first && next) {
        const a = Math.atan2(next[1] - first[1], next[0] - first[0]);
        ctx.strokeStyle = '#115e59';
        ctx.lineWidth = 4.6;
        ctx.beginPath();
        ctx.moveTo(first[0] - Math.cos(a) * 23, first[1] - Math.sin(a) * 23);
        ctx.lineTo(first[0] + Math.cos(a) * 2, first[1] + Math.sin(a) * 2);
        ctx.stroke();
    }
    // Cyan-teal whip body + milky-white venom sheen
    brushPoly(ctx, pts, 4.4, CYAN_DEEP_RGB, 0.94, whipProfile);
    brushPoly(ctx, pts, 2.8, CYAN_BRIGHT_RGB, 0.88, whipProfile);
    brushPoly(ctx, pts, 1.35, VENOM_WHITE_RGB, 0.86, whipProfile);
    ctx.restore();
}

export function serpentEffects(ctx, event, time, sampleAt, target, dir, impactAge, hit, webEnhanced = false) {
    const i = names.indexOf(event.move);
    if (i < 0 || time < 360 || time > 2660) return;
    const fade = 1 - ease((time - end(i)) / 440);
    const grow = ease((time - 360) / 220);
    const alpha = fade * grow;
    const world = (t) => {
        const f = sampleAt(t).frame;
        if (!f?.pose.whip) return [];
        return f.pose.whip.map((p) => [f.x + dir * p[0], 324 + f.lift + p[1]]);
    };
    const pts = world(time);
    if (pts.length < 2) return;
    const handOrigin = pts[0];
    const tip = pts[pts.length - 1];
    const prev = pts[Math.max(0, pts.length - 3)];
    const ang = Math.atan2(tip[1] - prev[1], tip[0] - prev[0]);

    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // 1. Pre-strike cyan + milky-white venom gather around whip hand (360~660ms)
    if (time <= 660) {
        const gatherP = ease((time - 360) / 220) * (1 - ease((time - 560) / 100));
        if (gatherP > 0.01) {
            for (let k = 0; k < 8; k++) {
                const ga = k * 2.399 + time * 0.0055;
                const r = (1 - clamp((time - 380) / 260)) * 38 + 6;
                const gx = handOrigin[0] + Math.cos(ga) * r;
                const gy = handOrigin[1] + Math.sin(ga) * r;
                ctx.globalAlpha = gatherP * 0.65;
                ctx.strokeStyle = k % 2 === 0 ? JADE_COLOR : `rgb(${VENOM_WHITE_RGB})`;
                ctx.lineWidth = k % 2 === 0 ? 2.0 : 1.5;
                ctx.beginPath();
                ctx.moveTo(gx, gy);
                ctx.lineTo(handOrigin[0] + Math.cos(ga) * r * 0.38, handOrigin[1] + Math.sin(ga) * r * 0.38);
                ctx.stroke();

                // Milky-white venom bead at the outer tip
                ctx.fillStyle = `rgb(${VENOM_WHITE_RGB})`;
                ctx.beginPath();
                ctx.arc(gx, gy, 1.7, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }

    // 3. Cyan Whip Energy Spine + Creamy White Venom Stream
    const inkPython = i === 7 && webEnhanced && pythonHead?.complete && pythonHead.naturalWidth;
    brushPoly(ctx, pts, i === 7 ? 15 : 10.5, CYAN_DEEP_RGB, alpha * (inkPython ? 0.32 : 0.56), whipProfile);
    brushPoly(ctx, pts, i === 7 ? 8.5 : 6.0, CYAN_BRIGHT_RGB, alpha * (inkPython ? 0.38 : 0.68), whipProfile);
    brushPoly(ctx, pts, i === 7 ? 4.8 : 3.2, VENOM_WHITE_RGB, alpha * 0.88, whipProfile);
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, pts, 2.0, CYAN_GLOW_RGB, alpha * 0.42, whipProfile);
    ctx.globalCompositeOperation = 'source-over';

    // 4. Ultimate White Venom Python Apparition (绝技·白蟒索命)
    if (i === 7) {
        const surgeP = clamp((time - 450) / 480);
        const span = Math.max(220, Math.abs(target[0] - handOrigin[0]) + (hit ? 80 : 145));
        const dx = target[0] - handOrigin[0];
        const dy = target[1] - handOrigin[1];
        const aimAng = Math.atan2(dy, Math.max(40, Math.abs(dx)));
        const pythonW = Math.min(430, span * 1.12);
        const pythonH = pythonW * 0.50;
        const headTravel = 68 + ease(surgeP) * (span - 14) + clamp((time - 960) / 480) * 46;

        if (inkPython) {
            // Cyan-teal venom mist underlay + milky-white venom core ribbon so the white python pops on all themes
            ctx.save();
            const ribPts = [];
            const ribMax = Math.min(span, headTravel - 16);
            for (let k = 0; k <= 16; k++) {
                const u = k / 16;
                ribPts.push([
                    mix(handOrigin[0], handOrigin[0] + dir * ribMax, u),
                    mix(handOrigin[1], target[1], u * 0.75) + Math.sin(u * 7.5 - time * 0.015) * 14 * Math.sin(u * Math.PI),
                ]);
            }
            brushPoly(ctx, ribPts, 22, CYAN_DEEP_RGB, alpha * 0.28);
            brushPoly(ctx, ribPts, 8.5, VENOM_WHITE_RGB, alpha * 0.52);
            if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
            brushPoly(ctx, ribPts, 3.8, CYAN_GLOW_RGB, alpha * 0.34);
            ctx.restore();

            drawStripSlicedImage(ctx, pythonHead, handOrigin[0] - dir * 10, handOrigin[1] - 6, pythonW, pythonH, {
                slices: 30,
                amp: 11,
                freq: 7.8,
                phase: time * 0.015,
                dir,
                angle: aimAng,
                alpha: alpha * 0.98,
                reveal: 0.35 + surgeP * 0.65,
                travelOffset: headTravel,
                rigidFrom: 0.62,
                clipMinX: -12,
                clipMaxX: span + 95,
            });

            // Trailing milky-white venom droplets spraying along the surging python jaws
            const jawX = handOrigin[0] + dir * Math.min(span + 24, headTravel * 0.92);
            const jawY = mix(handOrigin[1], target[1], ease(surgeP));
            drawVenomDroplets(ctx, jawX, jawY, dir, surgeP * 0.75, 9, 44, 71, alpha * 0.82);
        } else {
            const endX = handOrigin[0] + dir * Math.min(span + 35, headTravel);
            const endY = mix(handOrigin[1], target[1], ease(surgeP));
            drawProceduralInkPython(ctx, handOrigin[0], handOrigin[1], endX, endY, time, alpha, webEnhanced);
        }
    }

    // 5. Whip Lash Cyan+White-Venom Texture & Multi-Strand Trails ([0, 3, 4, 5])
    if (webEnhanced && whipSweep?.complete && whipSweep.naturalWidth && [0, 3, 4, 5].includes(i)) {
        const pulse = ease((time - 510) / 120) * (1 - ease((time - end(i) + 180) / 280));
        const startPt = pts[Math.floor(pts.length * 0.22)];
        const lashDx = tip[0] - startPt[0];
        const lashDy = tip[1] - startPt[1];
        const lashLen = Math.max(120, Math.hypot(lashDx, lashDy) + 34);
        const lashAng = Math.atan2(lashDy, Math.max(20, Math.abs(lashDx)));
        drawStripSlicedImage(ctx, whipSweep, startPt[0], startPt[1], lashLen, 84, {
            slices: 22,
            amp: 5.5,
            freq: 6.8,
            phase: time * 0.017,
            dir,
            angle: lashAng,
            alpha: alpha * pulse * 0.92,
            reveal: 0.55 + 0.45 * clamp((time - 510) / 260),
            travelOffset: lashLen - 12,
            rigidFrom: 0.84,
            featherRight: 0.08,
        });
    }

    if (i === 4 || i === 5) {
        const count = i === 5 ? 9 : 7;
        for (let j = 1; j <= count; j++) {
            const past = world(time - j * 14);
            if (past.length < 2) continue;
            const off = i === 5 ? (j - count / 2) * 8 : 0;
            const shifted = past.map((p, k) => [p[0], p[1] + Math.sin((k / 90) * Math.PI) * off]);
            brushPoly(
                ctx,
                shifted,
                i === 5 ? 2.2 : 3.0,
                j % 2 ? CYAN_BRIGHT_RGB : VENOM_WHITE_RGB,
                alpha * (1 - j / (count + 1)) * 0.52,
                whipProfile,
            );
        }
    }

    // 6. Coiling Cyan & White-Venom Vortex Rings on [1, 2, 6]
    if (i === 1 || i === 2 || i === 6) {
        const tighten = i === 6 ? ease((time - 940) / 400) * 0.38 : 0;
        const ringCount = i === 2 ? 4 : 3;
        for (let k = 0; k < ringCount; k++) {
            const r = ((i === 6 ? 62 : i === 2 ? 78 - k * 12 : 38) * (1 - tighten));
            const ry = i === 2 ? 322 - k * 34 * ease((time - 460) / 420) : target[1] + (k - 1) * 18;
            // Cyan-teal outer ring
            ctx.globalAlpha = clamp(alpha * (0.54 - k * 0.09));
            ctx.strokeStyle = JADE_COLOR;
            ctx.lineWidth = 2.8;
            ctx.beginPath();
            ctx.ellipse(target[0], ry, Math.max(8, r), Math.max(4, r * 0.24), 0.1 * dir, 0, Math.PI * 2);
            ctx.stroke();

            // Milky-white venom inner ring
            ctx.globalAlpha = clamp(alpha * (0.72 - k * 0.11));
            ctx.strokeStyle = `rgb(${VENOM_WHITE_RGB})`;
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            ctx.ellipse(target[0], ry - 1, Math.max(7, r * 0.96), Math.max(3.5, r * 0.22), 0.1 * dir, 0, Math.PI * 2);
            ctx.stroke();
        }
    }

    // 7. Ambient fine milky-white venom droplets & cyan mist along whip flight
    for (let j = 0; j < (i === 4 ? 28 : 16); j++) {
        const age = time - 520 - j * 28;
        if (age < 0 || age > 620) continue;
        const p = age / 620;
        const source = world(520 + j * 28);
        if (!source.length) continue;
        const o = source[source.length - 1];
        const px = o[0] - dir * p * (10 + seed(j) * 34);
        const py = o[1] + p * p * 56;
        const rx = 1.4 + seed(j + 9) * 1.7;
        const ry = 2.1 + p * 2.2;

        // Cyan rim
        ctx.globalAlpha = (1 - p) * alpha * 0.52;
        ctx.fillStyle = JADE_COLOR;
        ctx.beginPath();
        ctx.ellipse(px, py, rx * 1.35, ry * 1.25, -p, 0, Math.PI * 2);
        ctx.fill();

        // Creamy white venom droplet core
        ctx.globalAlpha = (1 - p) * alpha * 0.88;
        ctx.fillStyle = `rgb(${VENOM_WHITE_RGB})`;
        ctx.beginPath();
        ctx.ellipse(px, py, rx * 0.95, ry * 0.88, -p, 0, Math.PI * 2);
        ctx.fill();
    }

    // 8. Hit-Confirmed Milky-White Venom Splash Burst (STRICTLY omitted on dodge!)
    if (hit && impactAge >= 0 && impactAge < 640) {
        const p = impactAge / 640;
        const ringAlpha = (1 - p) * 0.92;
        const dropCount = i === 7 ? 24 : i >= 4 ? 16 : 12;
        drawVenomDroplets(ctx, target[0], target[1], dir, p, dropCount, i === 7 ? 118 : 78, event.action || 1, 1);

        const rings = i === 7 ? 3 : 2;
        for (let rIdx = 0; rIdx < rings; rIdx++) {
            const rad = 14 + p * (52 + rIdx * 24);
            ctx.globalAlpha = ringAlpha * (0.48 - rIdx * 0.12);
            ctx.strokeStyle = rIdx % 2 === 0 ? `rgb(${VENOM_WHITE_RGB})` : JADE_COLOR;
            ctx.lineWidth = (i === 7 ? 2.2 : 1.4) * (1 - p);
            ctx.beginPath();
            ctx.ellipse(target[0], target[1], rad * 0.76, rad, 0.16 * dir, 0, Math.PI * 2);
            ctx.stroke();
        }

        if (i === 7 && SHOW_ULTIMATE_SEALS) {
            drawSerpentSeal(ctx, target[0] + dir * 56, target[1] - 24, '白蟒', SEAL_COLOR, p);
        }
    }

    ctx.restore();
}

export const serpentTime = (t, c = 950) => (t <= c ? (t * 950) / Math.max(1, c) : 950 + (t - c) / 0.43);
export const serpentReplayTime = (t, c = 950) => (t <= 950 ? (t * Math.max(1, c)) / 950 : c + (t - 950) * 0.43);
