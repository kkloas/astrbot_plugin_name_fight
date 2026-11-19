import { twoBone } from './sampleMotion.js';
import { ease } from './choreography.js';

const clamp = (x) => Math.max(0, Math.min(1, x));
const smooth = (x) => { const v = clamp(x); return v * v * (3 - 2 * v); };
const mix = (a, b, t) => a + (b - a) * t;
const snap = (t, start, dur, power = 3.2) => 1 - Math.pow(1 - clamp((t - start) / Math.max(1, dur)), power);
const seed = (n) => {
    const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
    return x - Math.floor(x);
};

const m = (name, style, power, angle, lift = 0, strokes = 1, ranged = false, signature = false) => ({
    name,
    style,
    power,
    angle,
    lift,
    strokes,
    ranged,
    signature,
    ultimate: name.startsWith('绝技'),
});

export const xianglongArt = {
    name: '降龙十八掌',
    type: 'palm',
    weapon: 'unarmed',
    ink: '#211b14',
    glow: '#d97706',
    glowBright: '#fbbf24',
    sealColor: '#b45309',
    sash: '#92400e',
    sashHighlight: '#f59e0b',
    moves: [
        m('见龙在田', 'dragon_field', 0.92, 0.0),
        m('潜龙勿用', 'dragon_coiled', 0.96, -0.35),
        m('神龙摆尾', 'dragon_tail', 1.02, 0.15, 10),
        m('双龙取水', 'twin_dragons', 1.08, 0.0, 12, 2),
        m('震惊百里', 'dragon_quake', 1.14, 0.25, 22, 1, true, true),
        m('突如其来', 'dragon_dash', 1.18, 0.05, 8),
        m('飞龙在天', 'dragon_sky', 1.34, 0.55, 96, 1, false, true),
        m('绝技·亢龙有悔', 'domain_dragon', 1.48, 0.0, 0, 1, true, true),
    ],
};

const xianglongAssets = typeof Image === 'undefined' ? {} : Object.fromEntries(
    ['dragon-surge', 'palm-burst', 'ground-quake'].map((name) => {
        const image = new Image();
        image.src = new URL(`./assets/ink-${name}.png`, import.meta.url).href;
        return [name, image];
    }),
);

export function waitForXianglongAssets() {
    const imgs = Object.values(xianglongAssets).filter(Boolean);
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

const SHOW_ULTIMATE_SEALS = false;
const INK_RGB = '28,31,33';
const hexRgb = (hex) => {
    const h = String(hex).replace('#', '');
    return `${parseInt(h.slice(0, 2), 16) || 0},${parseInt(h.slice(2, 4), 16) || 0},${parseInt(h.slice(4, 6), 16) || 0}`;
};
const brushProfile = (u) => Math.pow(Math.sin(Math.PI * Math.pow(clamp(u), 0.75)), 0.8);

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

function arcPts(r, a0, a1, n, key) {
    const pts = [];
    for (let i = 0; i <= n; i++) {
        const rr = r + (seed(key + i * 3.7) - 0.5) * 1.4;
        const ang = mix(a0, a1, i / n);
        pts.push([Math.cos(ang) * rr, Math.sin(ang) * rr]);
    }
    return pts;
}

function drawInkShockArc(ctx, cx, cy, radius, angle, span, thickness, glowColor, alpha, webEnhanced) {
    if (alpha <= 0.01 || radius <= 2) return;
    const key = Math.round(angle * 10) * 7 + Math.round(span * 10);
    const rgbGlow = hexRgb(glowColor);
    const a0 = -span * 0.5;
    const a1 = span * 0.5;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(angle);
    for (let k = 0; k < 3; k++) {
        brushPoly(ctx, arcPts(radius + (k - 1) * thickness * 0.28, a0 + span * 0.05, a1, 14, key + k), thickness * (1 - k * 0.16), INK_RGB, alpha * 0.07);
    }
    for (let k = 0; k < 9; k++) {
        const t = k / 8;
        const centered = 1 - Math.abs(t - 0.5) * 2;
        const r = radius + (t - 0.5) * thickness * 1.05;
        const s0 = a0 + span * 0.08 * seed(key + k * 3);
        const s1 = a1 - span * 0.18 * seed(key + k * 5 + 1);
        const w = 1.0 + centered * 2.6;
        const a = alpha * (0.18 + centered * 0.34);
        const rgb = k % 4 === 1 ? rgbGlow : INK_RGB;
        if (k % 2) {
            const gs = mix(s0, s1, 0.44 + 0.1 * seed(key + k));
            const ge = gs + (s1 - s0) * 0.08;
            brushPoly(ctx, arcPts(r, s0, gs, 8, key + k), w, rgb, a);
            brushPoly(ctx, arcPts(r, ge, s1, 8, key + k + 40), w, rgb, a);
        } else {
            brushPoly(ctx, arcPts(r, s0, s1, 12, key + k), w, rgb, a);
        }
    }
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, arcPts(radius, a0 * 0.8, a1 * 0.9, 14, key + 90), webEnhanced ? 2.2 : 1.5, rgbGlow, alpha * (webEnhanced ? 0.32 : 0.24));
    ctx.restore();
}

function drawDragonSeal(ctx, cx, cy, chars, color, progress) {
    if (progress <= 0 || progress >= 1) return;
    const slam = progress < 0.18 ? mix(2.15, 1.0, ease(progress / 0.18)) : 1.0;
    const alpha = progress > 0.72 ? (1 - progress) / 0.28 : Math.min(1, progress / 0.12);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(slam, slam);
    ctx.rotate(-0.07);
    ctx.globalAlpha = clamp(alpha * 0.9);
    ctx.strokeStyle = color;
    ctx.fillStyle = 'rgba(180, 83, 9, 0.16)';
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
    ctx.fillText(chars[0] || '亢', 0, -3);
    ctx.fillText(chars[1] || '龙', 0, 17);
    ctx.restore();
}

export function drawStripSlicedImage(ctx, img, originX, originY, drawW, drawH, opts = {}) {
    if (!img?.complete || !img.naturalWidth || !img.naturalHeight || drawW <= 1 || drawH <= 1) return;
    const {
        slices = 28,
        amp = 0,
        freq = 7.5,
        phase = 0,
        dir = 1,
        angle = 0,
        alpha = 1,
        reveal = 1,
        travelOffset = 0,
        rigidFrom = 1,
        featherRight = 0,
        clipMinX = -Infinity,
        clipMaxX = Infinity,
    } = opts;
    if (alpha <= 0.01 || reveal <= 0.01) return;

    const imgW = img.naturalWidth;
    const imgH = img.naturalHeight;
    const count = Math.max(4, Math.min(48, Math.round(slices)));
    const headX = travelOffset - (1 - clamp(reveal)) * drawW * 0.35;
    const startX = headX - drawW;
    const rigidU = clamp(rigidFrom);
    const waveAt = (u) => {
        if (!amp || u >= rigidU) return 0;
        const t = u / Math.max(0.01, rigidU);
        const envelope = Math.sin(t * Math.PI) * (1 - t);
        return Math.sin(u * freq - phase) * amp * envelope;
    };

    ctx.save();
    ctx.translate(originX, originY);
    ctx.scale(dir >= 0 ? 1 : -1, 1);
    if (angle) ctx.rotate(angle);
    if (Number.isFinite(clipMinX) || Number.isFinite(clipMaxX)) {
        const minX = Number.isFinite(clipMinX) ? clipMinX : -drawW * 2;
        const maxX = Number.isFinite(clipMaxX) ? clipMaxX : drawW * 2;
        ctx.beginPath();
        ctx.rect(minX, -drawH * 1.4, Math.max(1, maxX - minX), drawH * 2.8);
        ctx.clip();
    }

    const bodySlices = rigidU < 0.99 ? Math.max(4, Math.round(count * rigidU)) : count;
    for (let i = 0; i < bodySlices; i++) {
        const u0 = (i / bodySlices) * rigidU;
        const u1 = ((i + 1) / bodySlices) * rigidU;
        const uMid = (u0 + u1) * 0.5;
        const sx = u0 * imgW;
        const sw = Math.max(0.5, (u1 - u0) * imgW);
        const dx = startX + u0 * drawW;
        const dw = (u1 - u0) * drawW;
        if (sx + sw > imgW + 0.1 || dw <= 0.1) continue;

        const wave = waveAt(uMid);
        let edgeFade = uMid < 0.1 ? uMid / 0.1 : 1;
        if (featherRight > 0 && uMid > 1 - featherRight) {
            edgeFade *= clamp((1 - uMid) / featherRight);
        }
        ctx.globalAlpha = clamp(alpha * edgeFade);
        ctx.drawImage(img, sx, 0, Math.min(sw, imgW - sx), imgH, dx, -drawH * 0.5 + wave, dw, drawH);
    }

    if (rigidU < 0.99) {
        const sx = rigidU * imgW;
        const sw = imgW - sx;
        const dx = startX + rigidU * drawW;
        const dw = (1 - rigidU) * drawW;
        if (sw > 0.5 && dw > 0.5) {
            ctx.globalAlpha = clamp(alpha);
            ctx.drawImage(img, sx, 0, sw, imgH, dx, -drawH * 0.5, dw, drawH);
        }
    }
    ctx.restore();
}

function drawProceduralInkDragon(ctx, startX, startY, endX, endY, time, alpha, glowColor, webEnhanced) {
    if (alpha <= 0.01) return;
    const dx = endX - startX;
    const dy = endY - startY;
    const len = Math.max(40, Math.hypot(dx, dy));
    const ang = Math.atan2(dy, dx);
    const pts = [];
    const bellyPts = [];
    const segs = 28;
    for (let i = 0; i <= segs; i++) {
        const u = i / segs;
        const sway = Math.sin(u * Math.PI * 2.6 - time * 0.014) * 24 * Math.sin(u * Math.PI) * (1 - u * 0.25);
        pts.push([u * len, sway]);
        bellyPts.push([u * len, sway + 5]);
    }
    ctx.save();
    ctx.translate(startX, startY);
    ctx.rotate(ang);
    const spineProfile = (u) => (0.28 + 0.72 * Math.sin(u * Math.PI * 0.88)) * (u > 0.85 ? 1 - (u - 0.85) * 3.2 : 1);
    brushPoly(ctx, pts, 32, INK_RGB, alpha * 0.28, spineProfile);
    brushPoly(ctx, pts, 17, INK_RGB, alpha * 0.78, spineProfile);
    brushPoly(ctx, bellyPts, 5.2, '235,222,196', alpha * 0.34, spineProfile);
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, pts, 3.6, hexRgb(glowColor), alpha * 0.62, spineProfile);
    ctx.globalCompositeOperation = 'source-over';

    const head = pts[pts.length - 1];
    ctx.translate(head[0], head[1]);
    ctx.fillStyle = `rgb(${INK_RGB})`;
    ctx.globalAlpha = clamp(alpha * 0.92);
    ctx.beginPath();
    ctx.moveTo(24, 0);
    ctx.quadraticCurveTo(5, -16, -24, -12);
    ctx.lineTo(-15, -2);
    ctx.lineTo(-26, 10);
    ctx.quadraticCurveTo(5, 15, 24, 2);
    ctx.closePath();
    ctx.fill();

    ctx.strokeStyle = '#f5d08a';
    ctx.lineWidth = 1.6;
    ctx.globalAlpha = clamp(alpha * 0.78);
    ctx.beginPath();
    ctx.moveTo(-8, -10);
    ctx.quadraticCurveTo(-25, -24, -40, -20);
    ctx.moveTo(6, -3);
    ctx.quadraticCurveTo(-9, 13, -28, 17);
    ctx.stroke();

    ctx.fillStyle = '#fde68a';
    ctx.beginPath();
    ctx.ellipse(6, -4, 3.5, 1.8, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
}

export function xianglongMotion(event, time, travel, dodged = false) {
    const move = xianglongArt.moves.find((item) => item.name === event?.move);
    if (!move) return undefined;

    // 4-phase crisp cadence: slow grounded windup (0-600ms) -> steep snap (600-780ms)
    // -> extended impact hold (780-1140ms) -> grounded recovery (1160-1700ms).
    const prep = smooth((time - 80) / 380);
    const snapIn = snap(time, 600, 185, 3.2);
    const settle = clamp((time - 785) / 165);
    const follow = clamp((time - 950) / 200);
    const recover = ease((time - 1170) / 480);
    const active = prep * (1 - recover);

    const launch = smooth((time - 420) / 420);
    let progress = launch * (1 - recover);
    let lift = 0;
    let opacity = 1;
    let blink = 0;
    let facing = 1;
    let roll = 0;

    let height = 74;
    let lean = -12 * prep + 24 * snapIn;
    // Hand targets in local shoulder space offsets (always clamped cleanly by twoBone).
    let frontOff = [mix(26, 70, snapIn), mix(18, -4, snapIn)];
    let rearOff = [mix(-20, -40, active), mix(20, 8, active)];

    switch (move.style) {
        case 'dragon_field': {
            // Sinking horse stance, left bracing palm, right heavy flat palm push.
            height = mix(74, 59, active);
            lean = -10 * prep * (1 - snapIn) + 23 * snapIn;
            progress = 0.78 * smooth((time - 420) / 390) * (1 - recover);
            frontOff = [mix(12, 74, snapIn), mix(16, 4, snapIn)];
            rearOff = [mix(-14, -42, active), mix(24, 14, active)];
            break;
        }
        case 'dragon_coiled': {
            // Coiled low crouch gather -> explosive upward-forward dragon palm.
            const coil = smooth((time - 120) / 360) * (1 - snapIn);
            height = mix(74, 50, coil) + 22 * snapIn;
            lean = -17 * coil + 24 * snapIn;
            progress = 0.88 * snap(time, 510, 320, 2.4) * (1 - recover);
            frontOff = [mix(-6, 72, snapIn), mix(28, -22, snapIn)];
            rearOff = [mix(-18, -44, active), mix(24, 16, active)];
            break;
        }
        case 'dragon_tail': {
            // Sweeping 360 spin back-palm strike: turns briefly away mid-turn, snaps face-forward by contact!
            const spinT = clamp((time - 470) / 450);
            if (spinT > 0.14 && spinT < 0.64) facing = -1;
            roll = Math.sin(spinT * Math.PI) * 0.15;
            lift = -18 * Math.sin(spinT * Math.PI);
            height = mix(74, 63, active);
            lean = 22 * snapIn;
            progress = 0.92 * launch * (1 - recover);
            frontOff = [mix(-26, 76, snapIn), mix(6, 2, snapIn)];
            rearOff = [mix(-28, -48, active), mix(14, -10, active)];
            break;
        }
        case 'twin_dragons': {
            // Rapid 1-2 alternating twin palm strike (front snap -> rear surge -> twin brace).
            const p1 = snap(time, 520, 175, 2.8);
            const p2 = snap(time, 735, 195, 3.0);
            height = mix(74, 62, active);
            lean = -12 * prep * (1 - p1) + 18 * p1 + 10 * p2;
            progress = 0.94 * smooth((time - 400) / 410) * (1 - recover);
            const frontPulse = p1 * (1 - 0.52 * smooth((time - 700) / 110)) + 0.52 * snap(time, 855, 95, 2.2);
            frontOff = [mix(12, 74, frontPulse), mix(18, -8, frontPulse)];
            rearOff = [mix(-26, 76, p2), mix(16, 4, p2)];
            break;
        }
        case 'dragon_quake': {
            // Leap stomp at 690ms sending ground fissure wave forward.
            const hop = Math.sin(Math.PI * clamp((time - 320) / 360));
            const stomp = snap(time, 630, 160, 3.0);
            lift = -34 * hop;
            height = mix(74, 54, stomp * (1 - recover));
            lean = -12 * prep * (1 - stomp) + 27 * stomp;
            progress = 0.42 * smooth((time - 320) / 340) * (1 - recover);
            frontOff = [mix(8, 70, stomp), mix(-18, 28, stomp)];
            rearOff = [mix(-14, 60, stomp), mix(-14, 32, stomp)];
            break;
        }
        case 'dragon_dash': {
            // Sudden low lightning dash with afterimage blink & heavy chest palm.
            const dash = snap(time, 535, 245, 2.9);
            const crouch = smooth((time - 100) / 360) * (1 - dash * 0.4);
            blink = time > 520 && time < 720 ? Math.sin(((time - 520) / 200) * Math.PI) * 0.72 : 0;
            lift = -12 * Math.sin(Math.PI * clamp((time - 520) / 260));
            height = mix(74, 56, crouch);
            lean = -15 * crouch + 30 * dash;
            progress = (0.12 * prep + 0.90 * dash) * (1 - recover);
            frontOff = [mix(-16, 78, dash), mix(20, -2, dash)];
            rearOff = [mix(-26, -46, active), mix(18, 10, active)];
            break;
        }
        case 'dragon_sky': {
            // Soaring skyward leap -> plunging downward palm strike at 950ms!
            const gather = smooth((time - 80) / 340) * (1 - smooth((time - 420) / 140));
            const leapArc = Math.sin(Math.PI * clamp((time - 410) / 550));
            const dive = snap(time, 700, 210, 2.8);
            lift = -98 * leapArc;
            height = mix(74, 54, gather) + 18 * leapArc * (1 - dive);
            lean = -14 * gather + 28 * dive;
            progress = smooth((time - 420) / 480) * (1 - recover);
            frontOff = [mix(12, 72, dive), mix(-34, 34, dive)];
            rearOff = [mix(-20, -40, dive), mix(18, -32, dive)];
            break;
        }
        case 'domain_dragon': {
            // Ultimate: deep rooted twin-palm spiral gather (0-620ms) -> explosive double-palm push (620-780ms)
            // -> subtle "youhui" recoil absorption after impact (1020-1160ms).
            const gather = smooth((time - 90) / 420) * (1 - snapIn);
            const youhui = smooth((time - 1020) / 140) * (1 - recover);
            height = mix(74, 53, gather) + 9 * snapIn;
            lean = -16 * gather + 27 * snapIn - 6 * youhui;
            progress = 0.32 * smooth((time - 430) / 340) * (1 - recover);
            const swirl = Math.sin(clamp(time / 600) * Math.PI * 2) * 14 * gather;
            frontOff = [mix(6 - swirl, 78 - 10 * youhui, snapIn), mix(16 + swirl * 0.5, -2, snapIn)];
            rearOff = [mix(-18 + swirl, 68 - 10 * youhui, snapIn), mix(24 - swirl * 0.5, 4, snapIn)];
            break;
        }
    }

    lean = Math.max(-34, Math.min(34, lean * (1 - recover)));
    height = mix(height, 74, recover);

    const hip = [0, -height];
    const neck = [lean, -height - Math.sqrt(Math.max(100, 52 * 52 - lean * lean))];
    const shoulders = [[neck[0] - 10, neck[1] + 6], [neck[0] + 10, neck[1] + 6]];

    const idleFront = [shoulders[1][0] + 29, shoulders[1][1] + 22];
    const idleRear = [shoulders[0][0] - 18, shoulders[0][1] + 26];
    const frontTarget = [
        mix(idleFront[0], shoulders[1][0] + frontOff[0], 1 - recover),
        mix(idleFront[1], shoulders[1][1] + frontOff[1], 1 - recover),
    ];
    const rearTarget = [
        mix(idleRear[0], shoulders[0][0] + rearOff[0], 1 - recover),
        mix(idleRear[1], shoulders[0][1] + rearOff[1], 1 - recover),
    ];

    const [elbow, hand] = twoBone(shoulders[1], frontTarget, 40, 1);
    const [backElbow, backHand] = twoBone(shoulders[0], rearTarget, 40, -1);

    const airborne = lift < -12;
    const stride = airborne ? 26 : 36 + 21 * smooth((time - 360) / 340) * (1 - recover) + 4 * settle * (1 - follow);
    const backFoot = airborne ? [-stride - 8, -24] : [-stride, 0];
    const frontFoot = airborne ? [stride * 0.78, -32] : [stride, 0];
    const [backKnee, backFootPt] = twoBone(hip, backFoot, 48, -1);
    const [knee, footPt] = twoBone(hip, frontFoot, 48, -1);

    const overshoot = dodged && time > 880 && time < 1260 ? 14 * Math.sin(((time - 880) / 380) * Math.PI) : 0;
    const stopOffset = move.ranged ? 0 : 12;

    return {
        x: Math.max(0, travel - stopOffset) * progress + overshoot,
        lift,
        opacity,
        blink,
        pose: {
            points: [[neck[0], neck[1] - 21], neck, hip, backElbow, backHand, elbow, hand, backKnee, backFootPt, knee, footPt],
            shoulders,
            sword: 0,
            lean: 0,
            facing,
            roll,
        },
    };
}

export function drawXianglongEffects(ctx, event, local, sampleAt, target, dir, impactAge, hit, width = 960, webEnhanced = false) {
    const move = xianglongArt.moves.find((item) => item.name === event?.move);
    if (!move || local < 150 || local > 1620) return;

    const fade = clamp((1580 - local) / 340);
    const current = sampleAt(Math.min(local, 980));
    const palmOrigin = current.hand;
    const rearOrigin = current.rearHand || current.hand;

    // 1. Warm amber-ink Domain Contrast Wash for 绝技·亢龙有悔
    if (move.ultimate && local >= 320 && local <= 1400) {
        const domainAlpha = smooth((local - 320) / 180) * (1 - smooth((local - 1080) / 320));
        ctx.save();
        ctx.fillStyle = `rgba(38, 25, 11, ${domainAlpha * (webEnhanced ? 0.26 : 0.14)})`;
        ctx.fillRect(-40, -40, width + 80, 510);
        ctx.restore();
    }

    // 2. Phase 1 Windup Qi Gathering around palms (160~640ms)
    if (local >= 160 && local <= 660) {
        const gatherP = smooth((local - 160) / 380) * (1 - smooth((local - 560) / 100));
        ctx.save();
        for (let i = 0; i < (move.ultimate ? 12 : 7); i++) {
            const ang = i * 2.399 + local * 0.004;
            const r = (1 - clamp((local - 180) / 440)) * 54 + 8;
            const px = palmOrigin[0] + Math.cos(ang) * r;
            const py = palmOrigin[1] + Math.sin(ang) * r * 0.8;
            ctx.globalAlpha = gatherP * 0.68;
            ctx.strokeStyle = i % 3 === 0 ? xianglongArt.glow : xianglongArt.ink;
            ctx.lineWidth = i % 3 === 0 ? 1.8 : 1.3;
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(mix(px, palmOrigin[0], 0.45), mix(py, palmOrigin[1], 0.45));
            ctx.stroke();
        }
        ctx.globalAlpha = gatherP * 0.34;
        ctx.strokeStyle = xianglongArt.glow;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.ellipse(current.root[0], 327, 26 + gatherP * 18, 4.5 + gatherP * 2, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
    }

    // 3. Move-Specific Dragon & Shockwave Visuals
    if (['dragon_field', 'dragon_coiled', 'dragon_dash'].includes(move.style) && local >= 640 && local <= 1180) {
        const p = clamp((local - 640) / 340);
        const burstFade = (1 - smooth((local - 880) / 300)) * smooth((local - 640) / 55);
        const angle = move.style === 'dragon_coiled' ? -0.32 : 0;
        const burstX = mix(palmOrigin[0], target[0], 0.48);
        const burstY = mix(palmOrigin[1], target[1], 0.35);

        if (webEnhanced && xianglongAssets['palm-burst']?.complete && xianglongAssets['palm-burst'].naturalWidth) {
            drawStripSlicedImage(ctx, xianglongAssets['palm-burst'], burstX, burstY, 175 + p * 65, 118 + p * 36, {
                slices: 18,
                amp: 4.5 * (1 - p),
                freq: 6,
                phase: local * 0.014,
                dir,
                angle,
                alpha: burstFade * 0.86,
                reveal: 0.55 + p * 0.45,
                travelOffset: 90 + p * 70,
            });
        } else {
            drawInkShockArc(ctx, burstX + dir * p * 32, burstY, 54 + p * 34, dir === 1 ? angle : Math.PI - angle, 2.05, 22 * (1 - p * 0.3), xianglongArt.glow, burstFade, webEnhanced);
        }
    }

    if (move.style === 'dragon_tail' && local >= 640 && local <= 1180) {
        const p = clamp((local - 640) / 360);
        const arcFade = (1 - smooth((local - 900) / 280)) * smooth((local - 640) / 60);
        const cx = mix(current.root[0], target[0], 0.52);
        const cy = target[1] + 6;
        drawInkShockArc(ctx, cx, cy, 62 + p * 28, dir === 1 ? 0.16 : Math.PI - 0.16, 2.35, 24 * (1 - p * 0.35), xianglongArt.glow, arcFade, webEnhanced);
        if (webEnhanced && xianglongAssets['palm-burst']?.complete && xianglongAssets['palm-burst'].naturalWidth) {
            drawStripSlicedImage(ctx, xianglongAssets['palm-burst'], cx, cy, 168 + p * 44, 110, {
                slices: 18,
                amp: 5,
                freq: 6.5,
                phase: local * 0.016,
                dir,
                angle: 0.12,
                alpha: arcFade * 0.65,
                reveal: 0.6 + p * 0.4,
                travelOffset: 88 + p * 54,
            });
        }
    }

    if (move.style === 'twin_dragons' && local >= 540 && local <= 1220) {
        for (const [k, startT, origin] of [[0, 560, palmOrigin], [1, 760, rearOrigin]]) {
            const age = local - startT;
            if (age < 0 || age > 420) continue;
            const q = age / 420;
            const a = (1 - q) * smooth(age / 55);
            const cx = mix(origin[0], target[0], 0.56);
            const cy = origin[1] + (k === 0 ? -10 : 12);
            if (webEnhanced && xianglongAssets['palm-burst']?.complete && xianglongAssets['palm-burst'].naturalWidth) {
                drawStripSlicedImage(ctx, xianglongAssets['palm-burst'], cx, cy, 160 + q * 48, 102, {
                    slices: 16,
                    amp: 4,
                    freq: 6,
                    phase: local * 0.015 + k * 2,
                    dir,
                    angle: k === 0 ? -0.1 : 0.1,
                    alpha: a * 0.78,
                    reveal: 0.55 + q * 0.45,
                    travelOffset: 85 + q * 55,
                });
            } else {
                drawInkShockArc(ctx, cx, cy, 48 + q * 34, dir === 1 ? (k === 0 ? -0.18 : 0.18) : (k === 0 ? Math.PI + 0.18 : Math.PI - 0.18), 1.95, 18 * (1 - q * 0.3), xianglongArt.glow, a, webEnhanced);
            }
        }
    }

    if (move.style === 'dragon_quake' && local >= 680 && local <= 1280) {
        const stompX = sampleAt(680).root[0] + dir * 24;
        const waveP = clamp((local - 690) / 270);
        const quakeFade = 1 - smooth((local - 980) / 300);
        const reachDist = Math.max(150, Math.abs(target[0] - stompX) + 84);
        const frontX = mix(stompX, stompX + dir * reachDist, ease(waveP));

        if (webEnhanced && xianglongAssets['ground-quake']?.complete && xianglongAssets['ground-quake'].naturalWidth) {
            const curW = reachDist * (0.36 + 0.64 * ease(waveP));
            drawStripSlicedImage(ctx, xianglongAssets['ground-quake'], stompX, 276, curW, 128, {
                slices: 18,
                amp: 0,
                dir,
                alpha: quakeFade * 0.9,
                reveal: 1,
                travelOffset: curW - 14,
                rigidFrom: 1,
                featherRight: 0.22,
            });
        }

        // Procedural ground cracks & dust fallback (shown on Bot GIF and blended on Web)
        const fissure = [];
        for (let i = 0; i <= 18; i++) {
            const u = i / 18;
            fissure.push([mix(stompX, frontX, u), 328 + (seed(i * 7 + 5) - 0.5) * 6 * (1 - u * 0.25)]);
        }
        const taper = (u) => Math.pow(1 - clamp(u), 0.55);
        ctx.save();
        brushPoly(ctx, fissure, 4.2, INK_RGB, quakeFade * 0.62, taper);
        if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
        brushPoly(ctx, fissure, 1.5, hexRgb(xianglongArt.glow), quakeFade * 0.52, taper);
        ctx.globalCompositeOperation = 'source-over';
        for (let i = 0; i < 10; i++) {
            const u = (i + 1) / 10;
            if (waveP < u * 0.85) continue;
            const age = clamp((local - (690 + u * 220)) / 520);
            const px = mix(stompX, stompX + dir * reachDist, u);
            const rise = age * (24 + seed(i + 12) * 28);
            ctx.fillStyle = i % 3 === 0 ? xianglongArt.glow : `rgb(${INK_RGB})`;
            ctx.globalAlpha = (1 - age) * 0.18 * quakeFade;
            ctx.beginPath();
            ctx.ellipse(px, 325 - rise * 0.5, 13 + age * 14, 5 + age * 4, 0, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    }

    if (move.style === 'dragon_sky' && local >= 560 && local <= 1240) {
        const apex = sampleAt(620).hand;
        const flyP = clamp((local - 600) / 350);
        const skyFade = (1 - smooth((local - 950) / 290)) * smooth((local - 560) / 70);
        const dx = target[0] - apex[0];
        const dy = (hit ? target[1] : 318) - apex[1];
        const dist = Math.max(90, Math.hypot(dx, dy));
        const diveAng = Math.atan2(dy, Math.abs(dx));

        if (webEnhanced && xianglongAssets['dragon-surge']?.complete && xianglongAssets['dragon-surge'].naturalWidth) {
            drawStripSlicedImage(ctx, xianglongAssets['dragon-surge'], apex[0] + dir * 18, apex[1] + 6, 290, 142, {
                slices: 26,
                amp: 9,
                freq: 7.2,
                phase: local * 0.016,
                dir,
                angle: diveAng,
                alpha: skyFade * 0.94,
                reveal: 0.4 + flyP * 0.6,
                travelOffset: 92 + ease(flyP) * (dist + 44),
                rigidFrom: 0.62,
                clipMinX: -20,
            });
        } else {
            const headX = mix(apex[0], apex[0] + dir * Math.abs(dx), ease(flyP));
            const headY = mix(apex[1], apex[1] + dy, ease(flyP));
            drawProceduralInkDragon(ctx, apex[0], apex[1], headX, headY, local, skyFade, xianglongArt.glow, webEnhanced);
        }
    }

    if (move.style === 'domain_dragon' && local >= 610 && local <= 1460) {
        const surgeP = clamp((local - 620) / 360);
        const dragonFade = (1 - smooth((local - 1080) / 380)) * smooth((local - 610) / 60);
        const launchHand = sampleAt(660).hand;
        const span = Math.max(240, Math.abs(target[0] - launchHand[0]) + (hit ? 95 : 170));
        const dragonW = Math.min(460, span * 1.15);
        const dragonH = dragonW * 0.48;
        const headTravel = 68 + ease(surgeP) * (span - 18) + clamp((local - 980) / 480) * 58;

        if (webEnhanced && xianglongAssets['dragon-surge']?.complete && xianglongAssets['dragon-surge'].naturalWidth) {
            // Tapered golden-amber calligraphic qi ribbons weaving along the surging dragon spine
            ctx.save();
            ctx.globalCompositeOperation = 'lighter';
            const ribPts = [];
            const ribMax = Math.min(span, headTravel - 18);
            for (let i = 0; i <= 18; i++) {
                const u = i / 18;
                ribPts.push([
                    launchHand[0] + dir * u * ribMax,
                    launchHand[1] - 4 + Math.sin(u * 7.2 - local * 0.015) * 14 * Math.sin(u * Math.PI),
                ]);
            }
            brushPoly(ctx, ribPts, 5.2, hexRgb(xianglongArt.glow), dragonFade * 0.42);
            brushPoly(ctx, ribPts, 1.8, hexRgb(xianglongArt.glowBright), dragonFade * 0.52);
            ctx.restore();

            drawStripSlicedImage(ctx, xianglongAssets['dragon-surge'], launchHand[0] - dir * 12, launchHand[1] - 4, dragonW, dragonH, {
                slices: 32,
                amp: 11,
                freq: 7.8,
                phase: local * 0.015,
                dir,
                angle: 0,
                alpha: dragonFade * 0.96,
                reveal: 0.35 + surgeP * 0.65,
                travelOffset: headTravel,
                rigidFrom: 0.62,
                clipMinX: -12,
                clipMaxX: span + 90,
            });
        } else {
            const endX = launchHand[0] + dir * Math.min(span + 40, headTravel);
            drawProceduralInkDragon(ctx, launchHand[0], launchHand[1], endX, launchHand[1] - 6, local, dragonFade, xianglongArt.glow, webEnhanced);
        }

        // Ground wind wake beneath surging dragon
        ctx.save();
        ctx.globalAlpha = dragonFade * 0.42;
        ctx.strokeStyle = xianglongArt.glow;
        ctx.lineWidth = 1.6;
        const wakeX = launchHand[0] + dir * headTravel * 0.72;
        ctx.beginPath();
        ctx.ellipse(wakeX, 328, 48, 5.5, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
    }

    // 4. Hit-Confirmed Impact Burst (STRICTLY omitted on dodge!)
    if (hit && impactAge >= 0 && impactAge < 640) {
        const p = impactAge / 640;
        const ringAlpha = (1 - p) * 0.9 * fade;
        ctx.save();
        const dropCount = move.ultimate ? 26 : move.signature ? 18 : 11;
        for (let i = 0; i < dropCount; i++) {
            const ang = i * 2.39996 + (event.action || 0);
            const speed = (36 + seed(i * 13) * (move.ultimate ? 132 : 82)) * ease(p * 1.25);
            const dx = target[0] + Math.cos(ang) * speed;
            const dy = target[1] + Math.sin(ang) * speed * 0.78 + p * p * 26;
            const r = (1.8 + seed(i * 23) * 3.4) * (1 - p * 0.55);
            ctx.globalAlpha = ringAlpha * 0.85;
            ctx.fillStyle = i % 3 === 0 ? xianglongArt.glow : xianglongArt.ink;
            ctx.beginPath();
            ctx.ellipse(dx, dy, r * 1.7, r * 0.9, ang, 0, Math.PI * 2);
            ctx.fill();
        }

        if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
        const rings = move.ultimate ? 3 : 2;
        for (let rIdx = 0; rIdx < rings; rIdx++) {
            const rad = 14 + p * (58 + rIdx * 28);
            ctx.globalAlpha = ringAlpha * (0.44 - rIdx * 0.12);
            ctx.strokeStyle = xianglongArt.glow;
            ctx.lineWidth = (move.ultimate ? 2.0 : 1.2) * (1 - p);
            ctx.beginPath();
            ctx.ellipse(target[0], target[1], rad * 0.75, rad, 0.16 * dir, 0, Math.PI * 2);
            ctx.stroke();
        }
        ctx.restore();

        if (move.ultimate && SHOW_ULTIMATE_SEALS) {
            drawDragonSeal(ctx, target[0] + dir * 56, target[1] - 24, '亢龙', xianglongArt.sealColor, p);
        }
    }
}
