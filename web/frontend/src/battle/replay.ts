import { useEffect, useRef, useState } from 'react';

export type Side = 'a' | 'b';
export type BattleEvent = {
  type: string;
  time: number;
  action?: number;
  actor?: Side;
  target?: Side;
  amount?: number;
  hpBefore?: number;
  hpAfter?: number;
  maxHp?: number;
  crit?: boolean;
  cause?: string;
  bodyPart?: string;
  bodyPartKey?: string;
  status?: string;
  reason?: string;
  move?: string;
  martialArtId?: string;
  weaponType?: string;
  moveIndex?: number;
  effect?: string;
  multiplier?: number;
  fromSide?: Side;
  duration?: number;
  sourceSkill?: { category: string; id?: string; name: string };
  weaponsReady?: Record<Side, boolean>;
  gauge?: Record<Side, number>;
  gaugeFrom?: Record<Side, number>;
  gaugeBefore?: Record<Side, number>;
  gaugeValue?: number;
  speeds?: Record<Side, number>;
  speedAfter?: number;
  endTime?: number;
  ticksAdvanced?: number;
  victoryKind?: 'quick' | 'dominant' | 'standard' | 'clutch' | 'judged' | 'draw';
  victoryVariant?: number;
  logs?: string[];
  states?: Record<Side, { type: string; duration: number }[]>;
  final?: Record<Side, { hp: number; maxHp: number }>;
};

export type ReplayEntry = { id?: string; name: string; type?: string };
export type ReplayFighter = {
  name: string; stats: { hp: number; spd?: number }; currentHp?: number; martialArt: ReplayEntry;
  neigong?: ReplayEntry; qinggong?: ReplayEntry;
};
export type ReplayBattle = {
  attacker: ReplayFighter;
  defender: ReplayFighter;
  winner: string | null;
  events: BattleEvent[];
  rating?: Record<string, { name: string; before: number; after: number; delta: number }> | null;
};

export const statusLabels: Record<string, string> = {
  bleeding: '流血', poisoned: '中毒', stunned: '眩晕', slowed: '迟缓',
  weakened: '虚弱', disarmed: '缴械', armor_broken: '破甲', crisis_defense: '护体',
};

export const victoryLabels:Record<string,string>={quick:'速战速决',dominant:'从容取胜',standard:'胜负已分',clutch:'险中取胜',judged:'略胜半筹',draw:'不分胜负'};

export function stateAt(battle: ReplayBattle, time: number) {
  const hp = {
    a: battle.attacker.currentHp ?? battle.attacker.stats.hp,
    b: battle.defender.currentHp ?? battle.defender.stats.hp,
  };
  const states: Record<Side, string[]> = { a: [], b: [] };
  const weaponsReady = { a: true, b: true };
  const gauge = {a:0,b:0};
  const speeds = {a:battle.attacker.stats.spd || 0,b:battle.defender.stats.spd || 0};
  let hasGauge=false;
  const logs: string[] = [];
  let turn: BattleEvent | undefined;
  let ended = false;
  for (const event of battle.events) {
    if (event.time > time) break;
    if (event.target && event.hpAfter !== undefined) hp[event.target] = event.hpAfter;
    if (event.type === 'turn_start') turn = event;
    if (event.gauge) {
      hasGauge=true;
      if(event.type==='gauge_charge' && event.gaugeFrom && event.endTime!==undefined) {
        const phase=Math.max(0,Math.min(1,(time-event.time)/Math.max(1,event.endTime-event.time)));
        for(const side of ['a','b'] as Side[]) gauge[side]=event.gaugeFrom[side]+(event.gauge[side]-event.gaugeFrom[side])*phase;
      } else Object.assign(gauge,event.gauge);
    }
    if(event.speeds) Object.assign(speeds,event.speeds);
    if(event.target && event.gaugeValue!==undefined) gauge[event.target]=event.gaugeValue;
    if(event.target && event.speedAfter!==undefined) speeds[event.target]=event.speedAfter;
    if (event.type === 'status_apply' && event.target && event.status) {
      if (!states[event.target].includes(event.status)) states[event.target].push(event.status);
      if (event.status === 'disarmed') weaponsReady[event.target] = false;
    }
    if (event.weaponsReady) Object.assign(weaponsReady, event.weaponsReady);
    if (event.states) {
      states.a = event.states.a.filter(s => s.duration > 0).map(s => s.type);
      states.b = event.states.b.filter(s => s.duration > 0).map(s => s.type);
    }
    if (event.type === 'battle_end') {
      ended = true;
      if (event.final) { hp.a = event.final.a.hp; hp.b = event.final.b.hp; }
    }
    logs.push(...(event.logs || []));
  }
  return { hp, states, weaponsReady, gauge, speeds, hasGauge, logs, turn, ended };
}

export function initiativeAt(battle: ReplayBattle, time: number, state=stateAt(battle,time)) {
  const gauge={...state.gauge};
  const charges=battle.events.filter(e=>e.type==='gauge_charge' && e.endTime!==undefined);
  const index=charges.findIndex(e=>e.endTime!>time);
  const charge=charges[index];
  if(!charge?.gauge || !charge.gaugeFrom) return gauge;
  const start=index>0?charges[index-1].endTime!:charge.time;
  // Spread the next recorded tick accumulation across the preceding animation,
  // rather than squeezing it into the short gap between two turns. Resource
  // boosts and actual speed changes rebase the interpolation immediately.
  const rawProgress=time<charge.time?0:Math.max(0,Math.min(1,(time-charge.time)/Math.max(1,charge.endTime!-charge.time)));
  for(const side of ['a','b'] as Side[]) {
    let origin=start;
    for(const event of battle.events) {
      if(event.time>Math.min(time,charge.time)) break;
      if(event.target===side && event.gaugeValue!==undefined) origin=Math.max(origin,event.time);
    }
    const integral=(end:number)=>{
      if(end<=origin) return 0;
      let speed=(side==='a'?battle.attacker:battle.defender).stats.spd || 1;
      let cursor=origin,total=0;
      for(const event of battle.events) {
        if(event.time>end) break;
        const next=event.speeds?.[side] ?? (event.target===side?event.speedAfter:undefined);
        if(next===undefined) continue;
        if(event.time>origin) {total+=(event.time-cursor)*speed;cursor=event.time;}
        speed=next;
      }
      return total+(end-cursor)*speed;
    };
    const progress=Math.max(0,Math.min(1,integral(time)/Math.max(1,integral(charge.endTime!))));
    gauge[side]+=(charge.gauge[side]-charge.gaugeFrom[side])*(progress-rawProgress);
  }
  return gauge;
}

export function useBattlePlayback(battle: ReplayBattle | null) {
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const clock = useRef(0);
  const duration = battle?.events[battle.events.length - 1]?.time || 0;
  useEffect(() => {
    clock.current = 0;
    setTime(0);
    setPlaying(Boolean(battle));
  }, [battle]);
  useEffect(() => {
    if (!playing || !battle) return;
    let frame = 0;
    let previous = performance.now();
    const tick = (now: number) => {
      // Hidden tabs do not consume the replay or jump over the fight on return.
      const elapsed = document.hidden ? 0 : Math.min(80, now - previous);
      previous = now;
      clock.current = Math.min(duration, clock.current + elapsed * speed);
      setTime(clock.current);
      if (clock.current >= duration) setPlaying(false);
      else frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [battle, duration, playing, speed]);
  const seek = (value: number) => {
    clock.current = Math.max(0, Math.min(duration, value));
    setTime(clock.current);
    if (clock.current >= duration) setPlaying(false);
  };
  const replay = () => { seek(0); setPlaying(true); };
  return { time, playing, speed, duration, seek, replay, setPlaying, setSpeed };
}

export type Playback = ReturnType<typeof useBattlePlayback>;
