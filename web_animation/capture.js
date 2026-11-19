import { draw, waitForBattleAssets } from './battle/InkStage.js';
import { statusLabels } from './battle/replay.js';
import { battleHudAt } from './battle/hud.js';
const params = new URLSearchParams(location.search);
const battle = window.__BATTLE__;
const canvas = document.querySelector('canvas');
canvas.width = 900;
canvas.height = 430;
const ctx = canvas.getContext('2d');
if (!ctx)
    throw new Error('canvas unavailable');
const botRenderOptions = { webEnhanced: true, sceneTheme: 'classic', battleStains: false };
const text = (id) => document.getElementById(id);
const hpBar = (side) => document.getElementById(`hp-${side}`);
const gaugeBar = (side) => document.getElementById(`gauge-${side}`);
function updateHud(time) {
    const { state, move, victory, sides } = battleHudAt(battle, time);
    text('heading-state').textContent = state.ended ? (battle.boss?.endingLabel || '胜负已分') : victory ? '收势' : '交锋中';
    text('heading-turn').textContent = state.turn ? `第 ${state.turn.action} 手` : '凝神待发';
    text('move-name').textContent = move;
    for (const side of ['a', 'b']) {
        const fighter = side === 'a' ? battle.attacker : battle.defender;
        text(`name-${side}`).textContent = fighter.name;
        text(`hp-value-${side}`).textContent = `${state.hp[side]} / ${fighter.stats.hp}`;
        hpBar(side).style.width = `${Math.max(0, state.hp[side] / fighter.stats.hp * 100)}%`;
        text(`speed-${side}`).textContent = `速度 ${sides[side].speed}`;
        text(`gauge-value-${side}`).textContent = sides[side].action;
        gaugeBar(side).style.width = `${sides[side].percent}%`;
        text(`loadout-${side}`).textContent = `${fighter.martialArt.name} / ${fighter.neigong?.name || ''} / ${fighter.qinggong?.name || ''}`;
        text(`states-${side}`).textContent = state.states[side].map(value => statusLabels[value] || '运功').join(' / ') || '正常';
    }
}
const renderFrame = (time) => {
    draw(ctx, battle, time, 900, false, true, 'mixed', botRenderOptions);
    updateHud(time);
};
window.renderFrame = renderFrame;
const initialTime = Number(params.get('time') || 0);
renderFrame(initialTime);
waitForBattleAssets().then(() => renderFrame(initialTime));
document.body.dataset.ready = '1';

// Export the existing stage with a cached browser-rendered background.
const exportTextIds = ['heading-state', 'heading-turn', 'move-name', ...['a', 'b'].flatMap(side =>
    ['name', 'hp-value', 'speed', 'gauge-value', 'loadout', 'states'].map(key => `${key}-${side}`))];
let exportCanvas, exportContext, exportBackground, exportOrigin;
window.prepareExport = async () => {
    await document.fonts.ready;
    await Promise.all([
        waitForBattleAssets(),
        ...[...document.images].map(image => image.decode().catch(() => {})),
    ]);
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
    const scale = 640 / exportBackground.width;
    exportCanvas.width = 640;
    exportCanvas.height = Math.round(exportBackground.height * scale);
    exportContext = exportCanvas.getContext('2d', { alpha: false, willReadFrequently: true });
    exportContext.scale(scale, scale);
    document.getElementById('export-hide').remove();
};
const composeExportFrame = (time) => {
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
};
window.exportFrame = (time) => {
    composeExportFrame(time);
    return exportCanvas.toDataURL('image/png').split(',')[1];
};
let previousPixels = null;
window.exportRawFrame = async (time) => {
    composeExportFrame(time);
    const pixels = exportContext.getImageData(0, 0, exportCanvas.width, exportCanvas.height).data;
    const width = exportCanvas.width, height = exportCanvas.height;
    const words = new Uint32Array(pixels.buffer, pixels.byteOffset, pixels.byteLength / 4);
    let left = width, top = height, right = 0, bottom = 0;
    if (previousPixels && previousPixels.length === words.length) {
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const i = y * width + x;
                if (words[i] !== previousPixels[i]) {
                    left = Math.min(left, x); right = Math.max(right, x + 1);
                    top = Math.min(top, y); bottom = y + 1;
                }
            }
        }
    } else { left = 0; top = 0; right = width; bottom = height; }
    // Compare exact RGBA words; no color reduction occurs during transport.
    previousPixels = words;
    if (right === 0) return {width, height, x: 0, y: 0, patchWidth: 0, patchHeight: 0, data: ''};
    const patchWidth = right - left, patchHeight = bottom - top;
    const patch = new Uint8Array(patchWidth * patchHeight * 4);
    for (let y = 0; y < patchHeight; y++) {
        const start = ((top + y) * width + left) * 4;
        patch.set(pixels.subarray(start, start + patchWidth * 4), y * patchWidth * 4);
    }
    const data = typeof patch.toBase64 === 'function' ? patch.toBase64() : await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(new Blob([patch]));
    });
    return {width, height, x: left, y: top, patchWidth, patchHeight, data};
};
