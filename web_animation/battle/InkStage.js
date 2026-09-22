import { stateAt, statusLabels } from './replay.js';
import { techniqueFor, legacyTechniqueFor, weaponFor } from './martialVisuals.js';
import { drawWeapon } from './inkWeapons.js';
import { drawAura, drawTrigger, drawFootwork } from './inkEffects.js';
import { drawTechnique, drawImpact, drawPreparation, drawSampleAccent } from './inkStrikes.js';
import { contactTime, impactFor, plantedFoot } from './choreography.js';
import { sampleMove } from './sampleMotion.js';
import { moveMotion } from './moveMotion.js';
import { profileFor, themeColors } from './moveProfiles.js';
import { drawMoveTheme } from './moveEffects.js';
import { constrainRig } from './rig.js';
import { swordSequenceFor } from './swordSequences.js';
import { drawSwordSequenceEffects } from './swordEffects.js';
import { motionVariantFor } from './motionVariants.js';
import { isNewMove, newMoveFor } from './newMartialMotion.js';
import { drawCurvedFigure } from './curvedFigure.js';
import { drawNewMartialEffects } from './newMartialEffects.js';
import { expandedMoveFor, drawExpandedEffects } from './expandedArts.js';
// Head, neck, waist, rear elbow/hand, sword elbow/hand, rear knee/foot, front knee/foot.
const poses = {
    idle: { points: [[0, -137], [0, -116], [-7, -65], [-28, -95], [-19, -71], [24, -101], [39, -89], [-24, -34], [-39, 0], [20, -34], [39, 0]], sword: -.45, lean: 0 },
    gather: { points: [[-12, -129], [-10, -108], [-4, -59], [-34, -98], [-53, -113], [14, -102], [5, -128], [-28, -29], [-49, 0], [24, -29], [50, 0]], sword: -1.85, lean: -.06 },
    dash: { points: [[20, -119], [12, -99], [-10, -59], [-34, -85], [-61, -75], [31, -83], [51, -78], [-44, -21], [-70, -1], [27, -33], [51, 0]], sword: -.2, lean: .06 },
    strike: { points: [[30, -114], [21, -94], [-11, -53], [-35, -76], [-65, -95], [49, -91], [79, -102], [-43, -26], [-75, 0], [39, -41], [58, 0]], sword: -.12, lean: 0 },
    hit: { points: [[-27, -126], [-21, -105], [1, -62], [-40, -85], [-48, -63], [4, -83], [24, -55], [-25, -29], [-39, 0], [23, -32], [43, 0]], sword: .8, lean: -.13 },
    dodge: { points: [[-37, -92], [-25, -77], [3, -45], [-46, -62], [-70, -70], [-3, -65], [24, -82], [-26, -20], [-50, 0], [35, -24], [60, 0]], sword: -.5, lean: -.12 },
    fallen: { points: [[-84, -17], [-63, -17], [-15, -14], [-54, -7], [-78, -2], [-33, -6], [-14, -2], [15, -5], [46, 0], [16, -21], [49, 0]], sword: .03, lean: 0 },
    salute: { points: [[0, -143], [0, -122], [0, -68], [-22, -106], [7, -100], [25, -103], [11, -100], [-15, -36], [-23, 0], [13, -36], [22, 0]], sword: 1.45, lean: 0 },
    slash: { points: [[22, -120], [16, -100], [-8, -57], [-35, -82], [-49, -57], [40, -74], [74, -69], [-42, -26], [-70, 0], [32, -35], [55, 0]], sword: .3, lean: .04 },
    rise: { points: [[15, -131], [10, -110], [-6, -62], [-31, -97], [-46, -72], [41, -129], [62, -153], [-39, -26], [-68, 0], [28, -38], [45, 0]], sword: -.85, lean: .05 },
    overhead: { points: [[-6, -131], [-6, -110], [-5, -60], [-18, -130], [2, -158], [15, -138], [11, -168], [-27, -29], [-43, 0], [21, -32], [45, 0]], sword: -2.4, lean: -.08 },
    low: { points: [[17, -92], [7, -74], [-16, -40], [-27, -67], [-54, -48], [39, -53], [74, -38], [-39, -18], [-66, 0], [39, -18], [73, 0]], sword: .02, lean: 0 },
    palmIdle: { points: [[-3, -137], [-2, -116], [-6, -65], [-17, -91], [5, -85], [23, -105], [39, -121], [-24, -34], [-39, 0], [20, -34], [39, 0]], sword: 0, lean: 0 },
    palm: { points: [[18, -121], [12, -102], [-8, -61], [-18, -85], [4, -92], [46, -95], [82, -100], [-33, -27], [-62, 0], [24, -35], [49, 0]], sword: 0, lean: .03 },
    kickGather: { points: [[-7, -139], [-6, -118], [-3, -66], [-32, -94], [-19, -72], [19, -96], [36, -119], [-21, -30], [-30, 0], [32, -73], [29, -43]], sword: 0, lean: -.1 },
    kick: { points: [[-26, -138], [-21, -118], [-8, -70], [-42, -92], [-56, -106], [2, -107], [19, -126], [-24, -29], [-35, 0], [50, -89], [105, -111]], sword: 0, lean: -.04 },
    lowKick: { points: [[-22, -92], [-12, -73], [-9, -39], [-31, -59], [-45, -29], [11, -65], [36, -76], [-31, -18], [-43, 0], [43, -19], [106, -12]], sword: 0, lean: 0 },
    throwGather: { points: [[-6, -136], [-5, -115], [-4, -67], [-24, -96], [-13, -76], [-18, -117], [-35, -130], [-23, -34], [-39, 0], [20, -34], [39, 0]], sword: 0, lean: -.08 },
    throw: { points: [[12, -135], [8, -114], [-2, -66], [-19, -96], [-34, -82], [37, -106], [69, -104], [-28, -32], [-43, 0], [20, -35], [40, 0]], sword: -.1, lean: .04 },
    pluckIdle: { points: [[0, -140], [0, -119], [-3, -67], [-23, -96], [-29, -89], [23, -99], [34, -88], [-20, -34], [-36, 0], [20, -34], [36, 0]], sword: 0, lean: 0 },
    pluck: { points: [[4, -133], [4, -112], [-3, -67], [-21, -96], [-42, -83], [19, -91], [58, -81], [-20, -34], [-36, 0], [20, -34], [36, 0]], sword: 0, lean: .04 },
    pickup: { points: [[35, -75], [21, -59], [-11, -41], [-27, -27], [-29, -6], [42, -32], [48, -5], [-39, -22], [-50, 0], [26, -24], [47, 0]], sword: 0, lean: 0 },
    recoil: { points: [[-34, -109], [-23, -91], [4, -55], [-40, -78], [-57, -45], [0, -68], [28, -43], [-31, -24], [-50, 0], [31, -24], [61, 0]], sword: .95, lean: -.12 },
    bound: { points: [[9, -146], [4, -126], [-6, -77], [-30, -111], [-49, -123], [29, -115], [44, -134], [-35, -67], [-51, -40], [23, -52], [9, -25]], sword: -1.1, lean: .03 },
    reverse: { points: [[-9, -127], [-6, -108], [1, -62], [17, -93], [40, -102], [-35, -99], [-62, -122], [-27, -32], [-45, 0], [30, -29], [51, 0]], sword: -2.5, lean: -.02 },
    finish: { points: [[30, -103], [20, -85], [-6, -48], [-40, -76], [-58, -93], [49, -60], [78, -26], [-39, -25], [-74, 0], [37, -25], [63, 0]], sword: .78, lean: .03 },
    fan: { points: [[0, -137], [0, -115], [-4, -65], [-34, -111], [-65, -123], [38, -107], [70, -113], [-22, -32], [-42, 0], [21, -34], [41, 0]], sword: -.15, lean: 0 },
    strum: { points: [[12, -123], [8, -105], [-3, -64], [-29, -101], [-63, -113], [39, -84], [67, -65], [-27, -30], [-44, 0], [24, -32], [46, 0]], sword: 0, lean: .04 },
    victorySheath: { points: [[0, -146], [0, -124], [-1, -70], [-16, -88], [-1, -77], [18, -99], [5, -74], [-15, -36], [-25, 0], [14, -36], [23, 0]], sword: 2.95, lean: 0 },
    victoryRaise: { points: [[0, -146], [0, -124], [-1, -70], [-22, -104], [-29, -78], [28, -147], [32, -179], [-18, -35], [-30, 0], [17, -37], [31, 0]], sword: -1.45, lean: 0 },
    victoryBow: { points: [[24, -123], [16, -105], [-3, -64], [-13, -89], [13, -82], [32, -87], [17, -81], [-17, -32], [-29, 0], [17, -34], [30, 0]], sword: 1.5, lean: .02 },
    victoryRest: { points: [[-9, -138], [-6, -117], [0, -66], [-22, -90], [-11, -61], [16, -91], [28, -54], [-16, -32], [-28, 0], [18, -32], [31, 0]], sword: 1.12, lean: 0 },
    victoryKneel: { points: [[8, -109], [4, -89], [-10, -44], [-20, -73], [-9, -43], [23, -67], [35, -30], [-27, -19], [-41, -1], [31, -36], [51, 0]], sword: 1.35, lean: .02 },
    victoryWipe: { points: [[0, -141], [0, -119], [-3, -68], [-20, -109], [10, -146], [20, -92], [33, -61], [-18, -34], [-29, 0], [15, -34], [28, 0]], sword: .95, lean: 0 },
    victoryBack: { points: [[-3, -145], [-2, -123], [0, -69], [-23, -94], [-15, -69], [-15, -94], [-24, -65], [-17, -33], [-28, 0], [16, -35], [28, 0]], sword: 1.1, lean: -.02 },
};
const clamp = (x) => Math.max(0, Math.min(1, x));
const smooth = (x) => { const v = clamp(x); return v * v * (3 - 2 * v); };
function blend(a, b, t) {
    const f = clamp(t);
    const shoulders = a.shoulders || b.shoulders ? [0, 1].map(i => {
        const start = a.shoulders?.[i] || a.points[1], end = b.shoulders?.[i] || b.points[1];
        return [start[0] + (end[0] - start[0]) * f, start[1] + (end[1] - start[1]) * f];
    }) : undefined;
    return { points: a.points.map((p, i) => [p[0] + (b.points[i][0] - p[0]) * f, p[1] + (b.points[i][1] - p[1]) * f]),
        sword: a.sword + (b.sword - a.sword) * f, lean: a.lean + (b.lean - a.lean) * f, shoulders };
}
function stepping(pose, progress, distance, backwards = false) {
    const result = { ...pose, points: pose.points.map(p => [...p]), lean: 0 };
    const sign = backwards ? -1 : 1;
    const bob = Math.abs(Math.sin(progress * Math.PI * 3)) * 4;
    for (let i = 0; i <= 6; i++)
        result.points[i][1] -= bob;
    for (const [knee, foot, offset] of [[7, 8, 0], [9, 10, .5]]) {
        const [x, y] = plantedFoot(progress, 0, distance, offset);
        const footX = sign * x + (offset === 0 ? -20 : 20);
        result.points[foot] = [footX, y];
        const hip = result.points[2];
        const dx = footX - hip[0], dy = y - hip[1];
        const length = Math.max(1, Math.hypot(dx, dy));
        const bend = Math.sqrt(Math.max(0, 48 * 48 - length * length / 4));
        result.points[knee] = [(hip[0] + footX) / 2 + dy / length * bend, (hip[1] + y) / 2 - dx / length * bend];
    }
    return result;
}
function sequence(entries, time) {
    for (let i = 1; i < entries.length; i++)
        if (time < entries[i][0]) {
            return blend(entries[i - 1][1], entries[i][1], smooth((time - entries[i - 1][0]) / (entries[i][0] - entries[i - 1][0])));
        }
    return entries[entries.length - 1][1];
}
function stroke(ctx, points, width, color) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.moveTo(...points[0]);
    points.slice(1).forEach(p => ctx.lineTo(...p));
    ctx.stroke();
}
function fighter(ctx, x, side, pose, time, weapon, alpha = 1, lift = 0, sheathed = false, artId) {
    drawCurvedFigure(ctx, x, side === 'a' ? 1 : -1, pose, time, weapon, alpha, lift, sheathed, artId);
}
function motionPoses(technique, weapon, type) {
    const resting = weapon === 'zither' ? poses.pluckIdle : weapon === 'unarmed' ? poses.palmIdle : poses.idle;
    const idle = { ...resting, points: resting.points.map((p, i) => [p[0], p[1] - (i <= 6 ? 17 : 0)]) };
    let gather = poses.gather;
    let strike = poses.strike;
    switch (technique.motion) {
        case 'slash':
        case 'flurry':
            strike = poses.slash;
            break;
        case 'rise':
            gather = poses.low;
            strike = poses.rise;
            break;
        case 'cleave':
            gather = poses.overhead;
            strike = weapon === 'unarmed' ? poses.palm : poses.finish;
            break;
        case 'sweep':
            gather = poses.gather;
            strike = type === 'leg' ? poses.lowKick : poses.low;
            break;
        case 'leap':
            gather = poses.low;
            strike = poses.slash;
            break;
        case 'draw':
            gather = poses.low;
            strike = poses.strike;
            break;
        case 'palm':
            gather = poses.palmIdle;
            strike = poses.palm;
            break;
        case 'kick':
            gather = poses.kickGather;
            strike = poses.kick;
            break;
        case 'throw':
            gather = poses.throwGather;
            strike = poses.throw;
            break;
        case 'pluck':
            gather = poses.pluckIdle;
            strike = poses.pluck;
            break;
    }
    if (technique.pattern === 'fan' || technique.pattern === 'rain')
        gather = poses.fan;
    if (technique.pattern === 'crescendo') {
        gather = poses.fan;
        strike = poses.strum;
    }
    if (weapon === 'spear') {
        // The rear hand holds the same shaft as the leading hand.
        strike = { ...strike, points: strike.points.map(p => [...p]) };
        strike.points[4] = [strike.points[6][0] - 65 * Math.cos(strike.sword), strike.points[6][1] - 65 * Math.sin(strike.sword)];
    }
    if (weapon === 'katana' && technique.motion === 'draw') {
        gather = { ...poses.low, points: poses.low.points.map(p => [...p]) };
        gather.points[5] = [15, -65];
        gather.points[6] = [3, -42];
        strike = poses.slash;
    }
    return { idle, gather, strike };
}
export function poseAt(battle, side, time, width, turn, mode = 'mixed') {
    const dir = side === 'a' ? 1 : -1;
    const actor = side === 'a' ? battle.attacker : battle.defender;
    const weapon = weaponFor(actor);
    const home = width * (side === 'a' ? .235 : .765);
    const ranged = weapon === 'needles' || weapon === 'zither';
    const reach = weapon === 'spear' ? 210 : weapon === 'brush' ? 113 : weapon === 'unarmed' ? 94 : 165;
    const travel = ranged ? 0 : width * .53 - reach;
    let x = home;
    let lift = 0;
    let opacity = 1, blink = 0;
    const state = stateAt(battle, time);
    const hp = state.hp[side];
    const victory = battle.events.find(e => e.type === 'victory_start' && e.time <= time);
    let victorySheathed = false;
    const local = turn ? time - turn.time : -1;
    const events = turn ? battle.events.filter(e => e.action === turn.action) : [];
    const attack = events.find(e => e.type === 'attack');
    const variant = motionVariantFor(battle, attack, mode);
    const technique = (variant === 'legacy' ? legacyTechniqueFor : techniqueFor)(attack, actor);
    const motion = motionPoses(technique, weapon, actor.martialArt.type);
    let pose = blend(motion.idle, motion.gather, .05 + Math.sin(time / 530) * .025);
    const outcome = events.find(e => e.type === 'dodge' || (e.type === 'damage' && e.cause === 'strike'));
    const victim = turn?.actor === 'a' ? battle.defender : battle.attacker;
    const impact = impactFor(outcome, victim.stats.hp, technique);
    const contact = outcome && turn ? outcome.time - turn.time : 950;
    const actionTime = contactTime(local, contact, impact.hold);
    if (turn && attack && local >= 0 && local < 1740) {
        if (turn.actor === side) {
            const t = actionTime;
            const stepProgress = clamp((t - 380) / 460);
            const p = actor.qinggong?.id === 'lightning_flash' ? smooth(stepProgress ** 1.5) :
                actor.qinggong?.id === 'shadow_drift' ? smooth(stepProgress) : stepProgress;
            const aerial = technique.motion === 'leap' || technique.motion === 'kick';
            const draw = technique.motion === 'draw';
            const advance = draw ? smooth((t - 745) / 205) : p * .76 + smooth((t - 840) / 110) * .24;
            x += dir * travel * advance;
            pose = sequence([[0, motion.idle], [240, blend(motion.idle, motion.gather, .4)], [420, motion.gather],
                [790, motion.gather], [950, motion.strike], [1040, motion.strike], [1190, blend(motion.strike, motion.idle, .32)]], t);
            if (!ranged && !draw && t > 380 && t < 840) {
                if (aerial) {
                    pose = sequence([[380, motion.gather], [570, poses.bound], [780, motion.gather], [950, motion.strike]], t);
                    lift = -70 * Math.sin(Math.PI * clamp((t - 380) / 610));
                }
                else {
                    const gait = stepping(blend(poses.dash, motion.gather, p * .65), p, travel * .76);
                    pose = blend(motion.gather, gait, smooth((t - 380) / 60) * (1 - smooth((t - 780) / 60)));
                }
            }
            if (aerial && t >= 840 && t < 990)
                lift = -70 * Math.sin(Math.PI * clamp((t - 380) / 610));
            if (technique.motion === 'flurry' && t >= 770 && t < 1190) {
                const cut = technique.pattern === 'fall' ? poses.overhead : poses.reverse;
                pose = sequence([[770, cut], [840, poses.slash], [890, poses.rise], [950, motion.strike], [1060, cut], [1140, poses.finish], [1190, motion.strike]], t);
            }
            if (technique.pattern === 'wheel' && t > 700 && t < 950) {
                pose = sequence([[700, motion.gather], [805, poses.reverse], [870, poses.overhead], [950, motion.strike]], t);
            }
            if (technique.motion === 'pluck' && t > 600 && t < 1160) {
                pose = sequence([[600, motion.gather], [720, poses.pluck], [805, motion.gather], [950, motion.strike], [1060, poses.strum], [1160, motion.strike]], t);
            }
            if (technique.motion === 'throw' && technique.pattern === 'rain' && t > 630 && t < 1100) {
                pose = sequence([[630, poses.fan], [780, poses.overhead], [950, poses.throw], [1100, poses.fan]], t);
            }
            if (technique.feint) {
                if (t < 745) {
                    x -= dir * 38 * Math.sin(Math.PI * clamp(t / 745));
                    pose = sequence([[0, motion.idle], [300, poses.reverse], [620, poses.low], [745, motion.gather]], t);
                }
                else if (t < 950)
                    pose = blend(poses.reverse, motion.strike, smooth((t - 745) / 205));
            }
            if (t >= 1190) {
                const retreat = smooth((t - 1190) / 490);
                x = home + dir * travel * (1 - retreat);
                if ((weapon === 'spear' || weapon === 'brush') && travel > 0) {
                    pose = stepping(blend(motion.strike, motion.idle, retreat), retreat, travel, true);
                    pose = blend(pose, motion.idle, smooth((t - 1570) / 110));
                }
                else if (!ranged && travel > 0) {
                    // Backward bound: fold the legs in flight, then absorb the landing.
                    lift = -46 * Math.sin(Math.PI * retreat);
                    pose = sequence([[1190, motion.strike], [1290, poses.bound], [1500, poses.low], [1630, motion.idle]], t);
                }
                else
                    pose = blend(motion.strike, motion.idle, retreat);
            }
            // The preceding choreography is the retained f39413d animation path.
            const moveFrame = variant === 'current' && attack && moveMotion(attack, t, travel, weapon, outcome?.type === 'dodge');
            if (moveFrame) {
                const frame = moveFrame;
                const transition = smooth(t / 140) * (1 - smooth((t - 1620) / 120));
                x = home + dir * frame.x;
                pose = blend(motion.idle, frame.pose, transition);
                lift = frame.lift;
                opacity = frame.opacity;
                blink = frame.blink;
            }
        }
        else if (outcome) {
            const age = time - outcome.time;
            if (outcome.type === 'dodge' && age > -120 && age < 630) {
                const f = age < 80 ? smooth((age + 120) / 200) : 1 - smooth((age - 130) / 500);
                const footwork = actor.qinggong?.id;
                const avoid = footwork === 'earth_root' ? poses.low : footwork === 'swan_shadow' || footwork === 'phantom_lotus' ? poses.bound :
                    footwork === 'lightning_flash' ? poses.dash : poses.dodge;
                pose = blend(motion.idle, avoid, f);
                x -= dir * (footwork === 'earth_root' ? 22 : footwork === 'lightning_flash' ? 80 : 62) * f;
                if (footwork === 'swan_shadow')
                    lift = -48 * f;
                if (footwork === 'phantom_lotus')
                    lift = -32 * f;
            }
            else if (outcome.type === 'damage' && age >= 0 && age < 720) {
                const held = contactTime(age, 35, impact.hold);
                const f = held < 85 ? smooth(held / 85) : 1 - smooth((held - 170) / 480);
                const reaction = outcome.bodyPartKey === 'leg' ? poses.low : outcome.bodyPartKey === 'abdomen' ? poses.recoil : poses.hit;
                pose = blend(motion.idle, reaction, f);
                x -= dir * (16 + impact.force * 52) * f;
                if (impact.heavy)
                    lift = -12 * Math.sin(Math.PI * clamp(held / 380));
                if (held > 200 && impact.heavy)
                    pose = blend(pose, stepping(motion.idle, clamp((held - 200) / 430), 32, true), .35 * (1 - f));
            }
        }
    }
    const skip = turn ? battle.events.find(e => e.type === 'turn_skip' && e.action === turn.action && e.actor === side && e.time <= time) : undefined;
    const skipAge = skip ? time - skip.time : -1;
    if (skip && skipAge >= 0 && skipAge < 1520 && hp > 0) {
        pose = blend(motion.idle, skip.reason === 'disarmed' ? poses.pickup : poses.hit, Math.sin(Math.PI * clamp(skipAge / 1520)) * .85);
    }
    if (hp <= 0) {
        opacity = 1;
        blink = 0;
        const death = battle.events.filter(e => e.target === side && e.hpAfter === 0 && e.time <= time).pop();
        pose = blend(poses.hit, poses.fallen, smooth((time - (death?.time || time)) / 560));
        const deathTurn = battle.events.find(e => e.type === 'turn_start' && e.action === death?.action);
        const deathAttack = battle.events.find(e => e.type === 'attack' && e.action === death?.action);
        const deathLocal = death && deathTurn ? death.time - deathTurn.time : 0;
        x = home;
        if (deathTurn?.actor === side && deathAttack && deathLocal >= 550) {
            x += dir * travel * (deathLocal < 950 ? smooth((deathLocal - 550) / 370) : deathLocal < 1100 ? 1 : 1 - smooth((deathLocal - 1100) / 550));
        }
        if (death?.cause === 'strike')
            x -= dir * (18 + impact.force * 40) * smooth((time - death.time) / 240);
    }
    else if (victory) {
        opacity = 1;
        blink = 0;
        const variant = (victory.victoryVariant || 0) % 3;
        const kind = victory.victoryKind || 'standard';
        const won = victory.actor === side;
        const options = {
            quick: [poses.victorySheath, poses.victoryBack, poses.victoryRest],
            dominant: [poses.victoryRaise, poses.victoryBack, poses.salute],
            standard: [poses.salute, poses.victoryBow, poses.victoryWipe],
            clutch: [poses.victoryKneel, poses.victoryRest, poses.victoryWipe],
            judged: [poses.victoryBow, poses.victoryWipe, poses.salute],
            draw: [poses.salute, poses.victoryBow, motion.idle],
        };
        let finish = won || kind === 'draw' ? options[kind][variant] : poses.victoryRest;
        if (weapon === 'zither')
            finish = variant === 0 ? poses.pluckIdle : variant === 1 ? poses.victoryBow : poses.victoryRest;
        const age = time - victory.time;
        const preparation = kind === 'clutch' ? poses.recoil : kind === 'quick' && variant === 2 ? poses.slash : motion.gather;
        pose = sequence([[0, motion.idle], [260, preparation], [950, finish], [1800, finish]], age);
        x = home;
        lift = 0;
        if (kind === 'clutch' && won && age > 950)
            pose = blend(finish, poses.victoryRest, .06 + .04 * Math.sin(age / 190));
        const length = { sword: 99, katana: 112, blade: 107, spear: 140, brush: 45 }[weapon];
        if (length && pose.sword > 0 && pose.sword < Math.PI / 2) {
            pose = { ...pose, sword: Math.min(pose.sword, Math.asin(clamp((-pose.points[6][1] - 5) / length))) };
        }
        victorySheathed = won && kind === 'quick' && variant === 0 && age > 740 && ['sword', 'katana', 'blade'].includes(weapon);
    }
    else if (time >= (battle.events[battle.events.length - 1]?.time || Infinity)) {
        pose = weapon === 'zither' ? poses.pluckIdle : poses.salute;
        x = home;
    }
    const sheathed = victorySheathed || (weapon === 'katana' && technique.motion === 'draw' && attack?.actor === side && local >= 0 && local < 830);
    pose = constrainRig(pose);
    return { x, pose, lift, opacity, blink, weapon: state.weaponsReady[side] ? weapon : 'unarmed', technique, armed: state.weaponsReady[side], sheathed, variant };
}
export function draw(ctx, battle, time, width, reducedMotion, effects, mode) {
    ctx.clearRect(0, 0, width, 430);
    const state = stateAt(battle, time);
    const frameAt = (side, at, turn) => poseAt(battle, side, at, width, turn, mode);
    const frames = { a: frameAt('a', time, state.turn), b: frameAt('b', time, state.turn) };
    const turn = state.turn;
    const attack = turn && battle.events.find(e => e.action === turn.action && e.type === 'attack');
    const striker = attack?.actor === 'a' ? battle.attacker : battle.defender;
    const variant = motionVariantFor(battle, attack, mode);
    const technique = (variant === 'legacy' ? legacyTechniqueFor : techniqueFor)(attack, striker);
    const outcome = attack && battle.events.find(e => e.action === attack.action && (e.cause === 'strike' || e.type === 'dodge'));
    const victim = attack?.actor === 'a' ? battle.defender : battle.attacker;
    const force = impactFor(outcome, victim.stats.hp, technique);
    const impactAge = outcome ? time - outcome.time : -1;
    ctx.save();
    if (effects && force.cinematic && impactAge > -160 && impactAge < 480) {
        const focus = impactAge < 0 ? smooth((impactAge + 160) / 160) : 1 - smooth((impactAge - 80) / 400);
        ctx.fillStyle = `rgba(32,39,35,${focus * .17})`;
        ctx.fillRect(0, 0, width, 430);
    }
    if (effects && !reducedMotion && force.heavy && impactAge >= 0 && impactAge < 220) {
        const shake = (1 - impactAge / 220) * force.force * 5;
        ctx.translate(Math.sin(impactAge * .09) * shake, Math.cos(impactAge * .13) * shake * .4);
    }
    ctx.lineCap = 'round';
    stroke(ctx, [[width * .065, 329], [width * .4, 329], [width * .72, 330], [width * .94, 329]], 1, 'rgba(44,49,40,.25)');
    stroke(ctx, [[width * .159, 333], [width * .396, 333]], .6, 'rgba(44,49,40,.15)');
    for (const side of ['a', 'b']) {
        const frame = frames[side];
        const actor = side === 'a' ? battle.attacker : battle.defender;
        const { x, pose, weapon, lift } = frame;
        const dir = side === 'a' ? 1 : -1;
        ctx.fillStyle = `rgba(30,35,29,${.13 * frame.opacity})`;
        ctx.beginPath();
        ctx.ellipse(x, 330, 52 + lift * .3, 6, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.save();
        ctx.globalAlpha = frame.opacity;
        if (effects && state.hp[side] > 0)
            drawAura(ctx, x, 324 + lift, state.states[side], time, state.stacks[side]);
        const local = turn ? time - turn.time : -1;
        if (effects && attack?.actor === side && !isNewMove(attack) && !expandedMoveFor(attack))
            drawPreparation(ctx, technique, x, dir, local, ['needles', 'zither'].includes(weapon));
        ctx.restore();
        const dodging = battle.events.find(e => e.type === 'dodge' && e.target === side && time >= e.time - 100 && time < e.time + 550);
        const moving = attack?.actor === side && ((local > 430 && local < 960) || (local > 1210 && local < 1660)) && !['needles', 'zither'].includes(weapon);
        if (effects && (moving || dodging)) {
            const qinggong = actor.qinggong?.id;
            const shadows = qinggong === 'earth_root' ? 0 : qinggong === 'shadow_drift' || qinggong === 'shadow_fragrance' ? 4 : 2;
            for (let i = shadows; i > 0; i--) {
                const past = frameAt(side, Math.max(0, time - i * 35), turn);
                fighter(ctx, past.x, side, past.pose, time - i * 35, past.weapon, .18 / i * past.opacity, past.lift, past.sheathed, actor.martialArt.id);
            }
            const trace = Array.from({ length: 4 }, (_, i) => {
                const past = frameAt(side, Math.max(turn?.time || 0, time - i * 60), turn);
                return { x: past.x, y: 324 + past.lift };
            });
            if (frame.opacity > .1)
                drawFootwork(ctx, qinggong, x, dir, .85 * frame.opacity, time, trace);
        }
        if (effects && !reducedMotion && frame.blink > .01) {
            ctx.save();
            ctx.globalAlpha = frame.blink * .45;
            for (let i = 0; i < 9; i++) {
                const spread = 12 + (1 - frame.opacity) * 26;
                const px = x + Math.sin(i * 2.4) * spread, py = 247 + lift + Math.cos(i * 2.4) * spread * .8;
                stroke(ctx, [[px - dir * 12, py + 8], [px + dir * 8, py - 10]], 1 + i % 3, '#495750');
            }
            ctx.restore();
        }
        fighter(ctx, x, side, pose, time, weapon, frame.opacity, lift, frame.sheathed, actor.martialArt.id);
        if (!frame.armed && weaponFor(actor) !== 'unarmed') {
            const disarm = battle.events.filter(e => e.type === 'status_apply' && e.status === 'disarmed' && e.target === side && e.time <= time).pop();
            const age = time - (disarm?.time || 0);
            const f = clamp(age / 430);
            ctx.save();
            ctx.translate(x - dir * (30 + f * 14), 230 + 94 * f - 40 * Math.sin(f * Math.PI));
            ctx.scale(dir, 1);
            ctx.rotate(f * 3.2);
            drawWeapon(ctx, weaponFor(actor), '#52574c', time);
            ctx.restore();
        }
    }
    if (effects && attack?.actor) {
        const side = attack.actor;
        const actor = side === 'a' ? battle.attacker : battle.defender;
        const dir = side === 'a' ? 1 : -1;
        const frame = frames[side];
        const outcome = battle.events.find(e => e.action === attack.action && (e.cause === 'strike' || e.type === 'dodge'));
        const heights = { head: 190, chest: 230, abdomen: 259, arm: 240, leg: 291 };
        const y = heights[outcome?.bodyPartKey || 'chest'] || 230;
        const targetSide = side === 'a' ? 'b' : 'a';
        // A missed attack passes through the original position instead of tracking
        // the dodging fighter and looking like a successful hit.
        const targetX = outcome?.type === 'dodge' ? width * (side === 'a' ? .765 : .235) : frames[targetSide].x;
        const age = contactTime(time - attack.time, (outcome?.time || attack.time + 400) - attack.time, force.hold);
        const emission = outcome && time > outcome.time ? frameAt(side, outcome.time, turn) : frame;
        const sample = variant === 'current' ? sampleMove(attack) : undefined;
        const profile = variant === 'current' ? profileFor(attack) : undefined, weapon = weaponFor(actor);
        const ranged = weapon === 'needles' || weapon === 'zither';
        const foot = attack.weaponType === 'leg';
        const tipReach = ({ sword: 99, katana: 112, blade: 107, spear: 140, brush: 45, unarmed: 0, needles: 0, zither: 0, heavy_sword: 110, tokens: 43, whip: 184 })[weapon] || 0;
        const tipAt = (source) => {
            const joint = source.pose.points[foot ? 10 : 6];
            return [source.x + dir * (joint[0] + Math.cos(source.pose.sword) * tipReach), 324 + source.lift + joint[1] + Math.sin(source.pose.sword) * tipReach];
        };
        if (variant === 'current' && turn && swordSequenceFor(attack)) {
            const local = contactTime(time - turn.time, (outcome?.time || turn.time + 950) - turn.time, force.hold);
            drawSwordSequenceEffects(ctx, attack, local, t => tipAt(frameAt(side, turn.time + t, turn)), dir, force);
        }
        if (expandedMoveFor(attack) && turn) {
            const sampleAt = t => {
                const pose = frameAt(side, turn.time + t, turn);
                return { tip: tipAt(pose), root: [pose.x, 324 + pose.lift] };
            };
            drawExpandedEffects(ctx, attack, time - turn.time, sampleAt,
                [frameAt(targetSide, outcome?.time || time, turn).x, y], dir, impactAge, force.hit);
        }
        else if (isNewMove(attack) && turn) {
            const sampleAt = (t) => {
                const pose = frameAt(side, turn.time + t, turn), hand = pose.pose.points[6], angle = pose.pose.sword;
                const world = (p) => [pose.x + dir * p[0], 324 + pose.lift + p[1]];
                const tip = weapon === 'blade' ? [104, -23] : [99, 0];
                return { hand: world(hand), tip: world([hand[0] + Math.cos(angle) * tip[0] - Math.sin(angle) * tip[1], hand[1] + Math.sin(angle) * tip[0] + Math.cos(angle) * tip[1]]), root: world([0, 0]) };
            };
            const contactTarget = [frameAt(targetSide, outcome?.time || time, turn).x, y];
            drawNewMartialEffects(ctx, attack.martialArtId === 'sword_danyu', time - turn.time, sampleAt, dir, impactAge, force.hit, force.force, contactTarget, newMoveFor(attack));
        }
        else if (profile && turn && time - turn.time > 650 && impactAge < 570) {
            // Sample the same poses as the figure, so trails follow the actual tip.
            const trace = Array.from({ length: 13 }, (_, i) => {
                const at = Math.max(turn.time + 650, time - (12 - i) * 14);
                const past = frameAt(side, at, turn);
                return { point: tipAt(past), opacity: past.opacity };
            });
            ctx.save();
            for (let i = 1; i < trace.length; i++) {
                ctx.globalAlpha = (i / trace.length) * .65 * (1 - clamp((impactAge - 80) / 280)) * Math.min(trace[i - 1].opacity, trace[i].opacity);
                stroke(ctx, [trace[i - 1].point, trace[i].point], (weapon === 'spear' ? 8 : ranged ? 2 : 6) * (i / trace.length), themeColors[profile.theme]);
                stroke(ctx, [trace[i - 1].point, trace[i].point], 1, '#f4f7ee');
            }
            ctx.restore();
            // Leave the burst at contact while the figure recovers, rather than
            // dragging the snow cloud back to the attacker's home position.
            const source = impactAge > 0 ? emission : frame;
            const tip = tipAt(source);
            const contactTarget = [outcome?.type === 'dodge' ? targetX : frameAt(targetSide, outcome?.time || time, turn).x, y];
            if (sample)
                drawSampleAccent(ctx, sample, tip, contactTarget, dir, impactAge, force);
            else
                drawMoveTheme(ctx, profile, tip, contactTarget, dir, impactAge, force);
            if (ranged)
                drawTechnique(ctx, techniqueFor(attack, actor), weapon, tip, contactTarget, dir, age, force.force);
        }
        else if (!profile) {
            drawTechnique(ctx, technique, weaponFor(actor), [emission.x + dir * 60, 236 + emission.lift], [targetX, y], dir, age, force.force);
        }
        if (!isNewMove(attack) && !expandedMoveFor(attack) && (!profile || sample === 'kick' || sample === 'spear'))
            drawImpact(ctx, targetX, y, dir, impactAge, force, attack.action || 0);
    }
    for (const event of battle.events) {
        const age = time - event.time;
        if (age < 0 || age > 1150)
            continue;
        const side = event.target || event.actor;
        if (!side)
            continue;
        const eventTurn = battle.events.find(e => e.type === 'turn_start' && e.action === event.action);
        const x = frameAt(side, event.time, eventTurn).x;
        const otherSide = event.fromSide || (event.actor !== side ? event.actor : side === 'a' ? 'b' : 'a');
        const otherX = otherSide ? frameAt(otherSide, event.time, eventTurn).x : x;
        // Reflection originates at the defender, while the HP event targets the attacker.
        const liveX = frames[side].x;
        const liveOtherX = otherSide ? frames[otherSide].x : otherX;
        if (effects) {
            const reflected = ['thorns', 'part_counter'].includes(event.cause);
            drawTrigger(ctx, event, reflected ? liveOtherX : liveX, reflected ? liveX : liveOtherX, age);
        }
        if (age > 850)
            continue;
        if (!['damage', 'heal', 'dodge', 'status_apply', 'turn_skip', 'passive_trigger', 'guard'].includes(event.type))
            continue;
        if (event.type === 'turn_skip' && event.reason === 'fallen')
            continue;
        const phase = age / 850;
        ctx.save();
        ctx.globalAlpha = Math.min(1, (850 - age) / 200);
        if (effects && event.type === 'damage' && event.cause !== 'strike' && age < 360) {
            ctx.fillStyle = event.crit ? '#863b2d' : '#353c32';
            for (let i = 0; i < 9; i++) {
                const angle = i * 2.399 + (event.action || 0);
                const r = (13 + (age / 360) * 57) * (i % 3 + 1) / 3;
                ctx.beginPath();
                ctx.ellipse(x + Math.cos(angle) * r, 230 + Math.sin(angle) * r, 1.5 + i % 3, 1 + i % 2, angle, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        const text = event.type === 'damage' ? `${event.crit ? '暴击 ' : ['thorns', 'part_counter'].includes(event.cause) ? '反震 ' : event.cause === 'deferred_damage' ? '暗劲 ' : event.cause === 'bleeding' ? '流血 ' : event.cause === 'poisoned' ? '毒伤 ' : ''}-${event.amount}` :
            event.type === 'heal' ? (event.cause === 'fatal_block' ? '神照护心' : `+${event.amount}`) : event.type === 'dodge' ? '闪' :
                event.type === 'guard' ? ((event.multiplier || 1) > 1 ? '罩门受创' : `${event.sourceSkill?.name || '真气'}护体`) :
                event.type === 'passive_trigger' ? (event.sourceSkill?.name || '身法触发') :
                event.type === 'turn_skip' ? (event.reason === 'disarmed' ? (weaponFor(side === 'a' ? battle.attacker : battle.defender) === 'unarmed' ? '重整架势' : '拾回兵刃') : '气机受阻') :
                    event.status === 'stacking_defense' ? `紫霞护体 ${event.stacks || 1}层` : statusLabels[event.status || ''] || '运功';
        const bottomTypes = ['status_apply', 'turn_skip', 'passive_trigger', 'guard'];
        const bottomLabel = bottomTypes.includes(event.type);
        const lane = battle.events.filter(e => e.action === event.action && e.time < event.time && (bottomLabel
            ? bottomTypes.includes(e.type) && (e.target || e.actor) === side && event.time - e.time < 850 && !(e.type === 'turn_skip' && e.reason === 'fallen')
            : e.type === event.type && e.target === event.target)).length;
        const labelY = bottomLabel ? 340 + Math.min(lane, 3) * 25 : 145 - (event.type === 'heal' ? 25 : 0) - Math.min(lane, 1) * 23;
        const major = event === outcome && force.heavy;
        ctx.font = `${major ? 'bold 34' : event.crit ? 'bold 29' : '24'}px "STKaiti", "KaiTi", serif`;
        ctx.textAlign = 'center';
        ctx.fillStyle = event.type === 'heal' ? '#405b45' : event.type === 'damage' ? '#892f27' : '#353b32';
        ctx.strokeStyle = 'rgba(250,249,237,.88)';
        ctx.lineWidth = 3;
        ctx.strokeText(text, x, labelY - phase * 22);
        ctx.fillText(text, x, labelY - phase * 22);
        ctx.restore();
    }
    ctx.restore();
}
