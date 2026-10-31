// Presentation metadata never changes combat events or their displayed names.
const visualCache = new WeakMap();
export function visualBattle(battle) {
    if (visualCache.has(battle)) return visualCache.get(battle);
    if (!battle.events.some(event => event.visualMove)) {
        visualCache.set(battle, battle);
        return battle;
    }
    const visual = { ...battle, events: battle.events.map(event => event.visualMove ? { ...event, move: event.visualMove } : event) };
    visualCache.set(battle, visual);
    visualCache.set(visual, visual);
    return visual;
}

function line(ctx, points, color, width = 2) {
    ctx.beginPath();
    points.forEach(([x, y], index) => index ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
}
function ring(ctx, x, y, radius, color, flat = 1) {
    ctx.beginPath(); ctx.ellipse(x, y, radius, radius * flat, 0, 0, Math.PI * 2);
    ctx.strokeStyle = color; ctx.lineWidth = 1.8; ctx.stroke();
}

export function drawBossPresence(ctx, battle, side, frame, time, state, effects, reducedMotion) {
    const actor = side === 'a' ? battle.attacker : battle.defender;
    if (!actor.bossKey?.startsWith('dragon_chief_')) return;
    const sovereign = actor.bossKey.endsWith('phase2');
    const gold = sovereign ? '#ba8527' : '#94702f';
    const jade = '#16826a';
    const dir = side === 'a' ? 1 : -1;
    const points = frame.pose.points;
    const world = p => [frame.x + dir * p[0], 324 + frame.lift + p[1]];
    const head = world(points[0]), neck = world(points[1]), waist = world(points[2]);
    ctx.save(); ctx.globalAlpha = frame.opacity;
    // Armor follows the existing skeleton, including dodge, stun and death poses.
    ctx.beginPath();
    ctx.moveTo(neck[0] - 17, neck[1]); ctx.lineTo(neck[0] + 17, neck[1]);
    ctx.lineTo(waist[0] + 23, waist[1] + 15); ctx.lineTo(waist[0] - 23, waist[1] + 15);
    ctx.closePath(); ctx.fillStyle = sovereign ? '#253d37' : '#39382d'; ctx.fill();
    ctx.strokeStyle = gold; ctx.lineWidth = 2; ctx.stroke();
    for (let i = 1; i < 5; i++) {
        const f = i / 5, x = neck[0] + (waist[0] - neck[0]) * f, y = neck[1] + (waist[1] - neck[1]) * f;
        line(ctx, [[x-13,y], [x,y+5], [x+13,y]], gold, 1.2);
    }
    if (sovereign) {
        line(ctx, [[head[0]-9,head[1]-5],[head[0]-17,head[1]-23],[head[0]-11,head[1]-30]], gold, 3);
        line(ctx, [[head[0]+8,head[1]-5],[head[0]+18,head[1]-22],[head[0]+14,head[1]-29]], gold, 3);
        line(ctx, [[head[0]-9,head[1]],[head[0],head[1]+8],[head[0]+12,head[1]+1]], gold, 3);
        line(ctx, [[head[0]-5,head[1]],[head[0]+5,head[1]]], jade, 3);
    } else {
        line(ctx, [[head[0]-11,head[1]-8],[head[0],head[1]-14],[head[0]+11,head[1]-8]], gold, 2.5);
    }
    if (!effects || state.hp[side] <= 0) { ctx.restore(); return; }
    const pulse = reducedMotion ? 0 : Math.sin(time / 450) * 3;
    ctx.globalAlpha = frame.opacity * .45;
    ring(ctx, frame.x, 327 + frame.lift, 55 + pulse, sovereign ? jade : gold, .13);
    // The arrival flourish is only shown for the first duel in each phase.
    if (battle.boss?.intro && time < 1600) {
        const f = time / 1600;
        ctx.globalAlpha = (1 - f) * .65;
        ring(ctx, frame.x, 255, 35 + f * 100, gold, .9);
        if (sovereign) {
            const curve = Array.from({length: 30}, (_, i) => {
                const t = i / 29;
                return [frame.x + Math.sin(t * Math.PI * 3 + f * 2) * 65, 315 - t * 180];
            });
            line(ctx, curve, jade, 4 * (1 - f) + 1);
        } else {
            for (const offset of [-1, 1]) line(ctx, [[frame.x + offset * 65, 320],[frame.x + offset * 65,180],[frame.x,160]], gold, 2);
        }
    }
    const attack = battle.events.find(event => event.type === 'attack' && event.actor === side && event.time <= time && time - event.time < 1600);
    if (attack && frame.armed) {
        const outcome = battle.events.find(event => event.action === attack.action && (event.cause === 'strike' || event.type === 'dodge'));
        const age = time - (outcome?.time ?? attack.time + 950);
        const fade = Math.max(0, 1 - Math.abs(age) / 460);
        const hand = world(points[6]);
        const index = attack.moveIndex ?? 0;
        ctx.globalAlpha = fade * frame.opacity * .8;
        if (fade > 0) {
            const count = 2 + index % 4;
            for (let i = 0; i < count; i++) {
                const angle = frame.pose.sword + (i - (count-1)/2) * .16;
                const length = 62 + (index % 3) * 15;
                const tip = [hand[0]+dir*Math.cos(angle)*length, hand[1]+Math.sin(angle)*length];
                line(ctx, [hand, tip], gold, sovereign ? 3 : 1.8);
                if (sovereign) {
                    const curve = Array.from({length: 14}, (_, j) => {
                        const t = j/13;
                        return [hand[0]+(tip[0]-hand[0])*t,hand[1]+(tip[1]-hand[1])*t+Math.sin(t*Math.PI*4+index)*6*Math.sin(t*Math.PI)];
                    });
                    line(ctx, curve, jade, 1.5);
                }
            }
        }
    }
    // Healing decoration is tied to an actual heal event, never a passive timer.
    const heal = battle.events.find(event => event.type === 'heal' && event.target === side && time >= event.time && time-event.time < 900);
    if (heal) {
        const f = (time-heal.time)/900;
        ctx.globalAlpha = (1-f)*.75;
        for (let i=0;i<7;i++) ring(ctx,frame.x+Math.sin(i*2.4)*28,310-f*95-i*3,2.2,jade);
    }
    ctx.restore();
}


export function drawBossBackdrop(ctx, battle, width) {
    if (!battle.boss) return;
    const sovereign = battle.boss.phase === 2;
    ctx.save();
    ctx.globalAlpha = .14;
    const color = sovereign ? '#527966' : '#826638';
    // A static scene keeps exports compact and gives each phase its own silhouette.
    for (let row = 0; row < 3; row++) {
        const points = Array.from({length: 19}, (_, i) => [width * i / 18,
            280 + row * 13 - Math.abs(Math.sin(i * 1.7 + row)) * (55 - row * 9)]);
        line(ctx, points, color, 1.5);
    }
    const x = width * .77;
    if (!sovereign) {
        line(ctx, [[x-88,320],[x-88,145],[x+88,145],[x+88,320]], color, 7);
        line(ctx, [[x-115,150],[x-75,126],[x,112],[x+75,126],[x+115,150]], color, 5);
        line(ctx, [[x-88,174],[x+88,174]], color, 3);
    } else {
        ring(ctx,x,218,96,color);
        ring(ctx,x,218,84,color);
        for(let i=0;i<12;i++) {
            const a=i*Math.PI/6;
            line(ctx,[[x+Math.cos(a)*88,218+Math.sin(a)*88],[x+Math.cos(a)*96,218+Math.sin(a)*96]],color,2);
        }
        line(ctx, [[x-58,272],[x-28,224],[x-42,185],[x,159],[x+25,180],[x+49,163],[x+34,208],[x+9,228],[x+23,258]], color, 4);
    }
    ctx.restore();
}
