import { draw, waitForBattleAssets } from '/spectate/v143/battle/InkStage.js';
import { battleHudAt } from '/spectate/v143/battle/hud.js';

const bouts = JSON.parse(document.querySelector('#bouts').textContent);
const byId = id => document.getElementById(id);
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');
const select = byId('bout'), seek = byId('seek'), play = byId('play');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const durations = bouts.map(bout => bout.events[bout.events.length - 1].time);
let index = 0, position = 0, since = 0, playing = false, frame = 0, lastPaint = 0;

function paint() {
    const battle = bouts[index];
    const { state, move, sides } = battleHudAt(battle, position);
    byId('move').textContent = move;
    draw(ctx, battle, position, canvas.width, reduced, true, 'mixed', { webEnhanced: true, sceneTheme: 'classic', battleStains: false });
    for (const [side, fighter] of [['a', battle.attacker], ['b', battle.defender]]) {
        byId(side + '-hp').textContent = '气血 ' + state.hp[side] + ' / ' + fighter.stats.hp;
        byId(side + '-bar').value = state.hp[side];
        byId(side + '-gauge').value = sides[side].percent;
        byId(side + '-speed').textContent = '速度 ' + sides[side].speed;
        byId(side + '-action').textContent = sides[side].action;
    }
    const message = state.logs[state.logs.length - 1] || '双方就位';
    byId('status').textContent = state.ended && battle.teamOutcome ? '【3v3 结果】' + battle.teamOutcome + '。' + message : message;
    seek.value = position;
}
function selectBout(number) {
    index = number;
    select.value = String(number);
    const battle = bouts[index];
    for (const [side, fighter] of [['a', battle.attacker], ['b', battle.defender]]) {
        byId(side + '-name').textContent = fighter.name;
        byId(side + '-bar').max = fighter.stats.hp;
        byId(side + '-arts').textContent = [fighter.martialArt?.name, fighter.neigong?.name, fighter.qinggong?.name].filter(Boolean).join(' / ');
    }
    seek.max = durations[index];
    position = 0;
    since = performance.now();
    paint();
}
function tick(now) {
    position = Math.min(durations[index], Math.max(0, now - since));
    if (now - lastPaint >= 32 || position >= durations[index]) {
        paint();
        lastPaint = now;
    }
    if (position >= durations[index]) {
        if (index + 1 === bouts.length) {
            playing = false;
            play.textContent = '重播';
            return;
        }
        selectBout(index + 1);
    }
    frame = requestAnimationFrame(tick);
}
function toggle() {
    if (playing) {
        cancelAnimationFrame(frame);
        playing = false;
        play.textContent = '继续';
    } else {
        if (position >= durations[index] && index + 1 === bouts.length) selectBout(0);
        since = performance.now() - position;
        playing = true;
        play.textContent = '暂停';
        frame = requestAnimationFrame(tick);
    }
}

bouts.forEach((_, i) => select.add(new Option('第 ' + (i + 1) + ' 场', String(i))));
byId('bout-label').hidden = bouts.length < 2;
select.onchange = () => { selectBout(Number(select.value)); if (!playing) play.textContent = '播放'; };
seek.oninput = () => {
    position = Number(seek.value);
    since = performance.now() - position;
    if (!playing) play.textContent = position >= durations[index] && index + 1 === bouts.length ? '重播' : '继续';
    paint();
};
play.onclick = toggle;
play.disabled = seek.disabled = false;
selectBout(0);
if (!reduced) toggle();
waitForBattleAssets().then(() => { if (!playing) paint(); });
