import { draw } from './battle/InkStage.js';
import { initiativeAt, stateAt, statusLabels, victoryLabels } from './battle/replay.js';
const params = new URLSearchParams(location.search);
const battle = window.__BATTLE__;
const canvas = document.querySelector('canvas');
canvas.width = 900;
canvas.height = 430;
const ctx = canvas.getContext('2d');
if (!ctx)
    throw new Error('canvas unavailable');
const text = (id) => document.getElementById(id);
const hpBar = (side) => document.getElementById(`hp-${side}`);
const gaugeBar = (side) => document.getElementById(`gauge-${side}`);
function updateHud(time) {
    const state = stateAt(battle, time);
    const gauge = initiativeAt(battle, time, state);
    const victory = battle.events.find(event => event.type === 'victory_start' && event.time <= time);
    const attack = battle.events.filter(event => event.type === 'attack' && event.time <= time).pop();
    const move = victory ? victoryLabels[victory.victoryKind || 'standard'] : attack?.move || (time < 1900 ? '起势' : '');
    text('heading-state').textContent = state.ended ? '胜负已分' : victory ? '收势' : '交锋中';
    text('heading-turn').textContent = state.turn ? `第 ${state.turn.action} 手` : '凝神待发';
    text('move-name').textContent = move;
    for (const side of ['a', 'b']) {
        const fighter = side === 'a' ? battle.attacker : battle.defender;
        const turnEnd = state.turn && battle.events.find(event => event.type === 'turn_end' && event.action === state.turn?.action);
        const acting = Boolean(state.turn?.actor === side && !state.ended && time < (turnEnd?.time || 0) && state.hp[side] > 0);
        const skipped = acting && battle.events.some(event => event.type === 'turn_skip' && event.action === state.turn?.action && event.time <= time);
        const ready = gauge[side] >= 100;
        const label = state.ended ? '已结束' : victory ? '收势' : state.hp[side] <= 0 ? '退场' : acting ? (skipped ? '行动受阻' : '出招中') : ready ? '待出招' : '蓄势';
        text(`name-${side}`).textContent = fighter.name;
        text(`hp-value-${side}`).textContent = `${state.hp[side]} / ${fighter.stats.hp}`;
        hpBar(side).style.width = `${Math.max(0, state.hp[side] / fighter.stats.hp * 100)}%`;
        text(`speed-${side}`).textContent = `速度 ${Math.round(state.speeds[side]) || '--'}`;
        text(`gauge-value-${side}`).textContent = state.hasGauge ? `${label} ${Math.floor(gauge[side])}/100` : `${label}`;
        gaugeBar(side).style.width = `${Math.min(100, Math.max(0, gauge[side]))}%`;
        text(`loadout-${side}`).textContent = `${fighter.martialArt.name} / ${fighter.neigong?.name || ''} / ${fighter.qinggong?.name || ''}`;
        text(`states-${side}`).textContent = state.states[side].map(value => statusLabels[value] || '运功').join(' / ') || '正常';
    }
}
const renderFrame = (time) => {
    draw(ctx, battle, time, 900, false, true, 'mixed');
    updateHud(time);
};
window.renderFrame = renderFrame;
renderFrame(Number(params.get('time') || 0));
document.body.dataset.ready = '1';

// Export the existing stage with a cached browser-rendered background.
const exportTextIds = ['heading-state', 'heading-turn', 'move-name', ...['a', 'b'].flatMap(side =>
    ['name', 'hp-value', 'speed', 'gauge-value', 'loadout', 'states'].map(key => `${key}-${side}`))];
let exportCanvas, exportContext, exportBackground, exportOrigin;
window.prepareExport = async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(image => image.decode().catch(() => {})));
    const background = new Image();
    background.src = new URL('./ink-bg.png', document.baseURI).href;
    await background.decode();
    // Reserve space for every status combination before caching the background.
    const stateElements = ['a', 'b'].map(side => text(`states-${side}`));
    const heights = [0, 0];
    for (const event of battle.events) {
        if (!['status_apply', 'passive_trigger', 'turn_end', 'battle_end'].includes(event.type))
            continue;
        updateHud(event.time);
        stateElements.forEach((element, index) => {
            heights[index] = Math.max(heights[index], element.getBoundingClientRect().height);
        });
    }
    stateElements.forEach((element, index) => { element.style.minHeight = `${heights[index]}px`; });
    renderFrame(0);
    const rect = document.body.getBoundingClientRect();
    exportOrigin = { x: rect.x, y: rect.y };
    const style = document.createElement('style');
    style.id = 'export-hide';
    style.textContent = `${exportTextIds.map(id => `#${id}`).join(',')}, canvas, .hp-track i, .gauge-track i { visibility: hidden !important; }`;
    document.head.append(style);
    return { x: rect.x, y: rect.y, width: Math.ceil(rect.width), height: Math.ceil(rect.height), scale: 1 };
};
window.initializeExport = async (source) => {
    exportBackground = new Image();
    exportBackground.src = `data:image/png;base64,${source}`;
    await exportBackground.decode();
    exportCanvas = document.createElement('canvas');
    const scale = 720 / exportBackground.width;
    exportCanvas.width = 720;
    exportCanvas.height = Math.round(exportBackground.height * scale);
    exportContext = exportCanvas.getContext('2d', { alpha: false });
    exportContext.scale(scale, scale);
    document.getElementById('export-hide').remove();
};
window.exportFrame = (time) => {
    renderFrame(time);
    const out = exportContext;
    out.drawImage(exportBackground, 0, 0);
    const stage = canvas.getBoundingClientRect();
    out.drawImage(canvas, stage.x - exportOrigin.x, stage.y - exportOrigin.y, stage.width, stage.height);
    for (const side of ['a', 'b']) {
        for (const bar of [hpBar(side), gaugeBar(side)]) {
            const rect = bar.getBoundingClientRect();
            const height = bar.offsetHeight;
            const width = parseFloat(getComputedStyle(bar).width);
            const skew = Math.tan(-7 * Math.PI / 180) * height;
            const left = rect.left - exportOrigin.x - Math.min(0, skew);
            const top = rect.top - exportOrigin.y;
            out.fillStyle = getComputedStyle(bar).backgroundColor;
            out.beginPath();
            out.moveTo(left, top);
            out.lineTo(left + width, top);
            out.lineTo(left + width + skew, top + height);
            out.lineTo(left + skew, top + height);
            out.closePath();
            out.fill();
        }
    }
    for (const id of exportTextIds) {
        const element = text(id);
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        out.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
        out.fillStyle = style.color;
        out.textAlign = style.textAlign === 'center' ? 'center' : 'left';
        out.textBaseline = 'alphabetic';
        const range = document.createRange();
        range.selectNodeContents(element);
        const rectangles = range.getClientRects();
        if (rectangles.length > 1 && element.firstChild?.nodeType === Node.TEXT_NODE) {
            const lines = [];
            for (let index = 0; index < element.textContent.length; index++) {
                range.setStart(element.firstChild, index);
                range.setEnd(element.firstChild, index + 1);
                const position = range.getBoundingClientRect();
                let line = lines[lines.length - 1];
                if (!line || Math.abs(line.top - position.top) > 1) {
                    line = { top: position.top, left: position.left, height: position.height, value: '' };
                    lines.push(line);
                }
                line.value += element.textContent[index];
            }
            out.textAlign = 'left';
            for (const line of lines) {
                const metrics = out.measureText(line.value);
                out.fillText(line.value, line.left - exportOrigin.x,
                    line.top - exportOrigin.y + (line.height - metrics.fontBoundingBoxAscent - metrics.fontBoundingBoxDescent) / 2 + metrics.fontBoundingBoxAscent);
            }
            continue;
        }
        const metrics = out.measureText(element.textContent);
        const ascent = metrics.fontBoundingBoxAscent;
        const descent = metrics.fontBoundingBoxDescent;
        const x = rect.x - exportOrigin.x + (out.textAlign === 'center' ? rect.width / 2 : 0);
        const y = rect.y - exportOrigin.y + (rect.height - ascent - descent) / 2 + ascent;
        out.fillText(element.textContent, x, y);
    }
    return exportCanvas.toDataURL('image/png').split(',')[1];
};
