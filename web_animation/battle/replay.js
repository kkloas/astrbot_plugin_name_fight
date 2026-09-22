export const statusLabels = {
    bleeding: '流血', poisoned: '中毒', stunned: '眩晕', slowed: '迟缓',
    weakened: '虚弱', disarmed: '缴械', armor_broken: '破甲', crisis_defense: '护体',
};
export const victoryLabels = { quick: '速战速决', dominant: '从容取胜', standard: '胜负已分', clutch: '险中取胜', judged: '略胜半筹', draw: '不分胜负' };
export function stateAt(battle, time) {
    const hp = {
        a: battle.attacker.currentHp ?? battle.attacker.stats.hp,
        b: battle.defender.currentHp ?? battle.defender.stats.hp,
    };
    const states = { a: [], b: [] };
    const weaponsReady = { a: true, b: true };
    const gauge = { a: 0, b: 0 };
    const speeds = { a: battle.attacker.stats.spd || 0, b: battle.defender.stats.spd || 0 };
    let hasGauge = false;
    const logs = [];
    let turn;
    let ended = false;
    for (const event of battle.events) {
        if (event.time > time)
            break;
        if (event.target && event.hpAfter !== undefined)
            hp[event.target] = event.hpAfter;
        if (event.type === 'turn_start')
            turn = event;
        if (event.gauge) {
            hasGauge = true;
            if (event.type === 'gauge_charge' && event.gaugeFrom && event.endTime !== undefined) {
                const phase = Math.max(0, Math.min(1, (time - event.time) / Math.max(1, event.endTime - event.time)));
                for (const side of ['a', 'b'])
                    gauge[side] = event.gaugeFrom[side] + (event.gauge[side] - event.gaugeFrom[side]) * phase;
            }
            else
                Object.assign(gauge, event.gauge);
        }
        if (event.speeds)
            Object.assign(speeds, event.speeds);
        if (event.target && event.gaugeValue !== undefined)
            gauge[event.target] = event.gaugeValue;
        if (event.target && event.speedAfter !== undefined)
            speeds[event.target] = event.speedAfter;
        if (event.type === 'status_apply' && event.target && event.status) {
            if (!states[event.target].includes(event.status))
                states[event.target].push(event.status);
            if (event.status === 'disarmed')
                weaponsReady[event.target] = false;
        }
        if (event.weaponsReady)
            Object.assign(weaponsReady, event.weaponsReady);
        if (event.states) {
            states.a = event.states.a.filter(s => s.duration > 0).map(s => s.type);
            states.b = event.states.b.filter(s => s.duration > 0).map(s => s.type);
        }
        if (event.type === 'battle_end') {
            ended = true;
            if (event.final) {
                hp.a = event.final.a.hp;
                hp.b = event.final.b.hp;
            }
        }
        logs.push(...(event.logs || []));
    }
    return { hp, states, weaponsReady, gauge, speeds, hasGauge, logs, turn, ended };
}
export function initiativeAt(battle, time, state = stateAt(battle, time)) {
    const gauge = { ...state.gauge };
    const charges = battle.events.filter(e => e.type === 'gauge_charge' && e.endTime !== undefined);
    const index = charges.findIndex(e => e.endTime > time);
    const charge = charges[index];
    if (!charge?.gauge || !charge.gaugeFrom)
        return gauge;
    const start = index > 0 ? charges[index - 1].endTime : charge.time;
    // Spread the next recorded tick accumulation across the preceding animation,
    // rather than squeezing it into the short gap between two turns. Resource
    // boosts and actual speed changes rebase the interpolation immediately.
    const rawProgress = time < charge.time ? 0 : Math.max(0, Math.min(1, (time - charge.time) / Math.max(1, charge.endTime - charge.time)));
    for (const side of ['a', 'b']) {
        let origin = start;
        for (const event of battle.events) {
            if (event.time > Math.min(time, charge.time))
                break;
            if (event.target === side && event.gaugeValue !== undefined)
                origin = Math.max(origin, event.time);
        }
        const integral = (end) => {
            if (end <= origin)
                return 0;
            let speed = (side === 'a' ? battle.attacker : battle.defender).stats.spd || 1;
            let cursor = origin, total = 0;
            for (const event of battle.events) {
                if (event.time > end)
                    break;
                const next = event.speeds?.[side] ?? (event.target === side ? event.speedAfter : undefined);
                if (next === undefined)
                    continue;
                if (event.time > origin) {
                    total += (event.time - cursor) * speed;
                    cursor = event.time;
                }
                speed = next;
            }
            return total + (end - cursor) * speed;
        };
        const progress = Math.max(0, Math.min(1, integral(time) / Math.max(1, integral(charge.endTime))));
        gauge[side] += (charge.gauge[side] - charge.gaugeFrom[side]) * (progress - rawProgress);
    }
    return gauge;
}
