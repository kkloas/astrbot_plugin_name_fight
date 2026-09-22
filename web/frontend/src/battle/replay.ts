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
  stacks?: number;
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

// Both frontends consume exactly the same event projection and gauge clock.
import { stateAt, initiativeAt, statusLabels, victoryLabels } from '../../../../web_animation/battle/replay.js';
export { stateAt, initiativeAt, statusLabels, victoryLabels };

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
