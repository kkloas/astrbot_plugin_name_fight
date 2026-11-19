import { initiativeAt, stateAt, victoryLabels } from './replay.js';

export function battleHudAt(battle, time) {
    const state = stateAt(battle, time);
    const gauge = initiativeAt(battle, time, state);
    const victory = battle.events.find(event => event.type === 'victory_start' && event.time <= time);
    const attack = battle.events.filter(event => event.type === 'attack' && event.time <= time).pop();
    const move = victory ? (battle.boss?.endingLabel || victoryLabels[victory.victoryKind || 'standard']) : attack?.move || (time < 1900 ? '起势' : '');
    const sides = {};
    for (const side of ['a', 'b']) {
        const turnEnd = state.turn && battle.events.find(event => event.type === 'turn_end' && event.action === state.turn?.action);
        const acting = Boolean(state.turn?.actor === side && !state.ended && time < (turnEnd?.time || 0) && state.hp[side] > 0);
        const skipped = acting && battle.events.some(event => event.type === 'turn_skip' && event.action === state.turn?.action && event.time <= time);
        const ready = gauge[side] >= 100;
        const label = state.ended ? '已结束' : victory ? '收势' : state.hp[side] <= 0 ? '退场' : acting ? (skipped ? '行动受阻' : '出招中') : ready ? '待出招' : '蓄势';
        sides[side] = {
            speed: Math.round(state.speeds[side]) || '--',
            percent: Math.min(100, Math.max(0, gauge[side])),
            action: state.hasGauge ? `${label} ${Math.floor(gauge[side])}/100` : label,
        };
    }
    return { state, move, victory, sides };
}
