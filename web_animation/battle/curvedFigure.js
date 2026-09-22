import { drawWeapon } from './inkWeapons.js';
// The fixed-length IK rig remains authoritative. Only the painted contour bends.
// Near full extension the joint is pulled toward the chord to avoid rubber limbs.
function limb(ctx, root, joint, end, width, color) {
    const midpoint = [(root[0] + end[0]) / 2, (root[1] + end[1]) / 2];
    const length = Math.hypot(joint[0] - root[0], joint[1] - root[1]) + Math.hypot(end[0] - joint[0], end[1] - joint[1]);
    const extension = Math.hypot(end[0] - root[0], end[1] - root[1]) / length;
    const curvature = .7 - .3 * Math.max(0, (extension - .8) / .2);
    ctx.beginPath();
    ctx.moveTo(...root);
    ctx.quadraticCurveTo(midpoint[0] + (joint[0] - midpoint[0]) * curvature, midpoint[1] + (joint[1] - midpoint[1]) * curvature, ...end);
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.stroke();
}
export function drawCurvedFigure(ctx, x, dir, pose, time, weapon, alpha, lift, sheathed, artId) {
    const p = pose.points, s = pose.shoulders || [p[1], p[1]], ink = dir === 1 ? '#252925' : '#475049';
    const accent = artId === 'sword_danyu' ? '#9c3b31' : artId === 'blade_jingchao' ? '#839897' : dir === 1 ? '#87372d' : '#aaa996';
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.translate(x, 324 + lift);
    ctx.scale(dir, 1);
    ctx.rotate(pose.lean);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    limb(ctx, s[0], p[3], p[4], 4.2, ink);
    limb(ctx, p[2], p[7], p[8], 6, ink);
    limb(ctx, p[2], p[9], p[10], 7.2, ink);
    ctx.strokeStyle = ink;
    ctx.lineWidth = 8.5;
    ctx.beginPath();
    ctx.moveTo(...p[1]);
    ctx.lineTo(...p[2]);
    ctx.stroke();
    limb(ctx, s[1], p[5], p[6], 5.5, ink);
    ctx.fillStyle = ink;
    ctx.beginPath();
    ctx.ellipse(p[0][0], p[0][1], 10, 13, .08, 0, Math.PI * 2);
    ctx.fill();
    const finger = Math.atan2(p[4][1] - p[3][1], p[4][0] - p[3][0]);
    if (weapon === 'sword' && !sheathed)
        for (const offset of [-.12, .12]) {
            ctx.beginPath();
            ctx.moveTo(...p[4]);
            ctx.lineTo(p[4][0] + Math.cos(finger + offset) * 9, p[4][1] + Math.sin(finger + offset) * 9);
            ctx.lineWidth = 1.7;
            ctx.stroke();
        }
    const flutter = Math.sin(time / 155) * 4;
    for (const [start, length, width] of [[p[0], 37, 2], [p[2], 45, 3]]) {
        ctx.strokeStyle = accent;
        ctx.lineWidth = width;
        ctx.beginPath();
        ctx.moveTo(start[0] + 7, start[1] - 2);
        ctx.quadraticCurveTo(start[0] - 12, start[1] - 7, start[0] - length, start[1] + flutter + 5);
        ctx.stroke();
    }
    if (sheathed) {
        ctx.strokeStyle = ink;
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(p[2][0] - 65, p[2][1] + 12);
        ctx.lineTo(p[2][0] + 12, p[2][1] - 3);
        ctx.stroke();
    }
    else {
        const hand = weapon === 'zither' ? [5, -83] : p[6];
        ctx.translate(...hand);
        ctx.rotate(weapon === 'zither' ? 0 : pose.sword);
        drawWeapon(ctx, weapon, ink, time);
    }
    ctx.restore();
}
