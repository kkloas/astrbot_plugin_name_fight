import { twoBone } from './sampleMotion.js';
import { ease } from './choreography.js';

const clamp = (x) => Math.max(0, Math.min(1, x));
const smooth = (x) => { const v = clamp(x); return v * v * (3 - 2 * v); };
const mix = (a, b, t) => a + (b - a) * t;
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

export const masterArts = {
    sword_xuanmo: {
        name: '玄墨剑典',
        type: 'sword',
        weapon: 'sword',
        ink: '#172026',
        glow: '#0ea5e9',
        glowBright: '#7dd3fc',
        sealColor: '#0369a1',
        sash: '#0e7490',
        sashHighlight: '#38bdf8',
        moves: [
            m('起笔问墨', 'rise', 0.92, -0.52),
            m('残月掠影', 'crescent', 0.98, 0.14),
            m('墨影穿云', 'blink', 0.96, -0.06, 16),
            m('破空剑气', 'wave', 1.06, 0.08, 0, 1, true),
            m('泼墨回风', 'whirl', 1.12, -0.18, 18, 2),
            m('太极封锋', 'taiji', 1.16, -0.04, 8, 1, false, true),
            m('万剑归宗', 'wanjian', 1.36, -0.22, 92, 5, true, true),
            m('绝技·一剑霜寒', 'domain_sword', 1.48, 0.02, 14, 1, false, true),
        ],
    },
    blade_chixiao: {
        name: '赤霄断魂刀',
        type: 'blade',
        weapon: 'blade',
        ink: '#241515',
        glow: '#dc2626',
        glowBright: '#fb923c',
        sealColor: '#b91c1c',
        sash: '#991b1b',
        sashHighlight: '#f97316',
        moves: [
            m('赤霞横江', 'sweep', 0.98, 0.12),
            m('裂甲断岳', 'crush', 0.92, 0.42, 44),
            m('残阳撩月', 'upper', 1.05, -0.68, 20),
            m('血影旋斩', 'spin', 1.02, 0.08, 24, 2),
            m('焚风踏浪', 'double', 1.14, 0.24, 14, 2),
            m('赤练裂地', 'ground_wave', 1.22, 0.52, 56, 1, true, true),
            m('狂煞乱舞', 'storm', 1.38, 0.16, 26, 4, false, true),
            m('绝技·赤霄断魂', 'domain_blade', 1.50, 0.36, 102, 1, false, true),
        ],
    },
};

export const masterMoves = Object.entries(masterArts).flatMap(([id, art]) =>
    art.moves.map((move) => ({ id, name: art.name, type: art.type, move: move.name, power: move.power })),
);

export const isMasterArt = (id) => Boolean(masterArts[id]);
export const masterMoveFor = (event) => masterArts[event?.martialArtId]?.moves.find((item) => item.name === event?.move);

export function masterTechnique(event, fighter) {
    const id = event?.martialArtId || fighter?.martialArt?.id;
    const art = masterArts[id];
    const move = masterMoveFor({ ...event, martialArtId: id });
    if (!art || !move) return undefined;
    const motionMap = {
        rise: 'rise',
        crescent: 'slash',
        blink: 'draw',
        wave: 'slash',
        whirl: 'flurry',
        taiji: 'thrust',
        wanjian: 'leap',
        domain_sword: 'draw',
        sweep: 'sweep',
        crush: 'cleave',
        upper: 'rise',
        spin: 'flurry',
        double: 'flurry',
        ground_wave: 'leap',
        storm: 'flurry',
        domain_blade: 'cleave',
    };
    return {
        motion: motionMap[move.style] || 'slash',
        trail: 'edge',
        weight: move.ultimate ? 1.95 : move.signature ? 1.55 : move.power,
        color: art.glow,
        pattern: 'direct',
    };
}

export function masterMotion(event, time, travel, dodged = false) {
    const art = masterArts[event?.martialArtId];
    const move = masterMoveFor(event);
    if (!art || !move) return undefined;

    const prep = ease((time - 80) / 360);
    const launch = ease((time - 420) / 470);
    const strike = clamp((time - 600) / 350);
    const follow = clamp((time - 950) / 240);
    const recover = ease((time - 1180) / 480);

    let progress = launch * (1 - recover);
    let lift = -move.lift * Math.sin(Math.PI * clamp((time - 420) / 640));
    let opacity = 1;
    let blink = 0;
    let facing = 1;
    let roll = 0;

    let arm = -1.6 * prep + (1.7 + move.angle) * ease(strike);
    let sword = -2.1 * prep + (2.15 + move.angle) * ease(strike);
    let reach = 52 + 24 * ease(strike);
    let height = 78;
    let lean = -9 * prep + 26 * launch;
    let rearAngle = -2.35;
    let rearReach = 48;
    let twoHanded = false;

    switch (move.style) {
        case 'rise': {
            // Sword-finger wipes blade low, then sweeps skyward like an ink brush stroke.
            const wipe = smooth((time - 140) / 340) * (1 - smooth((time - 540) / 140));
            const crouch = smooth((time - 160) / 260) * (1 - smooth((time - 570) / 220));
            arm = mix(0.68, -0.92, ease(strike));
            sword = mix(0.95, -1.25, ease(strike)) + follow * 0.18;
            reach = 48 + 28 * ease(strike);
            height = 78 - 15 * crouch + 6 * ease(strike);
            lean = 12 * crouch + 13 * ease(strike);
            if (wipe > 0.05) {
                rearAngle = mix(-1.2, 0.35, wipe);
                rearReach = 44;
            } else {
                rearAngle = -2.55;
                rearReach = 54;
            }
            break;
        }
        case 'crescent': {
            arm = mix(-2.15, 0.32, ease(strike));
            sword = mix(-2.55, 0.48, ease(strike));
            reach = 54 + 24 * Math.sin(strike * Math.PI);
            lean = -18 * prep * (1 - ease(strike)) + 25 * ease(strike);
            rearAngle = -2.75;
            rearReach = 56;
            break;
        }
        case 'blink': {
            // Vanishes into ink mist and materializes in a low piercing lunge.
            const vanish = time > 470 && time < 700 ? Math.sin(((time - 470) / 230) * Math.PI) : 0;
            blink = vanish;
            opacity = 1 - vanish * 0.92;
            progress = smooth((time - 510) / 220) * (1 - recover);
            arm = mix(-0.85, -0.05, ease(strike));
            sword = mix(-1.1, -0.04, ease(strike));
            reach = 46 + 32 * ease(strike);
            height = 71;
            lean = 30 * smooth((time - 540) / 260);
            rearAngle = -2.65;
            rearReach = 58;
            break;
        }
        case 'wave': {
            // Mid-range sword-qi projection: stops short and slashes a crescent projectile across the stage.
            progress = launch * 0.32 * (1 - recover);
            const slashBeat = smooth((time - 560) / 210);
            arm = mix(-2.1, 0.26, slashBeat);
            sword = mix(-2.45, 0.34, slashBeat);
            reach = 52 + 24 * slashBeat;
            lean = -12 * prep + 24 * slashBeat;
            rearAngle = -2.6;
            rearReach = 54;
            break;
        }
        case 'whirl': {
            const sweep = smooth((time - 570) / 300);
            arm = mix(-2.05, 0.30, sweep);
            sword = mix(-2.4, 0.36, sweep);
            reach = 52 + 20 * Math.sin(sweep * Math.PI * 0.5);
            lean = -10 * prep * (1 - sweep) + 22 * sweep;
            rearAngle = mix(-1.8, -2.65, sweep);
            break;
        }
        case 'taiji': {
            // Draws a circular Yin-Yang diagram with the sword tip before thrusting straight through.
            const circlePhase = clamp((time - 220) / 460);
            const thrustPhase = smooth((time - 680) / 270);
            progress = (0.35 * smooth((time - 240) / 360) + 0.65 * thrustPhase) * (1 - recover);
            if (time < 690) {
                const ang = circlePhase * Math.PI * 2 - Math.PI * 0.5;
                arm = -0.25 + Math.sin(ang) * 0.55;
                sword = -0.15 + Math.sin(ang) * 0.72;
                reach = 52 + Math.cos(ang) * 10;
                lean = 6;
                rearAngle = ang + Math.PI;
                rearReach = 40;
            } else {
                arm = mix(-0.3, -0.03, thrustPhase);
                sword = mix(-0.2, -0.02, thrustPhase);
                reach = mix(48, 78, thrustPhase);
                lean = mix(6, 29, thrustPhase);
                rearAngle = -2.75;
                rearReach = 58;
            }
            break;
        }
        case 'wanjian': {
            // Aerial Taiji Sword Formation: rises into the air, points sword skyward, then commands 10 spirit swords forward!
            const ascend = smooth((time - 240) / 320);
            const descend = smooth((time - 1080) / 360);
            const airborne = ascend * (1 - descend);
            lift = -96 * airborne;
            progress = 0.24 * airborne;
            const command = smooth((time - 700) / 210);
            arm = mix(-1.62, -0.16, command);
            sword = mix(-1.78, -0.12, command);
            reach = mix(56, 74, command);
            height = 79;
            lean = mix(-6, 20, command) * airborne;
            rearAngle = mix(-1.45, -2.55, command);
            rearReach = 50;
            break;
        }
        case 'domain_sword': {
            // Ultimate: low sheathed crouch, then instant cross-stage iaijutsu flash!
            const charge = smooth((time - 100) / 420);
            const flash = smooth((time - 590) / 210);
            const vanish = time > 580 && time < 770 ? Math.sin(((time - 580) / 190) * Math.PI) : 0;
            blink = vanish;
            opacity = 1 - vanish * 0.86;
            const dashDist = dodged ? 0.92 : 1.06;
            progress = flash * dashDist * (1 - recover * 0.92);
            height = mix(78, 64, charge * (1 - flash)) + 8 * flash;
            lean = mix(0, -14, charge * (1 - flash)) + 31 * flash;
            arm = mix(0.1, -2.45, charge * (1 - flash)) + 2.52 * flash;
            sword = mix(-0.4, -2.85, charge * (1 - flash)) + 2.92 * flash;
            reach = mix(44, 78, flash);
            rearAngle = flash > 0.4 ? -2.7 : 0.65;
            rearReach = 52;
            break;
        }
        case 'sweep': {
            arm = mix(-2.45, 0.32, ease(strike));
            sword = mix(-2.85, 0.28, ease(strike));
            reach = 54 + 24 * ease(strike);
            height = 72;
            lean = -12 * prep + 29 * launch;
            twoHanded = time > 450 && time < 1050;
            break;
        }
        case 'crush': {
            arm = mix(-2.15, 0.48, ease(strike));
            sword = mix(-2.45, 0.56, ease(strike));
            reach = 58 + 20 * ease(strike);
            height = 75 - 8 * follow;
            lean = -14 * prep + 28 * ease(strike);
            twoHanded = true;
            break;
        }
        case 'upper': {
            // Ground-scraping blade drag into towering rising moon cleave!
            const drag = smooth((time - 320) / 240) * (1 - smooth((time - 680) / 120));
            const cleave = smooth((time - 660) / 290);
            height = mix(76, 63, drag) + 16 * cleave;
            lean = 22 * drag + 18 * cleave;
            arm = mix(0.85, -1.18, cleave);
            sword = mix(0.68, -1.52, cleave);
            reach = 52 + 24 * cleave;
            rearAngle = -2.45;
            break;
        }
        case 'spin': {
            const spinT = clamp((time - 520) / 430);
            if (spinT > 0.18 && spinT < 0.66) facing = -1;
            roll = Math.sin(spinT * Math.PI) * 0.14;
            arm = -2.4 + spinT * 2.85;
            sword = -2.75 + spinT * 3.15;
            reach = 58 + 18 * Math.sin(spinT * Math.PI);
            lean = 22 * launch;
            break;
        }
        case 'double': {
            const first = smooth((time - 540) / 200);
            const second = smooth((time - 760) / 190);
            arm = -2.1 + first * 2.5 - smooth((time - 700) / 80) * 1.9 + second * 2.05;
            sword = arm + 0.18;
            reach = 52 + 24 * Math.max(first * (1 - second), second);
            lean = 25 * launch;
            twoHanded = second > 0.2;
            break;
        }
        case 'ground_wave': {
            // Mid-range aerial slam that sends a crimson fissure racing across the ground.
            const jump = Math.sin(Math.PI * clamp((time - 340) / 430));
            lift = -62 * jump;
            const slam = smooth((time - 580) / 190);
            progress = 0.38 * smooth((time - 340) / 380) * (1 - recover);
            height = mix(78, 64, slam * (1 - recover));
            lean = -12 * prep + 28 * slam;
            arm = mix(-2.25, 0.56, slam);
            sword = mix(-2.55, 0.48, slam);
            reach = 56 + 20 * slam;
            twoHanded = true;
            break;
        }
        case 'storm': {
            const cleave = smooth((time - 560) / 330);
            arm = mix(-2.35, 0.42, cleave);
            sword = mix(-2.7, 0.40, cleave);
            reach = 54 + 22 * cleave;
            height = 78 - 8 * cleave;
            lean = -13 * prep * (1 - cleave) + 28 * cleave;
            twoHanded = true;
            break;
        }
        case 'domain_blade': {
            // Ultimate: sky-high blood-moon leap into titanic diagonal execution cleave!
            const gather = smooth((time - 120) / 380);
            const leap = Math.sin(Math.PI * clamp((time - 430) / 510));
            const cleave = smooth((time - 690) / 260);
            lift = -104 * leap;
            progress = smooth((time - 450) / 460) * (1 - recover);
            height = mix(78, 66, cleave * (1 - recover));
            lean = mix(-16 * gather, 31, cleave);
            arm = mix(-2.35 * gather, 0.52, cleave);
            sword = mix(-2.65 * gather, 0.46, cleave);
            reach = 56 + 22 * cleave;
            twoHanded = true;
            break;
        }
    }

    arm = mix(arm, 0.45, recover);
    sword = mix(sword, -0.42, recover);
    reach = mix(reach, 52, recover);
    lean *= 1 - recover;
    height = mix(height, 78, recover);

    const clampedLean = Math.max(-34, Math.min(34, lean));
    const hip = [0, -height];
    const neck = [clampedLean, -height - Math.sqrt(Math.max(100, 52 * 52 - clampedLean * clampedLean))];
    const shoulders = [[neck[0] - 10, neck[1] + 6], [neck[0] + 10, neck[1] + 6]];

    let frontTarget = [shoulders[1][0] + Math.cos(arm) * reach, shoulders[1][1] + Math.sin(arm) * reach];
    let rearTarget = [shoulders[0][0] + Math.cos(rearAngle) * rearReach, shoulders[0][1] + Math.sin(rearAngle) * rearReach];

    if (twoHanded) {
        const gripGap = 15;
        for (let i = 0; i < 8; i++) {
            for (const [root, off] of [[shoulders[1], 0], [shoulders[0], gripGap]]) {
                const dx = frontTarget[0] - off * Math.cos(sword) - root[0];
                const dy = frontTarget[1] - off * Math.sin(sword) - root[1];
                const d = Math.hypot(dx, dy);
                if (d > 77) {
                    frontTarget[0] -= dx * (1 - 77 / d);
                    frontTarget[1] -= dy * (1 - 77 / d);
                }
            }
        }
        rearTarget = [frontTarget[0] - gripGap * Math.cos(sword), frontTarget[1] - gripGap * Math.sin(sword)];
    }

    const [elbow, hand] = twoBone(shoulders[1], frontTarget, 40, 1);
    const [backElbow, backHand] = twoBone(shoulders[0], rearTarget, 40, -1);

    const airborne = lift < -12;
    const stride = airborne ? 26 : 36 + 22 * Math.sin(launch * Math.PI) * (1 - recover);
    let backFootPos = airborne ? [-stride - 8, -26] : [-stride, 0];
    let frontFootPos = airborne ? [stride * 0.75, -34] : [stride + 6 * ease(strike) * (1 - recover), 0];
    if (!airborne && move.style === 'rise') {
        const stance = smooth((time - 180) / 260) * (1 - recover);
        backFootPos = [mix(backFootPos[0], -49, stance), 0];
        frontFootPos = [mix(frontFootPos[0], 53, stance), 0];
    } else if (!airborne && move.style === 'crescent') {
        const step = smooth((time - 350) / 260);
        const stepLift = Math.sin(Math.PI * step) * (1 - recover);
        backFootPos = [mix(backFootPos[0], -20, step * (1 - recover)), -18 * stepLift];
        frontFootPos = [mix(frontFootPos[0], 54, step * (1 - recover)), 0];
    }
    const [backKnee, backFoot] = twoBone(hip, backFootPos, 48, -1);
    const [knee, foot] = twoBone(hip, frontFootPos, 48, -1);

    const bladeLen = art.weapon === 'blade' ? 106 : 99;
    if (!airborne && sword > 0 && sword < Math.PI / 2) {
        sword = Math.min(sword, Math.asin(clamp((-hand[1] - 6) / bladeLen)));
    }

    const stopOffset = move.ranged ? 0 : art.weapon === 'blade' ? 14 : 8;
    return {
        x: Math.max(0, travel - stopOffset) * progress,
        lift,
        opacity,
        blink,
        pose: {
            points: [[neck[0], neck[1] - 21], neck, hip, backElbow, backHand, elbow, hand, backKnee, backFoot, knee, foot],
            shoulders,
            sword,
            lean: 0,
            facing,
            roll,
        },
    };
}

// Organic calligraphic tapered brush stroke between two joints (inspired by code_artifact.html drawBrushLimb).
function brushSegment(ctx, p1, p2, wStart, wEnd, color) {
    const dx = p2[0] - p1[0];
    const dy = p2[1] - p1[1];
    const len = Math.hypot(dx, dy);
    if (len < 0.5) return;
    const nx = -dy / len;
    const ny = dx / len;
    const mx = (p1[0] + p2[0]) * 0.5 + nx * 1.4;
    const my = (p1[1] + p2[1]) * 0.5 + ny * 1.4;
    const wMid = (wStart + wEnd) * 0.52;

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(p1[0] + nx * wStart * 0.5, p1[1] + ny * wStart * 0.5);
    ctx.quadraticCurveTo(mx + nx * wMid * 0.5, my + ny * wMid * 0.5, p2[0] + nx * wEnd * 0.5, p2[1] + ny * wEnd * 0.5);
    ctx.arc(p2[0], p2[1], wEnd * 0.5, Math.atan2(ny, nx), Math.atan2(-ny, -nx));
    ctx.quadraticCurveTo(mx - nx * wMid * 0.5, my - ny * wMid * 0.5, p1[0] - nx * wStart * 0.5, p1[1] - ny * wStart * 0.5);
    ctx.arc(p1[0], p1[1], wStart * 0.5, Math.atan2(-ny, -nx), Math.atan2(ny, nx));
    ctx.closePath();
    ctx.fill();
}

function drawMasterWeapon(ctx, art, weapon, ink, time, armed = true) {
    if (!armed || weapon === 'unarmed') return;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const pulse = 0.72 + Math.sin(time / 140) * 0.22;

    // Hilt tassel fluttering with weapon motion
    const tasselWave = Math.sin(time / 105) * 7;
    ctx.strokeStyle = art.sash;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(-17, 0);
    ctx.quadraticCurveTo(-29, 7 + tasselWave * 0.6, -38, 14 + tasselWave);
    ctx.stroke();

    if (weapon === 'blade') {
        // Broad crimson-ink saber (赤霄断魂刃)
        ctx.strokeStyle = '#3b2322';
        ctx.lineWidth = 5.5;
        ctx.beginPath();
        ctx.moveTo(-18, 0);
        ctx.lineTo(3, 0);
        ctx.stroke();

        // Guard
        ctx.strokeStyle = '#d97706';
        ctx.lineWidth = 3.5;
        ctx.beginPath();
        ctx.moveTo(2, -10);
        ctx.lineTo(4, 10);
        ctx.stroke();

        // Dark ink spine + glowing crimson-gold edge
        ctx.fillStyle = '#261c1d';
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.3;
        ctx.beginPath();
        ctx.moveTo(5, -3);
        ctx.quadraticCurveTo(58, -8, 105, -24);
        ctx.quadraticCurveTo(94, 2, 78, 10);
        ctx.lineTo(5, 6);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Molten spirit vein along cutting arc
        ctx.strokeStyle = art.glow;
        ctx.globalAlpha *= 0.85 * pulse;
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.moveTo(8, 4.5);
        ctx.quadraticCurveTo(68, 7, 103, -22);
        ctx.stroke();

        ctx.strokeStyle = '#fef08a';
        ctx.lineWidth = 0.9;
        ctx.beginPath();
        ctx.moveTo(14, 3.5);
        ctx.quadraticCurveTo(68, 5, 103, -22);
        ctx.stroke();
    } else {
        // Cyan-ink master jian (玄墨青锋)
        ctx.strokeStyle = '#20343d';
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(-17, 0);
        ctx.lineTo(3, 0);
        ctx.stroke();

        // Taiji-inspired guard
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(2, -9);
        ctx.lineTo(2, 9);
        ctx.stroke();

        ctx.fillStyle = '#e2edf2';
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(5, -3);
        ctx.lineTo(86, -2);
        ctx.lineTo(100, 0);
        ctx.lineTo(86, 2.2);
        ctx.lineTo(5, 3);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Glowing cyan ink fuller
        ctx.strokeStyle = art.glow;
        ctx.globalAlpha *= 0.9 * pulse;
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.moveTo(8, 0);
        ctx.lineTo(96, 0);
        ctx.stroke();
    }
    ctx.restore();
}

export function drawMasterSash(ctx, side, time, alpha, artId, trailSamples = []) {
    const art = masterArts[artId];
    if (!art) return;
    if (trailSamples.length >= 2 && alpha > 0.22) {
        ctx.save();
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        for (const [jointIndex, baseWidth, waveAmp, color] of [
            [0, 3.2, 5.5, art.sashHighlight],
            [2, 5.0, 7.5, art.sash],
        ]) {
            const nodes = trailSamples.map((sample, k) => {
                const sDir = (side === 'a' ? 1 : -1) * (sample.pose.facing || 1);
                const jp = sample.pose.points[jointIndex];
                const flutter = Math.sin(time / 115 - k * 0.85 + jointIndex) * waveAmp * (k / trailSamples.length);
                const dragX = -sDir * k * 8.5;
                return [
                    sample.x + sDir * jp[0] + dragX,
                    324 + sample.lift + jp[1] + flutter + k * 1.4,
                ];
            });
            for (let k = 0; k < nodes.length - 1; k++) {
                const ratio = 1 - k / nodes.length;
                ctx.globalAlpha = alpha * ratio * (jointIndex === 0 ? 0.72 : 0.82);
                brushSegment(ctx, nodes[k], nodes[k + 1], baseWidth * ratio + 0.8, Math.max(0.6, baseWidth * (ratio - 0.16)), color);
            }
        }
        ctx.restore();
    }
}

export function drawMasterFigure(ctx, x, side, pose, time, weapon, alpha, lift, sheathed, artId, trailSamples = []) {
    const art = masterArts[artId];
    if (!art) return;
    const facingDir = (side === 'a' ? 1 : -1) * (pose.facing || 1);
    const p = pose.points;
    const s = pose.shoulders || [p[1], p[1]];
    const ink = side === 'a' ? art.ink : '#2f3837';

    drawMasterSash(ctx, side, time, alpha, artId, trailSamples);

    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.translate(x, 324 + lift);
    ctx.scale(facingDir, 1);
    ctx.rotate(pose.lean || 0);
    if (pose.roll) {
        ctx.translate(p[2][0], p[2][1]);
        ctx.rotate(pose.roll);
        ctx.translate(-p[2][0], -p[2][1]);
    }
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Back arm & back leg (tapered calligraphic strokes)
    brushSegment(ctx, s[0], p[3], 5.6, 4.4, ink);
    brushSegment(ctx, p[3], p[4], 4.4, 3.0, ink);
    brushSegment(ctx, p[2], p[7], 7.8, 6.0, ink);
    brushSegment(ctx, p[7], p[8], 6.0, 4.0, ink);

    // Martial robe skirt / hem silhouette between hips and knees
    ctx.fillStyle = ink;
    ctx.globalAlpha = alpha * 0.86;
    ctx.beginPath();
    ctx.moveTo(p[2][0] - 8, p[2][1] - 4);
    ctx.quadraticCurveTo(p[7][0] - 8, p[7][1] + 4, p[7][0] - 2, p[7][1] + 10);
    ctx.quadraticCurveTo(p[2][0], p[2][1] + 22, p[9][0] + 6, p[9][1] + 8);
    ctx.quadraticCurveTo(p[9][0] + 4, p[9][1] - 4, p[2][0] + 8, p[2][1] - 4);
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = alpha;

    // Torso (broad shoulder-to-waist calligraphic wedge)
    brushSegment(ctx, p[1], p[2], 11.2, 8.2, ink);

    // School sash belt at waist
    ctx.strokeStyle = art.sash;
    ctx.lineWidth = 3.4;
    ctx.beginPath();
    ctx.moveTo(p[2][0] - 7, p[2][1] - 1);
    ctx.lineTo(p[2][0] + 8, p[2][1] + 1);
    ctx.stroke();

    // Front leg & front arm
    brushSegment(ctx, p[2], p[9], 8.6, 6.6, ink);
    brushSegment(ctx, p[9], p[10], 6.6, 4.3, ink);
    brushSegment(ctx, s[1], p[5], 6.6, 5.0, ink);
    brushSegment(ctx, p[5], p[6], 5.0, 3.4, ink);

    // Head + distinctive martial silhouette crown/hat
    ctx.fillStyle = ink;
    ctx.beginPath();
    ctx.ellipse(p[0][0], p[0][1], 10.2, 13, 0.08, 0, Math.PI * 2);
    ctx.fill();

    if (artId === 'sword_xuanmo') {
        // Ink-cyan topknot & headband fillet
        ctx.fillStyle = art.sash;
        ctx.beginPath();
        ctx.ellipse(p[0][0] - 2, p[0][1] - 14, 4.5, 3.2, -0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = art.sashHighlight;
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.moveTo(p[0][0] - 9, p[0][1] - 4);
        ctx.lineTo(p[0][0] + 9, p[0][1] - 3);
        ctx.stroke();
    } else {
        // Crimson-gold martial brow band & fierce plume
        ctx.strokeStyle = art.sashHighlight;
        ctx.lineWidth = 2.6;
        ctx.beginPath();
        ctx.moveTo(p[0][0] - 10, p[0][1] - 5);
        ctx.lineTo(p[0][0] + 10, p[0][1] - 3);
        ctx.stroke();
    }

    // Sword-finger mudra on rear hand for sword_xuanmo
    if (artId === 'sword_xuanmo' && weapon === 'sword' && !sheathed) {
        const finger = Math.atan2(p[4][1] - p[3][1], p[4][0] - p[3][0]);
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.8;
        for (const off of [-0.11, 0.11]) {
            ctx.beginPath();
            ctx.moveTo(p[4][0], p[4][1]);
            ctx.lineTo(p[4][0] + Math.cos(finger + off) * 10, p[4][1] + Math.sin(finger + off) * 10);
            ctx.stroke();
        }
    }

    if (sheathed) {
        ctx.strokeStyle = ink;
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(p[2][0] - 66, p[2][1] + 12);
        ctx.lineTo(p[2][0] + 14, p[2][1] - 3);
        ctx.stroke();
    } else if (weapon !== 'unarmed') {
        ctx.translate(p[6][0], p[6][1]);
        ctx.rotate(pose.sword || 0);
        drawMasterWeapon(ctx, art, weapon, ink, time, true);
    }
    ctx.restore();
}

// ---------------------------------------------------------------------------
// 水墨笔触原语：两端出锋的毛笔笔画 + 飞白断笔 + 淡墨晕染。全部为纯函数(f(参数))，无随机、无状态。
// 取代早先实心三角 / 实心拱弧 / 粗描边亮线，让招式像宣纸上一笔扫过的淡墨，而不是抛出去的硬块。
// ---------------------------------------------------------------------------
const INK_RGB = '28,34,38';
const inkAssets = typeof Image === 'undefined' ? {} : Object.fromEntries(
    ['crescent', 'fissure'].map((name) => {
        const image = new Image();
        image.src = new URL(`./assets/ink-${name}.png`, import.meta.url).href;
        return [name, image];
    }),
);
const hexRgb = (hex) => {
    const h = String(hex).replace('#', '');
    return `${parseInt(h.slice(0, 2), 16) || 0},${parseInt(h.slice(2, 4), 16) || 0},${parseInt(h.slice(4, 6), 16) || 0}`;
};
const brushProfile = (u) => Math.pow(Math.sin(Math.PI * Math.pow(clamp(u), 0.75)), 0.8);

// Filled calligraphic stroke along a polyline; width follows `profile(u)` so both ends come to a point.
function brushPoly(ctx, pts, wMax, rgb, alpha, profile = brushProfile) {
    const n = pts.length;
    if (n < 2 || alpha <= 0.008 || wMax <= 0.05) return;
    const left = [], right = [];
    for (let i = 0; i < n; i++) {
        const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
        let dx = b[0] - a[0], dy = b[1] - a[1];
        const len = Math.hypot(dx, dy) || 1;
        dx /= len; dy /= len;
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

// One sweep of the brush: faint wash bleed, dry-brush hairlines with 飞白 gaps, a whisper of school colour.
function brushLine(ctx, x1, y1, x2, y2, wMax, glowColor, alpha, key, webEnhanced, bow = 0) {
    if (alpha <= 0.01) return;
    const dx = x2 - x1, dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len, ny = dx / len;
    const build = (off) => {
        const pts = [];
        for (let i = 0; i <= 18; i++) {
            const u = i / 18;
            const bend = (bow * Math.sin(Math.PI * u) + (seed(key + i * 2.3) - 0.5) * 2.2 * Math.sin(Math.PI * u)) + off;
            pts.push([mix(x1, x2, u) + nx * bend, mix(y1, y2, u) + ny * bend]);
        }
        return pts;
    };
    const rgbGlow = hexRgb(glowColor);
    ctx.save();
    brushPoly(ctx, build(0), wMax * 1.7, INK_RGB, alpha * 0.07);
    brushPoly(ctx, build(0), wMax, INK_RGB, alpha * 0.40);
    for (let k = 0; k < 4; k++) {
        const pts = build((k - 1.5) * wMax * 0.34);
        const cut = 5 + Math.floor(seed(key + k * 11) * 6);
        const gap = 2 + Math.floor(seed(key + k * 5) * 2);
        const hair = k % 2 ? pts.slice(0, cut).concat([]) : pts;
        brushPoly(ctx, hair, 1.1 + seed(key + k) * 0.9, INK_RGB, alpha * 0.30);
        if (k % 2) brushPoly(ctx, pts.slice(cut + gap), 1.0, INK_RGB, alpha * 0.26);
    }
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, build(0), Math.max(1.2, wMax * 0.2), rgbGlow, alpha * (webEnhanced ? 0.34 : 0.24));
    ctx.restore();
}

// 淡墨一笔扫过的弧形刀/剑光：晕染 + 飞白细笔 + 一缕流派色，没有实心色块。
function drawInkGlowCrescent(ctx, cx, cy, radius, angle, span, thickness, glowColor, brightColor, alpha, webEnhanced) {
    if (alpha <= 0.01 || radius <= 2) return;
    const key = Math.round(angle * 10) * 7 + Math.round(span * 10);
    const rgbGlow = hexRgb(glowColor);
    const a0 = -span * 0.5, a1 = span * 0.5;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(angle);
    for (let k = 0; k < 3; k++)
        brushPoly(ctx, arcPts(radius + (k - 1) * thickness * 0.3, a0 + span * 0.05, a1, 14, key + k), thickness * (1 - k * 0.15), INK_RGB, alpha * 0.055);
    for (let k = 0; k < 10; k++) {
        const t = k / 9, centered = 1 - Math.abs(t - 0.5) * 2;
        const r = radius + (t - 0.5) * thickness * 1.05;
        const s0 = a0 + span * 0.10 * seed(key + k * 3);
        const s1 = a1 - span * 0.20 * seed(key + k * 5 + 1);
        const w = 0.9 + centered * 2.4;
        const a = alpha * (0.16 + centered * 0.30);
        const rgb = k % 4 === 1 ? rgbGlow : INK_RGB;
        if (k % 2) {
            const gs = mix(s0, s1, 0.42 + 0.1 * seed(key + k)), ge = gs + (s1 - s0) * 0.07;
            brushPoly(ctx, arcPts(r, s0, gs, 8, key + k), w, rgb, a);
            brushPoly(ctx, arcPts(r, ge, s1, 8, key + k + 40), w, rgb, a);
        } else brushPoly(ctx, arcPts(r, s0, s1, 12, key + k), w, rgb, a);
    }
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, arcPts(radius, a0 * 0.8, a1 * 0.9, 14, key + 90), webEnhanced ? 2.0 : 1.4, rgbGlow, alpha * (webEnhanced ? 0.28 : 0.22));
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = `rgb(${INK_RGB})`;
    for (let i = 0; i < 6; i++) {
        const ang = mix(a0, a1, (i + 0.5) / 6);
        const dr = radius + thickness * (0.7 + seed(key + i * 7) * 0.8);
        ctx.globalAlpha = clamp(alpha * 0.3);
        ctx.beginPath();
        ctx.ellipse(Math.cos(ang) * dr, Math.sin(ang) * dr, 0.9 + seed(key + i * 9) * 1.9, 0.7 + seed(key + i * 13) * 1.1, ang, 0, Math.PI * 2);
        ctx.fill();
    }
    ctx.restore();
}

// 刀尖扫过的墨痕：由旧到新渐粗的淡墨笔画，外加一缕细细的流派色，不再是实心多边形。
function drawSweptWeaponRibbon(ctx, samples, glowColor, brightColor, fade, webEnhanced) {
    if (samples.length < 3 || fade <= 0.01) return;
    const rgbGlow = hexRgb(glowColor);
    const tips = samples.map((s) => s.tip).reverse();
    const mids = samples.map((s) => [mix(s.tip[0], s.hand[0], 0.28), mix(s.tip[1], s.hand[1], 0.28)]).reverse();
    const grow = (u) => Math.pow(clamp(u), 1.2);
    ctx.save();
    brushPoly(ctx, tips, 15, INK_RGB, fade * 0.07, grow);
    brushPoly(ctx, tips, 5.2, INK_RGB, fade * 0.40, grow);
    brushPoly(ctx, mids, 2.2, INK_RGB, fade * 0.20, grow);
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, tips, 2.0, rgbGlow, fade * 0.36, grow);
    ctx.restore();
}

// Rotating Yin-Yang Taiji & Eight-Trigrams Bagua Ink Seal
export function drawTaijiBaguaSeal(ctx, cx, cy, radius, rotation, glowColor, alpha, webEnhanced = false) {
    if (alpha <= 0.01 || radius <= 2) return;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rotation);

    // Outer ink brush ring
    ctx.globalAlpha = clamp(alpha * 0.42);
    ctx.strokeStyle = '#141c22';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.stroke();

    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = clamp(alpha * 0.85);
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.arc(0, 0, radius * 0.86, 0, Math.PI * 2);
    ctx.stroke();

    // Yin-Yang S-curve divider
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.arc(0, -radius * 0.43, radius * 0.43, -Math.PI * 0.5, Math.PI * 0.5, false);
    ctx.arc(0, radius * 0.43, radius * 0.43, -Math.PI * 0.5, Math.PI * 0.5, true);
    ctx.stroke();

    // Twin Yin-Yang eyes
    ctx.fillStyle = glowColor;
    ctx.beginPath();
    ctx.arc(0, -radius * 0.43, Math.max(1.5, radius * 0.09), 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#0f172a';
    ctx.globalCompositeOperation = 'source-over';
    ctx.beginPath();
    ctx.arc(0, radius * 0.43, Math.max(1.5, radius * 0.09), 0, Math.PI * 2);
    ctx.fill();

    // 8 Bagua trigram ticks around outer perimeter
    ctx.strokeStyle = glowColor;
    ctx.globalAlpha = clamp(alpha * 0.72);
    ctx.lineWidth = 1.8;
    for (let k = 0; k < 8; k++) {
        const ang = (k * Math.PI) / 4;
        ctx.save();
        ctx.rotate(ang);
        for (let row = 0; row < 2; row++) {
            const ry = -radius * (1.08 + row * 0.09);
            if ((k + row) % 2 === 0) {
                ctx.beginPath();
                ctx.moveTo(-radius * 0.14, ry);
                ctx.lineTo(radius * 0.14, ry);
                ctx.stroke();
            } else {
                ctx.beginPath();
                ctx.moveTo(-radius * 0.14, ry);
                ctx.lineTo(-radius * 0.03, ry);
                ctx.moveTo(radius * 0.03, ry);
                ctx.lineTo(radius * 0.14, ry);
                ctx.stroke();
            }
        }
        ctx.restore();
    }
    ctx.restore();
}

// Deterministic jagged Wuxia sky/slash lightning bolt
function drawJaggedLightning(ctx, x1, y1, x2, y2, seedBase, glowColor, alpha, webEnhanced) {
    if (alpha <= 0.01) return;
    const segments = 11;
    const dx = x2 - x1, dy = y2 - y1;
    const len = Math.max(1, Math.hypot(dx, dy));
    const nx = -dy / len, ny = dx / len;
    const pts = [[x1, y1]];
    for (let i = 1; i < segments; i++) {
        const u = i / segments;
        const jitter = (seed(seedBase + i * 19.3) - 0.5) * 38 * Math.sin(u * Math.PI);
        pts.push([x1 + dx * u + nx * jitter, y1 + dy * u + ny * jitter]);
    }
    pts.push([x2, y2]);

    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';

    ctx.globalAlpha = clamp(alpha * 0.26);
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = 3.6;
    ctx.beginPath();
    pts.forEach((p, idx) => (idx ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.stroke();

    ctx.globalAlpha = clamp(alpha * 0.55);
    ctx.strokeStyle = '#eef6f8';
    ctx.lineWidth = 1.0;
    ctx.beginPath();
    pts.forEach((p, idx) => (idx ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.stroke();
    ctx.restore();
}

// Calligraphic Vermilion Seal Stamp rendered on canvas during Ultimate impact
function drawCanvasSeal(ctx, cx, cy, chars, color, progress) {
    if (progress <= 0 || progress >= 1) return;
    const slam = progress < 0.18 ? mix(2.1, 1.0, ease(progress / 0.18)) : 1.0;
    const alpha = progress > 0.72 ? (1 - progress) / 0.28 : Math.min(1, progress / 0.12);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(slam, slam);
    ctx.rotate(-0.08);
    ctx.globalAlpha = clamp(alpha * 0.88);
    ctx.strokeStyle = color;
    ctx.fillStyle = 'rgba(165, 28, 24, 0.14)';
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
    ctx.fillText(chars[0] || '绝', 0, -3);
    ctx.fillText(chars[1] || '杀', 0, 17);
    ctx.restore();
}

// 御剑：一笔淡墨勾出的细长剑影，剑尖出锋、剑尾拖丝，不再是实心菱形。
function drawFlyingSpiritSword(ctx, x, y, angle, scale, glowColor, brightColor, alpha, webEnhanced) {
    if (alpha <= 0.01) return;
    const rgbGlow = hexRgb(glowColor);
    const body = [];
    for (let i = 0; i <= 8; i++) body.push([mix(-34, 26, i / 8), 0]);
    const tail = [[-58, 1.5], [-46, 0.6], [-34, 0]];
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    ctx.scale(scale, scale);
    const profile = (u) => Math.min(1, 0.25 + u * 2.2) * (1 - Math.pow(u, 4));
    brushPoly(ctx, body, 3.2, INK_RGB, alpha * 0.58, profile);
    brushPoly(ctx, tail, 1.2, INK_RGB, alpha * 0.22, (u) => 1 - u * 0.6);
    if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
    brushPoly(ctx, body, 1.1, rgbGlow, alpha * 0.4, profile);
    ctx.restore();
}

export function drawMasterEffects(ctx, event, local, sampleAt, target, dir, impactAge, hit, width = 960, webEnhanced = false) {
    const art = masterArts[event?.martialArtId];
    const move = masterMoveFor(event);
    if (!art || !move || local < 160 || local > 1580) return;

    const fade = clamp((1540 - local) / 340);
    const current = sampleAt(Math.min(local, 980));

    // 1. Domain Contrast Wash for Ultimates (一剑霜寒 / 赤霄断魂)
    if (move.ultimate && local >= 340 && local <= 1360) {
        const domainAlpha = smooth((local - 340) / 180) * (1 - smooth((local - 1060) / 300));
        ctx.save();
        ctx.fillStyle = event.martialArtId === 'sword_xuanmo'
            ? `rgba(8, 18, 28, ${domainAlpha * (webEnhanced ? 0.52 : 0.30)})`
            : `rgba(32, 9, 10, ${domainAlpha * (webEnhanced ? 0.54 : 0.32)})`;
        ctx.fillRect(-40, -40, width + 80, 510);
        ctx.restore();
    }

    // 2. Swept Hand-to-Tip Polygon Weapon Ribbon during active slash window
    if (local >= 540 && local <= 1160 && move.style !== 'wanjian') {
        const samples = [];
        const count = move.ultimate ? 16 : 12;
        for (let i = 0; i < count; i++) {
            const t = local - i * 11;
            if (t < 500) break;
            samples.push(sampleAt(t));
        }
        const ribbonFade = clamp((1160 - local) / 220);
        drawSweptWeaponRibbon(ctx, samples, art.glow, art.glowBright, ribbonFade, webEnhanced);
    }

    // 3. Move-Specific Signature Visuals
    if (move.style === 'rise' || move.style === 'crescent' || move.style === 'sweep' || move.style === 'crush' || move.style === 'upper') {
        if (local >= 680 && local <= 1180) {
            const p = clamp((local - 680) / 480);
            const arcFade = (1 - p) * smooth((local - 680) / 70);
            const isUpper = move.style === 'rise' || move.style === 'upper';
            const isCrush = move.style === 'crush';
            const baseAngle = dir === 1
                ? (isUpper ? -0.58 : isCrush ? 0.38 : 0.06)
                : (isUpper ? Math.PI + 0.58 : isCrush ? Math.PI - 0.38 : Math.PI - 0.06);
            const cx = mix(current.root[0] + dir * 40, target[0], 0.55);
            const cy = current.root[1] - (isUpper ? 92 : 76);
            if (webEnhanced && art.weapon === 'blade' && inkAssets.crescent?.complete && inkAssets.crescent.naturalWidth) {
                const radius = 68 + p * 38;
                ctx.save();
                ctx.translate(cx, cy);
                ctx.rotate(baseAngle - Math.PI / 2);
                ctx.globalAlpha = arcFade * 0.75;
                ctx.drawImage(inkAssets.crescent, -radius, -radius, radius * 2, radius * 2);
                ctx.restore();
            } else drawInkGlowCrescent(
                ctx,
                cx,
                cy,
                68 + p * 38,
                baseAngle,
                isCrush ? 2.15 : 2.35,
                (art.weapon === 'blade' ? 24 : 18) * (1 - p * 0.35),
                art.glow,
                art.glowBright,
                arcFade,
                webEnhanced,
            );
        }
        // Ground-scraping ember trail for 残阳撩月
        if (move.style === 'upper' && local >= 360 && local <= 840) {
            ctx.save();
            if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
            for (let i = 0; i < 14; i++) {
                const age = local - 370 - i * 24;
                if (age < 0 || age > 320) continue;
                const q = age / 320;
                const sx = sampleAt(370 + i * 24).tip[0];
                ctx.globalAlpha = (1 - q) * 0.85;
                ctx.fillStyle = i % 2 ? '#fb923c' : '#fef08a';
                ctx.beginPath();
                ctx.arc(sx - dir * q * 18, 326 - q * (18 + (i % 4) * 9), 1.6 + (1 - q) * 2, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.restore();
        }
    }

    if (move.style === 'blink' && local >= 470 && local <= 1120) {
        // Ink-mist clones and piercing frost-cyan line
        for (let k = 0; k < 3; k++) {
            const ghostT = 480 + k * 65;
            const age = local - ghostT;
            if (age < 0 || age > 380) continue;
            const gp = sampleAt(ghostT);
            const q = age / 380;
            ctx.save();
            ctx.globalAlpha = (1 - q) * 0.42;
            ctx.fillStyle = '#0f172a';
            for (let mIdx = 0; mIdx < 6; mIdx++) {
                const ang = mIdx * 1.05 + k;
                ctx.beginPath();
                ctx.ellipse(
                    gp.root[0] + Math.cos(ang) * (12 + q * 28),
                    gp.root[1] - 68 + Math.sin(ang) * (24 + q * 20),
                    10 * (1 - q * 0.5),
                    5 * (1 - q * 0.5),
                    ang,
                    0,
                    Math.PI * 2,
                );
                ctx.fill();
            }
            ctx.restore();
        }
        if (local >= 760 && local <= 1100) {
            const q = clamp((local - 760) / 340);
            const startX = sampleAt(740).tip[0] - dir * 55;
            brushLine(ctx, startX, target[1] + 6, target[0] + dir * 34, target[1] - 4, 6.5 * (1 - q * 0.5), art.glow, (1 - q) * 0.95, 13, webEnhanced, 0);
        }
    }

    if (move.style === 'wave' && local >= 660 && local <= 1160) {
        // Travelling 3-layer Sword-Qi Crescent Projectile (破空剑气)
        const origin = sampleAt(700).tip;
        const fly = clamp((local - 680) / 270);
        const post = clamp((local - 950) / 210);
        const waveX = mix(origin[0], target[0] + (hit ? 0 : dir * 95), hit ? Math.min(1, fly) : fly + post * 0.35);
        const waveY = mix(origin[1], target[1], Math.min(1, fly));
        const waveAlpha = local < 950 ? smooth((local - 660) / 80) : 1 - post;
        drawInkGlowCrescent(
            ctx,
            waveX,
            waveY,
            56 + fly * 18,
            dir === 1 ? 0 : Math.PI,
            1.95,
            21,
            art.glow,
            art.glowBright,
            waveAlpha,
            webEnhanced,
        );
        // Ground wake ripples beneath the flying sword wave
        ctx.save();
        ctx.globalAlpha = waveAlpha * 0.45;
        ctx.strokeStyle = art.glow;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.ellipse(waveX - dir * 18, 328, 34, 5, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
    }

    if (move.style === 'whirl' || move.style === 'spin' || move.style === 'double' || move.style === 'storm') {
        const count = move.style === 'storm' ? 4 : 2;
        for (let k = 0; k < count; k++) {
            const startT = 620 + k * (move.style === 'storm' ? 78 : 135);
            const age = local - startT;
            if (age < 0 || age > 390) continue;
            const q = age / 390;
            const tilt = (k % 2 === 0 ? -0.46 : 0.48) + (k - 1) * 0.16;
            const center = k === count - 1
                ? [mix(current.root[0], target[0], 0.65), target[1]]
                : [current.root[0] + dir * (36 + k * 18), current.root[1] - 74 + (k % 2) * 16];
            drawInkGlowCrescent(
                ctx,
                center[0],
                center[1],
                60 + k * 9 + q * 26,
                (dir === 1 ? 0 : Math.PI) + tilt,
                2.25,
                (art.weapon === 'blade' ? 21 : 16) * (1 - q * 0.35),
                art.glow,
                art.glowBright,
                (1 - q) * 0.92,
                webEnhanced,
            );
        }
    }

    if (move.style === 'taiji') {
        // Rotating Taiji Bagua Seal at sword front, then pierced & shattered at 950ms!
        if (local >= 240 && local <= 1080) {
            const sealOrigin = sampleAt(Math.min(local, 680));
            const sx = sealOrigin.root[0] + dir * 66;
            const sy = sealOrigin.root[1] - 78;
            const sealAlpha = smooth((local - 240) / 140) * (1 - smooth((local - 880) / 190));
            const sealScale = 34 + smooth((local - 240) / 360) * 14 + smooth((local - 850) / 220) * 26;
            drawTaijiBaguaSeal(ctx, sx, sy, sealScale, local * 0.0045 * dir, art.glow, sealAlpha, webEnhanced);
        }
        if (local >= 760 && local <= 1140) {
            const q = clamp((local - 760) / 360);
            const beamStart = sampleAt(740).root[0] + dir * 56;
            brushLine(ctx, beamStart, target[1], target[0] + dir * 28, target[1], 8 * (1 - q * 0.4), art.glow, (1 - q) * 0.95, 21, webEnhanced, 0);
        }
    }

    if (move.style === 'wanjian') {
        // Aerial Taiji Bagua Array + 10 Spirit Swords converging on target (万剑归宗)!
        const caster = sampleAt(Math.min(local, 960));
        const arrayCenter = [caster.root[0] - dir * 12, caster.root[1] - 88];
        if (local >= 280 && local <= 1220) {
            const arrayAlpha = smooth((local - 280) / 180) * (1 - smooth((local - 980) / 240));
            drawTaijiBaguaSeal(ctx, arrayCenter[0], arrayCenter[1], 56, local * 0.0038 * dir, art.glow, arrayAlpha, webEnhanced);
        }
        const swordCount = 10;
        for (let i = 0; i < swordCount; i++) {
            const appearT = 360 + i * 24;
            const launchT = 650 + i * 22;
            const landT = 950;
            if (local < appearT || local > 1220) continue;

            const ringAng = -Math.PI * 0.65 + (i / (swordCount - 1)) * Math.PI * 1.3;
            const spawnX = arrayCenter[0] + Math.cos(ringAng) * 66 * dir;
            const spawnY = arrayCenter[1] + Math.sin(ringAng) * 58 - 18;
            const destX = target[0] + (hit ? (i - 4.5) * 5 : dir * (35 + i * 8));
            const destY = hit ? target[1] + ((i % 3) - 1) * 14 : 326;

            if (local <= launchT) {
                const formAlpha = smooth((local - appearT) / 110);
                const aim = Math.atan2(destY - spawnY, destX - spawnX);
                drawFlyingSpiritSword(ctx, spawnX, spawnY, aim, 0.85, art.glow, art.glowBright, formAlpha, webEnhanced);
            } else {
                const flight = clamp((local - launchT) / Math.max(60, landT - launchT));
                const postFade = 1 - smooth((local - landT) / 240);
                const arcLift = -Math.sin(flight * Math.PI) * (32 + (i % 3) * 18);
                const sx = mix(spawnX, destX, ease(flight));
                const sy = mix(spawnY, destY, ease(flight)) + arcLift;
                const prevF = clamp(flight - 0.14);
                const px = mix(spawnX, destX, ease(prevF));
                const py = mix(spawnY, destY, ease(prevF)) - Math.sin(prevF * Math.PI) * (32 + (i % 3) * 18);
                const aim = Math.atan2(destY - spawnY, destX - spawnX);

                // Glowing cyan wake behind each spirit sword
                ctx.save();
                if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
                ctx.globalAlpha = postFade * 0.68;
                ctx.strokeStyle = art.glow;
                ctx.lineWidth = 3.2;
                ctx.beginPath();
                ctx.moveTo(px, py);
                ctx.lineTo(sx, sy);
                ctx.stroke();
                ctx.restore();

                drawFlyingSpiritSword(ctx, sx, sy, aim, 0.92, art.glow, art.glowBright, postFade, webEnhanced);
            }
        }
    }

    if (move.style === 'ground_wave' && local >= 700 && local <= 1240) {
        // 赤练裂地：一道淡墨裂痕贴地奔涌，朱砂烟尘与墨烟升腾散去——没有实心锥体。
        const slamOrigin = sampleAt(740).tip[0];
        const waveP = clamp((local - 730) / 260);
        const fadeOut = 1 - smooth((local - 960) / 280);
        const frontX = mix(slamOrigin, target[0], ease(waveP));
        const rgbGlow = hexRgb(art.glow);
        ctx.save();
        if (webEnhanced && inkAssets.fissure?.complete && inkAssets.fissure.naturalWidth && waveP > 0) {
            const distance = Math.abs(target[0] - slamOrigin);
            ctx.save();
            ctx.translate(slamOrigin, 330);
            ctx.scale(dir, 1);
            ctx.beginPath();
            ctx.rect(0, -90, distance * ease(waveP), 110);
            ctx.clip();
            ctx.globalAlpha = fadeOut * 0.72;
            ctx.drawImage(inkAssets.fissure, 0, -74, distance, 100);
            ctx.restore();
        }
        const fissure = [];
        for (let i = 0; i <= 22; i++) {
            const u = i / 22;
            fissure.push([mix(slamOrigin, frontX, u), 329 + (seed(i * 5 + 3) - 0.5) * 5 * (1 - u * 0.3)]);
        }
        const taper = (u) => Math.pow(1 - clamp(u), 0.6);
        brushPoly(ctx, fissure, 3.4, INK_RGB, fadeOut * 0.46, taper);
        for (let b = 0; b < 4; b++) {
            const at = fissure[3 + b * 4];
            const dirY = b % 2 ? -1 : 1;
            const branch = [at, [at[0] + dir * 9, at[1] + dirY * 3], [at[0] + dir * 15, at[1] + dirY * 1], [at[0] + dir * 24, at[1] + dirY * 5]];
            brushPoly(ctx, branch, 1.2, INK_RGB, fadeOut * 0.3, taper);
        }
        for (let i = 0; i < 13; i++) {
            const u = (i + 1) / 13;
            if (waveP < u * 0.9) continue;
            const age = clamp((local - (730 + u * 210)) / 520);
            const px = mix(slamOrigin, target[0], u);
            const rise = age * (26 + seed(i) * 30);
            const rx = (14 + seed(i + 4) * 18) * (0.6 + age);
            const ry = (4 + seed(i + 9) * 5) * (0.6 + age * 0.9);
            ctx.fillStyle = `rgb(${INK_RGB})`;
            ctx.globalAlpha = (1 - age) * 0.11 * fadeOut;
            ctx.beginPath();
            ctx.ellipse(px, 326 - rise * 0.5, rx, ry, 0, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = `rgb(${rgbGlow})`;
            ctx.globalAlpha = (1 - age) * 0.06 * fadeOut;
            ctx.beginPath();
            ctx.ellipse(px + dir * 6, 324 - rise * 0.8, rx * 0.7, ry * 0.8, 0, 0, Math.PI * 2);
            ctx.fill();
            if (i % 2 === 0 && age < 0.9) {
                ctx.strokeStyle = `rgb(${INK_RGB})`;
                ctx.lineWidth = 1.1;
                ctx.globalAlpha = (1 - age) * 0.16 * fadeOut;
                ctx.beginPath();
                ctx.moveTo(px, 328);
                ctx.bezierCurveTo(px - 6, 328 - rise * 0.5, px + 8, 328 - rise * 0.9, px + dir * 3, 328 - rise * 1.3);
                ctx.stroke();
            }
        }
        if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
        brushPoly(ctx, fissure, 1.2, rgbGlow, fadeOut * 0.5, taper);
        ctx.restore();
    }

    if (move.style === 'domain_sword' && local >= 620 && local <= 1420) {
        // 绝技·一剑霜寒: Full-stage frost-ink horizon slash + sky lightning + seal!
        const slashAge = local - 680;
        if (slashAge >= 0) {
            const p = clamp(slashAge / 680);
            const lineAlpha = (1 - smooth((slashAge - 260) / 420)) * smooth(slashAge / 45);
            const slashY = target[1] - 4;

            brushLine(ctx, width * 0.03, slashY + dir * 10, width * 0.97, slashY - dir * 10, 17 * (1 - p * 0.5), art.glow, lineAlpha, 71, webEnhanced, -6 * dir);

            if (slashAge > 160 && slashAge < 620) {
                const boltAlpha = 1 - smooth((slashAge - 240) / 360);
                drawJaggedLightning(ctx, target[0] - 45, 24, target[0] + 6, slashY, 17, art.glow, boltAlpha, webEnhanced);
                drawJaggedLightning(ctx, width * 0.14, slashY + 8, width * 0.86, slashY - 8, 43, art.glowBright, boltAlpha * 0.75, webEnhanced);
            }
        }
    }

    if (move.style === 'domain_blade' && local >= 660 && local <= 1440) {
        // 绝技·赤霄断魂: Colossal diagonal blood-moon rift + crimson sky thunder!
        const slashAge = local - 740;
        if (slashAge >= 0) {
            const p = clamp(slashAge / 680);
            const alpha = (1 - smooth((slashAge - 260) / 420)) * smooth(slashAge / 55);
            drawInkGlowCrescent(
                ctx,
                target[0] - dir * 24,
                target[1] - 18,
                118 + p * 36,
                dir === 1 ? 0.34 : Math.PI - 0.34,
                2.55,
                34 * (1 - p * 0.4),
                art.glow,
                art.glowBright,
                alpha,
                webEnhanced,
            );

            // 一笔斜贯全场的朱砂墨痕
            const x1 = target[0] - dir * 240, y1 = 42;
            const x2 = target[0] + dir * 165, y2 = 342;
            brushLine(ctx, x1, y1, x2, y2, 15 * (1 - p * 0.5), art.glow, alpha, 29, webEnhanced, 10 * dir);

            if (slashAge < 540) {
                const boltAlpha = 1 - smooth((slashAge - 180) / 360);
                drawJaggedLightning(ctx, target[0] + dir * 20, 14, target[0], 328, 91, art.glow, boltAlpha, webEnhanced);
            }
        }
    }

    // 4. Hit-Confirmed Impact Burst (never drawn on dodge!)
    if (hit && impactAge >= 0 && impactAge < 620) {
        const p = impactAge / 620;
        const ringAlpha = (1 - p) * 0.88;
        ctx.save();
        // Expanding ink-splatter droplets
        const dropCount = move.ultimate ? 26 : move.signature ? 18 : 11;
        for (let i = 0; i < dropCount; i++) {
            const ang = i * 2.39996 + (event.action || 0);
            const speed = (38 + seed(i * 11) * (move.ultimate ? 135 : 82)) * ease(p * 1.25);
            const dx = target[0] + Math.cos(ang) * speed;
            const dy = target[1] + Math.sin(ang) * speed * 0.78 + p * p * 28;
            const r = (1.8 + seed(i * 23) * 3.4) * (1 - p * 0.55);
            ctx.globalAlpha = ringAlpha * 0.85;
            ctx.fillStyle = i % 3 === 0 ? art.glow : art.ink;
            ctx.beginPath();
            ctx.ellipse(dx, dy, r * 1.7, r * 0.9, ang, 0, Math.PI * 2);
            ctx.fill();
        }

        // Luminous shockwave rings & cross-flare
        if (webEnhanced) ctx.globalCompositeOperation = 'lighter';
        const rings = move.ultimate ? 3 : 2;
        for (let rIdx = 0; rIdx < rings; rIdx++) {
            const rad = 14 + p * (58 + rIdx * 28);
            ctx.globalAlpha = ringAlpha * (0.42 - rIdx * 0.12);
            ctx.strokeStyle = art.glow;
            ctx.lineWidth = (move.ultimate ? 1.8 : 1.1) * (1 - p);
            ctx.beginPath();
            ctx.ellipse(target[0], target[1], rad * 0.72, rad, 0.18 * dir, 0, Math.PI * 2);
            ctx.stroke();
        }
        ctx.restore();

        if (move.ultimate) {
            drawCanvasSeal(
                ctx,
                target[0] + dir * 46,
                target[1] - 58,
                event.martialArtId === 'sword_xuanmo' ? '霜寒' : '断魂',
                art.sealColor,
                p,
            );
        }
    }
}

// ============================================================================
// Web-Exclusive Dynamic Wuxia Scenery & Deterministic Ground Battle Stains
// (Active ONLY when InkStage is called with options.webEnhanced === true;
//  Bot GIF capture.js omits options and keeps its single static ink-bg.png!)
// ============================================================================
const SCENE_PALETTES = {
    sunset: {
        washTop: 'rgba(251, 232, 206, 0.34)',
        washBottom: 'rgba(244, 238, 224, 0.08)',
        sunColor: 'rgba(196, 56, 32, 0.78)',
        sunHalo: 'rgba(234, 112, 53, 0.22)',
        sunX: 0.73,
        sunY: 118,
        sunR: 54,
        ridgeFar: 'rgba(72, 68, 62, 0.16)',
        ridgeNear: 'rgba(45, 46, 42, 0.22)',
        stalkColor: 'rgba(38, 49, 41, 0.26)',
        leafColors: ['#2d3b32', '#4c5f4e', '#a94432'],
        mode: 'bamboo',
    },
    snow: {
        washTop: 'rgba(216, 232, 242, 0.38)',
        washBottom: 'rgba(240, 246, 250, 0.12)',
        sunColor: 'rgba(245, 250, 255, 0.82)',
        sunHalo: 'rgba(125, 211, 252, 0.24)',
        sunX: 0.27,
        sunY: 106,
        sunR: 44,
        ridgeFar: 'rgba(58, 78, 92, 0.18)',
        ridgeNear: 'rgba(35, 52, 66, 0.24)',
        stalkColor: 'rgba(52, 69, 78, 0.24)',
        leafColors: ['#ffffff', '#bae6fd', '#64748b'],
        mode: 'snow',
    },
    bloodmoon: {
        washTop: 'rgba(68, 20, 24, 0.30)',
        washBottom: 'rgba(32, 16, 18, 0.12)',
        sunColor: 'rgba(185, 28, 28, 0.82)',
        sunHalo: 'rgba(239, 68, 68, 0.28)',
        sunX: 0.50,
        sunY: 112,
        sunR: 62,
        ridgeFar: 'rgba(54, 28, 30, 0.22)',
        ridgeNear: 'rgba(34, 18, 20, 0.28)',
        stalkColor: 'rgba(46, 24, 24, 0.28)',
        leafColors: ['#dc2626', '#fb923c', '#291818'],
        mode: 'ember',
    },
};

export function drawWebSceneBackdrop(ctx, width, time, sceneTheme = 'sunset', windImpulse = 0) {
    if (!sceneTheme || sceneTheme === 'classic') return;
    const pal = SCENE_PALETTES[sceneTheme] || SCENE_PALETTES.sunset;

    ctx.save();
    // 1. Subtle atmospheric color glaze over paper texture
    const grad = ctx.createLinearGradient(0, 0, 0, 340);
    if (grad && grad.addColorStop) {
        grad.addColorStop(0, pal.washTop);
        grad.addColorStop(1, pal.washBottom);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, width, 345);
    }

    // 2. Celestial Sun / Winter Moon / Crimson Eclipse Moon
    const sx = width * pal.sunX;
    const sy = pal.sunY + Math.sin(time / 2400) * 2.5;
    ctx.fillStyle = pal.sunHalo;
    ctx.beginPath();
    ctx.arc(sx, sy, pal.sunR * 1.42, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = pal.sunColor;
    ctx.beginPath();
    ctx.arc(sx, sy, pal.sunR, 0, Math.PI * 2);
    ctx.fill();

    // Drifting mist ribbon across the celestial disc
    const mistDrift = Math.sin(time / 3200) * 22;
    ctx.fillStyle = 'rgba(248, 246, 238, 0.36)';
    ctx.beginPath();
    ctx.ellipse(sx + mistDrift, sy + pal.sunR * 0.28, pal.sunR * 1.55, 8, 0, 0, Math.PI * 2);
    ctx.fill();

    // 3. Distant Sumi-Ink Mountain Ridges
    for (const [baseY, amp, freq, fill] of [
        [278, 46, 0.0065, pal.ridgeFar],
        [308, 30, 0.0095, pal.ridgeNear],
    ]) {
        ctx.fillStyle = fill;
        ctx.beginPath();
        ctx.moveTo(0, 330);
        for (let x = 0; x <= width; x += 24) {
            const h = Math.sin(x * freq + baseY) * amp + Math.cos(x * freq * 2.1) * (amp * 0.42);
            ctx.lineTo(x, baseY - Math.abs(h));
        }
        ctx.lineTo(width, 330);
        ctx.closePath();
        ctx.fill();
    }

    // 4. Swaying Ink Bamboo Stalks at Arena Edges
    const sway = Math.sin(time / 950) * 6 + windImpulse * 14;
    ctx.strokeStyle = pal.stalkColor;
    ctx.lineCap = 'round';
    for (const [bx, leanSign, height, thick] of [
        [width * 0.045, 1, 235, 3.2],
        [width * 0.078, 1, 190, 2.2],
        [width * 0.935, -1, 225, 3.0],
        [width * 0.962, -1, 175, 2.0],
    ]) {
        const topX = bx + sway * 0.9 + leanSign * 14;
        const topY = 330 - height;
        ctx.lineWidth = thick;
        ctx.beginPath();
        ctx.moveTo(bx, 330);
        ctx.quadraticCurveTo(bx + sway * 0.35, 330 - height * 0.55, topX, topY);
        ctx.stroke();

        // Bamboo leaf clusters
        ctx.fillStyle = pal.stalkColor;
        for (let c = 0; c < 3; c++) {
            const u = 0.45 + c * 0.24;
            const lx = mix(bx, topX, u);
            const ly = 330 - height * u;
            for (let b = -1; b <= 1; b += 2) {
                const ang = b * 0.55 + sway * 0.015;
                ctx.save();
                ctx.translate(lx, ly);
                ctx.rotate(ang);
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.quadraticCurveTo(10 * b, -4, 22 * b, 3);
                ctx.quadraticCurveTo(10 * b, 2, 0, 0);
                ctx.fill();
                ctx.restore();
            }
        }
    }
    ctx.restore();
}

// Deterministic Ground Ink & Vermilion Stains left by Strike Impacts (scrub-safe!)
export function drawWebBattleStains(ctx, battle, time, frameAt) {
    ctx.save();
    for (let idx = 0; idx < battle.events.length; idx++) {
        const ev = battle.events[idx];
        if (ev.type !== 'damage' || ev.cause !== 'strike' || ev.time > time) continue;
        const age = time - ev.time;
        const appear = smooth(age / 140);
        const turn = battle.events.find((e) => e.type === 'turn_start' && e.action === ev.action);
        const side = ev.target || 'b';
        const victimX = frameAt(side, ev.time, turn).x;
        const heavy = Boolean(ev.crit || (ev.amount || 0) >= (ev.maxHp || 500) * 0.16);
        const count = heavy ? 5 : 2;
        for (let k = 0; k < count; k++) {
            const hSeed = idx * 31 + k * 17;
            const ox = (seed(hSeed) - 0.5) * (heavy ? 76 : 42);
            const oy = (seed(hSeed + 5) - 0.35) * 9;
            const rx = (4 + seed(hSeed + 9) * (heavy ? 13 : 7)) * appear;
            const ry = Math.max(1.1, rx * 0.24);
            const isVermilion = ev.crit || k === 0;
            ctx.globalAlpha = isVermilion ? 0.24 : 0.18;
            ctx.fillStyle = isVermilion ? '#8c231c' : '#1f2623';
            ctx.beginPath();
            ctx.ellipse(victimX + ox, 330 + oy, rx, ry, (seed(hSeed + 3) - 0.5) * 0.3, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    ctx.restore();
}

// Wind-reactive foreground drifting bamboo leaves / snow / crimson embers
export function drawWebSceneForeground(ctx, width, time, sceneTheme = 'sunset', windImpulse = 0) {
    if (!sceneTheme || sceneTheme === 'classic') return;
    const pal = SCENE_PALETTES[sceneTheme] || SCENE_PALETTES.sunset;
    const count = 18;
    ctx.save();
    for (let i = 0; i < count; i++) {
        const speedX = 0.028 + seed(i * 7) * 0.026;
        const speedY = pal.mode === 'ember' ? -(0.018 + seed(i * 11) * 0.022) : 0.022 + seed(i * 11) * 0.02;
        const rawX = seed(i * 3) * width + time * speedX + windImpulse * 48;
        const rawY = seed(i * 5) * 380 + time * speedY;
        const x = ((rawX % (width + 60)) + (width + 60)) % (width + 60) - 30;
        const y = ((rawY % 390) + 390) % 390;
        const color = pal.leafColors[i % pal.leafColors.length];

        ctx.save();
        ctx.translate(x, y);
        if (pal.mode === 'snow') {
            ctx.globalAlpha = 0.55;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(0, 0, 1.5 + seed(i * 19) * 2.2, 0, Math.PI * 2);
            ctx.fill();
        } else if (pal.mode === 'ember') {
            ctx.globalCompositeOperation = 'lighter';
            ctx.globalAlpha = 0.48 + Math.sin(time / 180 + i) * 0.2;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.ellipse(0, 0, 2.8, 1.3, time * 0.003 + i, 0, Math.PI * 2);
            ctx.fill();
        } else {
            // Bamboo leaf spinning in the sword-wind
            const rot = time * 0.0022 * (i % 2 ? 1 : -1) + i + windImpulse * 0.6;
            const s = 5 + seed(i * 23) * 4.5;
            ctx.rotate(rot);
            ctx.globalAlpha = 0.46;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.moveTo(-s, 0);
            ctx.quadraticCurveTo(0, -s * 0.42, s, 0);
            ctx.quadraticCurveTo(0, s * 0.42, -s, 0);
            ctx.fill();
        }
        ctx.restore();
    }
    ctx.restore();
}
