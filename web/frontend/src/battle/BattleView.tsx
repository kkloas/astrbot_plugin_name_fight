import { useEffect, useRef, useState } from 'react';
import { InkStage, type SceneTheme } from './InkStage';
import { stateAt, initiativeAt, statusLabels, victoryLabels, type Playback, type ReplayBattle, type Side } from './replay';
import { effectLabels, techniqueFor, weaponFor } from './martialVisuals';
import { impactFor } from './choreography';
import { wuxiaAudio } from './wuxiaAudio';
import './battle.css';

const SCENE_OPTIONS: [SceneTheme, string][] = [
  ['sunset', '残阳竹林'],
  ['snow', '寒江孤雪'],
  ['bloodmoon', '朱砂血月'],
  ['classic', '素宣原卷'],
];

export function BattleView({ battle, playback, startBattle, showResult = true, defaultScene = 'sunset' }: {
  battle: ReplayBattle | null; playback: Playback; startBattle: () => void; showResult?: boolean; defaultScene?: SceneTheme;
}) {
  const logRef=useRef<HTMLDivElement>(null);
  const follow=useRef(true);
  const prevTimeRef=useRef(0);
  const [starting,setStarting]=useState(false);
  const [sceneTheme,setSceneTheme]=useState<SceneTheme>(defaultScene);
  const [soundOn,setSoundOn]=useState(true);
  const state=battle?stateAt(battle,playback.time):null;

  useEffect(()=>{ setSceneTheme(defaultScene); },[defaultScene]);
  useEffect(()=>{ wuxiaAudio.enabled=soundOn; },[soundOn]);
  useEffect(()=>{ prevTimeRef.current=0; },[battle]);

  // Procedural Wuxia sound effects fired strictly on smooth forward playback (never during manual slider scrub).
  useEffect(()=>{
    if(!battle) return;
    const prev=prevTimeRef.current;
    const curr=playback.time;
    prevTimeRef.current=curr;
    if(!playback.playing || !soundOn || curr<=prev || curr-prev>380) return;
    for(const ev of battle.events){
      if(ev.time<=prev || ev.time>curr) continue;
      if(ev.type==='attack'){
        const isUlt=Boolean(ev.move?.startsWith('绝技')||ev.move?.startsWith('绝招')||ev.move==='万剑归宗');
        const crimson=ev.martialArtId==='blade_chixiao';
        if(isUlt) wuxiaAudio.playUltimateGuqin();
        wuxiaAudio.playSlash(isUlt,crimson);
      } else if(ev.type==='damage' && ev.cause==='strike'){
        const actorFighter=ev.actor==='a'?battle.attacker:battle.defender;
        const armed=weaponFor(actorFighter)!=='unarmed';
        const heavy=Boolean(ev.crit || (ev.amount||0)>=(ev.maxHp||500)*0.16);
        wuxiaAudio.playHit(heavy,Boolean(ev.crit),armed);
      } else if(ev.type==='dodge'){
        wuxiaAudio.playDodge();
      }
    }
  },[battle,playback.time,playback.playing,soundOn]);

  useEffect(()=>{
    if(follow.current && logRef.current) logRef.current.scrollTop=logRef.current.scrollHeight;
  },[state?.logs.length]);

  async function begin() { wuxiaAudio.unlock(); setStarting(true); try {await startBattle();} finally {setStarting(false);} }
  if(!battle || !state) return <section className="empty-battle">
    <h2>战斗剧场</h2><button disabled={starting} onClick={begin}>{starting?'准备中...':'开始试炼'}</button>
  </section>;

  const {time,duration,playing,speed,setPlaying,setSpeed,seek,replay}=playback;
  const gauge=initiativeAt(battle,time,state);
  const victory=battle.events.find(e=>e.type==='victory_start' && e.time<=time);
  const attack=battle.events.filter(e=>e.type==='attack' && e.time<=time).pop();
  const move=attack && time-attack.time<1280?attack.move:'';
  const outcome=attack && battle.events.find(e=>e.action===attack.action && (e.cause==='strike'||e.type==='dodge'));
  const striker=attack?.actor==='a'?battle.attacker:battle.defender;
  const victim=attack?.actor==='a'?battle.defender:battle.attacker;
  const impact=impactFor(outcome,victim.stats.hp,techniqueFor(attack,striker));
  const emphasize=Boolean(move && outcome && time>=outcome.time && time-outcome.time<650 && impact.heavy);
  const isUltimateMove=Boolean(move && (move.startsWith('绝技')||move.startsWith('绝招')||move==='万剑归宗'||move==='丹凤归云'||move==='一线分海'));
  const sealBadge=outcome && time>=outcome.time && time-outcome.time<780
    ? (outcome.crit?'暴击':isUltimateMove?'绝杀':'')
    : (isUltimateMove && attack && time-attack.time<520?'极意':'');

  return <section className={`ink-duel ink-duel-scene-${sceneTheme}`} aria-label="战斗剧场">
    <header className="duel-heading">
      <span>{state.ended?(battle.boss?.endingLabel || '胜负已分'):victory?'收势':playing?'交锋中':'已暂停'}</span>
      <span>{state.turn?`第 ${state.turn.action} 手`:'凝神待发'}</span>
    </header>
    <div className="duel-stage">
      <div className="duel-hud">
        {(['a','b'] as Side[]).map(side=>{
          const fighter=side==='a'?battle.attacker:battle.defender;
          const turnEnd=state.turn && battle.events.find(e=>e.type==='turn_end' && e.action===state.turn?.action);
          const acting=state.turn?.actor===side && !state.ended && time<(turnEnd?.time || 0) && state.hp[side]>0;
          const skipped=acting && battle.events.some(e=>e.type==='turn_skip' && e.action===state.turn?.action && e.time<=time);
          const ready=gauge[side]>=100;
          const label=state.ended?'已结束':victory?'收势':state.hp[side]<=0?'退场':acting?(skipped?'行动受阻':'出招中'):ready?'待出招':'蓄势';
          const boost=battle.events.filter(e=>e.type==='passive_trigger' && e.target===side && e.time<=time && time-e.time<1300).pop();
          const hpPercent=Math.max(0,Math.min(100,state.hp[side]/fighter.stats.hp*100));
          return <div className={`duel-health duel-health-${side}`} key={side}>
            <div className="duel-name"><strong>{fighter.name}</strong><span>{state.hp[side]} / {fighter.stats.hp}</span></div>
            <div className="duel-hp-track" role="progressbar" aria-label={`${fighter.name}气血`} aria-valuemin={0} aria-valuemax={fighter.stats.hp} aria-valuenow={state.hp[side]}>
              <em className="duel-hp-trail" style={{width:`${hpPercent}%`}} />
              <i style={{width:`${hpPercent}%`}} />
            </div>
            <div className={`duel-initiative${acting?' is-acting':ready?' is-ready':''}${boost?' is-boosted':''}`}>
              <div className="duel-initiative-label"><span>速度 {Math.round(state.speeds[side]) || '--'}</span>
                {boost && <b className="duel-boost-label">{boost.effect==='battle_start_first_strike'?'抢先':'提气'}</b>}
                <span className="duel-action-value">{state.hasGauge?(state.ended || victory || state.hp[side] <= 0?label:`${label} ${Math.floor(gauge[side])}/100`):'行动未记录'}</span></div>
              <div className="duel-action-track" role="progressbar" aria-label={`${fighter.name}行动条`} aria-valuemin={0} aria-valuemax={100}
                aria-valuenow={Math.min(100,Math.max(0,gauge[side]))} aria-valuetext={state.ended || victory || state.hp[side] <= 0?label:`${label}, 行动值 ${Math.floor(gauge[side])}`}>
                <i style={{transform:`scaleX(${Math.min(100,Math.max(0,gauge[side]))/100})`}} /><b />
              </div>
            </div>
            <div className="duel-loadout">{fighter.martialArt.name}<span>{[fighter.neigong?.name,fighter.qinggong?.name].filter(Boolean).join(' / ')}</span></div>
            <div className="duel-states">{state.states[side].map(s=><span key={s}>{statusLabels[s]||'运功'}</span>)}</div>
          </div>;
        })}
      </div>
      <div className={`duel-arena${isUltimateMove && !victory?' is-cinema':''}`}>
      <div className="duel-cinema-bar duel-cinema-top" aria-hidden="true" />
      <div className="duel-cinema-bar duel-cinema-bottom" aria-hidden="true" />
      <div className={`duel-move${emphasize?' duel-move-heavy':''}${isUltimateMove?' duel-move-ultimate':''}`} aria-live="off">
        {victory?(battle.boss?.endingLabel || victoryLabels[victory.victoryKind || 'standard']):move || (time<1900?'起势':'')}
        {sealBadge && !victory && <ins className="duel-seal-badge" key={`${attack?.action}-${sealBadge}`}>{sealBadge}</ins>}
      </div>
      <InkStage battle={battle} time={time} webEnhanced sceneTheme={sceneTheme} />
      <div className="duel-ground-labels"><span>我方</span><span>对手</span></div>
      <div className="duel-specials" aria-live="off">{(['a','b'] as Side[]).map(side=>{
        const events=battle.events.filter(e=>(['thorns','part_counter'].includes(e.cause||'')?e.actor===side:e.target===side) && e.sourceSkill && e.time<=time && time-e.time<1150 &&
          (e.type==='heal'||e.type==='passive_trigger'||e.type==='dodge'||e.type==='guard'||e.status==='crisis_defense'||['thorns','part_counter'].includes(e.cause||'')));
        const captions=[...new Set(events.map(e=>`${e.sourceSkill?.name} · ${e.type==='dodge'?'闪避':e.type==='guard'?((e.multiplier||1)>1?'罩门受击':'护体'):effectLabels[e.effect||e.cause||e.status||'']||'运功'}`))].slice(-3);
        return <span key={side}>{captions.map(text=><span key={text}>{text}</span>)}</span>;
      })}</div>
      </div>
    </div>
    <div className="duel-controls">
      <button onClick={()=>{wuxiaAudio.unlock(); state.ended?replay():setPlaying(!playing);}}>{state.ended?'再看一遍':playing?'暂停':'继续'}</button>
      <button onClick={()=>{wuxiaAudio.unlock(); replay();}}>重播</button>
      <button onClick={()=>seek(duration)} disabled={state.ended}>跳过</button>
      <label className="duel-speed">倍速 <select aria-label="播放倍速" value={speed} onChange={e=>setSpeed(Number(e.target.value))}>
        <option value={.25}>0.25x</option><option value={.5}>0.5x</option><option value={1}>1x</option><option value={1.5}>1.5x</option><option value={2}>2x</option>
      </select></label>
      <label className="duel-speed">画境 <select aria-label="战场画境" value={sceneTheme} onChange={e=>setSceneTheme(e.target.value as SceneTheme)}>
        {SCENE_OPTIONS.map(([id,label])=><option key={id} value={id}>{label}</option>)}
      </select></label>
      <button type="button" className={`duel-audio-btn${soundOn?' is-on':''}`} onClick={()=>{const next=!soundOn; setSoundOn(next); if(next) wuxiaAudio.unlock();}}>
        {soundOn?'琴音: 开':'琴音: 关'}
      </button>
      <output>{Math.floor(time/1000)} / {Math.floor(duration/1000)} 秒</output>
    </div>
    <input className="duel-scrubber" type="range" aria-label="战斗进度" min={0} max={duration} step={1} value={time} onChange={e=>seek(Number(e.target.value))} />
    {showResult && state.ended && <div className="duel-result" role="status">
      <div><strong>{battle.winner?`${battle.winner} 胜`:'平局'}</strong><span>剩余气血 {state.hp.a} / {state.hp.b}</span></div>
      {Object.entries(battle.rating || {}).map(([key,r])=><span key={key}>{r.name}: 排分 {r.before} → {r.after} ({r.delta>0?'+':''}{r.delta})</span>)}
      <button onClick={begin} disabled={starting}>{starting?'准备中...':'再战一场'}</button>
    </div>}
    <div className="duel-log-heading"><h3>战报</h3><span>{state.logs.length} 条</span></div>
    <div className="duel-log" ref={logRef} onScroll={()=>{
      const el=logRef.current;if(el) follow.current=el.scrollHeight-el.scrollTop-el.clientHeight<40;
    }}>
      {state.logs.map((line,i)=><p key={`${i}-${line}`}>{line}</p>)}
    </div>
  </section>;
}
