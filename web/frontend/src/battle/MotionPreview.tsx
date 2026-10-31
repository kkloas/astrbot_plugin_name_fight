import { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { InkStage, type SceneTheme } from './InkStage';
import { useBattlePlayback, type BattleEvent, type ReplayBattle, type Side } from './replay';
import { moveProfiles } from './moveProfiles';
import type { MotionMode } from './motionVariants';
import { newMotionMoves, isNewArt, newMoveFor } from './newMartialMotion';
import { expandedMoves, expandedMoveFor, isExpandedArt } from '../../../../web_animation/battle/expandedArts.js';
import { masterMoves, masterMoveFor, isMasterArt } from '../../../../web_animation/battle/wuxiaMasterArts.js';
import './motionPreview.css';
import { api } from '../api';
import { previewCount, previewSkillEvents, skillStages, type Skill } from './skillPreview';

type Config = { neigong: Skill[]; qinggong: Skill[] };

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
const moves=[
  ...masterMoves,
  ...samples,
  ...Object.entries(moveProfiles).filter(([id])=>!isNewArt(id)&&!isExpandedArt(id)&&!isMasterArt(id)).flatMap(([id,profiles])=>Object.keys(profiles)
    .filter(move=>!samples.some(m=>m.id===id && m.move===move))
    .map(move=>({id,name:arts[id][0],type:arts[id][1],move}))),
  ...newMotionMoves,
  ...expandedMoves,
];
const isDedicatedArt=(id:string)=>isNewArt(id)||isExpandedArt(id)||isMasterArt(id);

function MotionPreview() {
  const [config, setConfig] = useState<Config | null>(null);
  const [accessError, setAccessError] = useState('');
  const [innerId, setInnerId] = useState('');
  const [lightId, setLightId] = useState('');
  const [innerStage, setInnerStage] = useState('full');
  const [lightStage, setLightStage] = useState('full');
  const [loop, setLoop] = useState(false);
  useEffect(() => { api<Config>('/api/admin/practice/config').then(setConfig).catch(() => setAccessError('仅管理员可使用特效拆解台, 请先登录管理员账号.')); }, []);
  const [selection,setSelection]=useState(()=>{
    const qArt=new URLSearchParams(location.search).get('art');
    const qMove=new URLSearchParams(location.search).get('move');
    if(qArt && qMove) {
      const idx=moves.findIndex(m=>m.id===qArt && m.move===qMove);
      if(idx>=0) return idx;
    }
    if(qArt) return Math.max(0,moves.findIndex(m=>m.id===qArt));
    return 6; // Default to 玄墨剑典 / 万剑归宗 for immediate visual showcase!
  });
  const [side,setSide]=useState<Side>('a');
  const [missed,setMissed]=useState(false);
  const [motionMode,setMotionMode]=useState<MotionMode>('current');
  const [sceneTheme,setSceneTheme]=useState<SceneTheme>('sunset');
  const selectedInner=config?.neigong.find(item=>item.id===innerId);
  const selectedLight=config?.qinggong.find(item=>item.id===lightId);
  const rounds=Math.max(previewCount(selectedInner,'neigong',innerStage),previewCount(selectedLight,'qinggong',lightStage));
  const battle=useMemo<ReplayBattle>(()=>{
    const art=moves[selection],target:Side=side==='a'?'b':'a';
    const master=masterMoveFor({martialArtId:art.id,move:art.move,type:'attack',time:0});
    const authored=newMoveFor({martialArtId:art.id,move:art.move,type:'attack',time:0});
    const expanded=expandedMoveFor({martialArtId:art.id,move:art.move,type:'attack',time:0});
    const damage=master?(master.ultimate?380:Math.round(185*master.power)):expanded?Math.round(180*expanded.power):authored?(authored.signature?340:Math.round(180*authored.power)):selection===1?340:140;
    const qinggong=selectedLight;
    const neigong=selectedInner;
    const sample={name:art.move,stats:{hp:1000,spd:60},martialArt:art,neigong,qinggong};
    const opponent={name:'试招对手',stats:{hp:1000,spd:60},martialArt:{id:art.id==='sword_xuanmo'?'blade_chixiao':'palm_crushing_wave',name:art.id==='sword_xuanmo'?'赤霄断魂刀':'碎浪掌',type:art.id==='sword_xuanmo'?'blade':'palm'},qinggong:{id:'taxue_wuhen',name:'踏雪无痕'}};
    const events: BattleEvent[]=[{type:'battle_start',time:0},
      ...previewSkillEvents(neigong,'neigong',innerStage,side,rounds),
      ...previewSkillEvents(qinggong,'qinggong',lightStage,side,rounds)];
    for(let i=0;i<rounds;i++){
      const base=i*2500,action=i+1;
      events.push({type:'turn_start',time:base+300,action,actor:side},
        {type:'attack',time:base+850,action,actor:side,target,martialArtId:art.id,move:art.move,weaponType:art.type},
        missed?{type:'dodge',time:base+1250,action,actor:side,target}:
          {type:'damage',time:base+1250,action,actor:side,target,cause:'strike',amount:damage,hpAfter:1000-damage,maxHp:1000,crit:Boolean(master?.ultimate),bodyPartKey:'chest'},
        {type:'turn_end',time:base+2100,action});
    }
    events.push({type:'battle_end',time:rounds*2500+700});
    events.sort((a,b)=>a.time-b.time);
    return {attacker:side==='a'?sample:opponent,defender:side==='b'?sample:opponent,winner:null,events};
  },[selection,side,missed,selectedInner,selectedLight,innerStage,lightStage,rounds]);
  const playback=useBattlePlayback(battle,loop);
  const phase=Math.min(rounds,Math.floor(playback.time/2500)+1);
  if (accessError) return <main className="motion-preview"><p role="alert">{accessError}</p><a href="/">返回游戏</a></main>;
  if (!config) return <main className="motion-preview">正在检查管理员权限...</main>;
  return <main className="motion-preview">
    <header><h1>动作样板 · 新武学拆解台</h1><a href="/">返回游戏剧场</a></header>
    <p>内功和轻功使用模拟触发事件预览特效, 不代表实际战斗的触发条件或伤害数值.</p>
    <div className="preview-controls">
      <label>招式 <select aria-label="招式" value={selection} onChange={e=>setSelection(Number(e.target.value))}>{moves.map((m,i)=><option key={`${m.id}/${m.move}`} value={i}>{m.name} / {m.move}</option>)}</select></label>
      <label>内功 <select value={innerId} onChange={e=>{setInnerId(e.target.value);setInnerStage('full');}}><option value="">不使用</option>{config.neigong.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      {selectedInner && <label>内功阶段 <select value={innerStage} onChange={e=>setInnerStage(e.target.value)}>{skillStages(selectedInner,'neigong').map(item=><option key={item.value} value={item.value}>{item.label}</option>)}</select></label>}
      <label>轻功 <select value={lightId} onChange={e=>{setLightId(e.target.value);setLightStage('full');}}><option value="">不使用</option>{config.qinggong.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      {selectedLight && <label>轻功阶段 <select value={lightStage} onChange={e=>setLightStage(e.target.value)}>{skillStages(selectedLight,'qinggong').map(item=><option key={item.value} value={item.value}>{item.label}</option>)}</select></label>}
      <label>出招方 <select aria-label="出招方" value={side} onChange={e=>setSide(e.target.value as Side)}><option value="a">左方</option><option value="b">右方</option></select></label>
      <label>画境 <select aria-label="画境" value={sceneTheme} onChange={e=>setSceneTheme(e.target.value as SceneTheme)}><option value="sunset">残阳竹林</option><option value="snow">寒江孤雪</option><option value="bloodmoon">朱砂血月</option><option value="classic">素宣原卷</option></select></label>
      <label>动画 <select aria-label="动画版本" value={isDedicatedArt(moves[selection].id)?'current':motionMode} disabled={isDedicatedArt(moves[selection].id)} onChange={e=>setMotionMode(e.target.value as MotionMode)}><option value="mixed">随机混用</option><option value="legacy">旧版</option><option value="current">{isDedicatedArt(moves[selection].id)?'专属':'新版'}</option></select></label>
      <label><input type="checkbox" checked={missed} onChange={e=>setMissed(e.target.checked)} /> 闪避</label>
      <label><input type="checkbox" checked={loop} onChange={e=>setLoop(e.target.checked)} /> 循环播放</label>
      <button onClick={()=>playback.setPlaying(!playback.playing)}>{playback.playing?'暂停':'播放'}</button>
      <button onClick={playback.replay}>重播</button>
      <label>倍速 <select aria-label="倍速" value={playback.speed} onChange={e=>playback.setSpeed(Number(e.target.value))}><option value={.25}>0.25x</option><option value={.5}>0.5x</option><option value={1}>1x</option><option value={2}>2x</option></select></label>
    </div>
    <p aria-live="polite">{rounds > 1 ? `当前阶段: ${phase} / ${rounds}` : '当前阶段: 单次预览'}{selectedInner ? ` | 内功: ${selectedInner.name}${innerStage === 'full' && previewCount(selectedInner,'neigong',innerStage) > 1 ? ` 第 ${Math.min(phase, previewCount(selectedInner,'neigong',innerStage))} 层` : ''}` : ''}{selectedLight ? ` | 轻功: ${selectedLight.name}${lightStage === 'full' && previewCount(selectedLight,'qinggong',lightStage) > 1 ? ` 第 ${Math.min(phase, previewCount(selectedLight,'qinggong',lightStage))} 层` : ''}` : ''}</p>
    <div className="preview-stages">{[false,true].map(effects=><section key={String(effects)}><h2>{effects?'Web 增强特效':'纯骨骼动作 (Bot 素底对照)'}</h2><InkStage battle={battle} time={playback.time} effects={effects} motionMode={motionMode} webEnhanced={effects} sceneTheme={sceneTheme} /></section>)}</div>
    <div className="preview-timeline"><input type="range" aria-label="动作进度" min={0} max={playback.duration} step={1} value={playback.time} onChange={e=>playback.seek(Number(e.target.value))} /><output>{Math.round(playback.time)} ms</output></div>
  </main>;
}

createRoot(document.getElementById('root')!).render(<MotionPreview />);
