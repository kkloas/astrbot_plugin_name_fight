import { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { InkStage } from './InkStage';
import { useBattlePlayback, type ReplayBattle, type Side } from './replay';
import { moveProfiles } from './moveProfiles';
import type { MotionMode } from './motionVariants';
import { newMotionMoves, isNewArt, newMoveFor } from './newMartialMotion';
import './motionPreview.css';

const samples = [
  {id:'sword_falling_plum',name:'落梅剑法',move:'寒枝点雪',type:'sword'},
  {id:'staff_yuejiaqiang',name:'岳家枪法',move:'绝招·回马枪',type:'staff'},
  {id:'leg_shadow_whirl',name:'追影腿',move:'穿云踢',type:'leg'},
];
const arts:Record<string,[string,string]>={
  palm_crushing_wave:['碎浪掌','palm'],sword_falling_plum:['落梅剑法','sword'],leg_shadow_whirl:['追影腿','leg'],
  sword_huashan:['华山剑法','sword'],short_panguanbi:['掌命判官笔','short_weapon'],blade_chengyun:['乘云刀法','blade'],
  staff_yuejiaqiang:['岳家枪法','staff'],sword_ittoryu:['北辰一刀流','sword'],sword_xiaoyaowuxiang:['逍遥无相剑','sword'],
  hidden_baoyulihua:['暴雨梨花针','hidden_weapon'],zither_duanzhi:['断指离弦琴','musical_instrument'],
};
const moves=[...samples,...Object.entries(moveProfiles).filter(([id])=>!isNewArt(id)).flatMap(([id,profiles])=>Object.keys(profiles)
  .filter(move=>!samples.some(m=>m.id===id && m.move===move))
  .map(move=>({id,name:arts[id][0],type:arts[id][1],move}))),...newMotionMoves];

function MotionPreview() {
  const [selection,setSelection]=useState(()=>Math.max(0,moves.findIndex(m=>m.id===new URLSearchParams(location.search).get('art'))));
  const [side,setSide]=useState<Side>('a');
  const [missed,setMissed]=useState(false);
  const [motionMode,setMotionMode]=useState<MotionMode>('current');
  const battle=useMemo<ReplayBattle>(()=>{
    const art=moves[selection],target:Side=side==='a'?'b':'a';
    const authored=newMoveFor({martialArtId:art.id,move:art.move,type:'attack',time:0});
    const damage=authored?(authored.signature?340:Math.round(180*authored.power)):selection===1?340:140;
    const sample={name:art.move,stats:{hp:1000,spd:60},martialArt:art};
    const opponent={name:'试招对手',stats:{hp:1000,spd:60},martialArt:{id:'palm_crushing_wave',name:'碎浪掌',type:'palm'}};
    return {attacker:side==='a'?sample:opponent,defender:side==='b'?sample:opponent,winner:null,events:[
      {type:'battle_start',time:0},
      {type:'turn_start',time:300,action:1,actor:side},
      {type:'attack',time:850,action:1,actor:side,target,martialArtId:art.id,move:art.move,weaponType:art.type},
      missed?{type:'dodge',time:1250,action:1,actor:side,target}:
        {type:'damage',time:1250,action:1,actor:side,target,cause:'strike',amount:damage,hpAfter:1000-damage,maxHp:1000,bodyPartKey:'chest'},
      {type:'turn_end',time:2100,action:1},
      {type:'battle_end',time:2500},
    ]};
  },[selection,side,missed]);
  const playback=useBattlePlayback(battle);
  return <main className="motion-preview">
    <header><h1>动作样板</h1><a href="/">返回游戏</a></header>
    <div className="preview-controls">
      <label>招式 <select aria-label="招式" value={selection} onChange={e=>setSelection(Number(e.target.value))}>{moves.map((m,i)=><option key={`${m.id}/${m.move}`} value={i}>{m.name} / {m.move}</option>)}</select></label>
      <label>出招方 <select aria-label="出招方" value={side} onChange={e=>setSide(e.target.value as Side)}><option value="a">左方</option><option value="b">右方</option></select></label>
      <label>动画 <select aria-label="动画版本" value={isNewArt(moves[selection].id)?'current':motionMode} disabled={isNewArt(moves[selection].id)} onChange={e=>setMotionMode(e.target.value as MotionMode)}><option value="mixed">随机混用</option><option value="legacy">旧版</option><option value="current">{isNewArt(moves[selection].id)?'专属':'新版'}</option></select></label>
      <label><input type="checkbox" checked={missed} onChange={e=>setMissed(e.target.checked)} /> 闪避</label>
      <button onClick={()=>playback.setPlaying(!playback.playing)}>{playback.playing?'暂停':'播放'}</button>
      <button onClick={playback.replay}>重播</button>
      <label>倍速 <select aria-label="倍速" value={playback.speed} onChange={e=>playback.setSpeed(Number(e.target.value))}><option value={.25}>0.25x</option><option value={.5}>0.5x</option><option value={1}>1x</option><option value={2}>2x</option></select></label>
    </div>
    <div className="preview-stages">{[false,true].map(effects=><section key={String(effects)}><h2>{effects?'完整特效':'纯动作'}</h2><InkStage battle={battle} time={playback.time} effects={effects} motionMode={motionMode} /></section>)}</div>
    <div className="preview-timeline"><input type="range" aria-label="动作进度" min={0} max={playback.duration} step={1} value={playback.time} onChange={e=>playback.seek(Number(e.target.value))} /><output>{Math.round(playback.time)} ms</output></div>
  </main>;
}

createRoot(document.getElementById('root')!).render(<MotionPreview />);
