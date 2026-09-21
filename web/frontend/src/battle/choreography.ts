import type { BattleEvent } from './replay';
import type { Technique } from './martialVisuals';

export const unit = (n: number) => Math.max(0, Math.min(1, n));
export const ease = (n: number) => { const t=unit(n); return t*t*(3-2*t); };

export function impactFor(event: BattleEvent | undefined, maxHp: number, technique: Technique) {
  const hit=event?.type==='damage' && event.cause==='strike' && (event.amount || 0)>0;
  const ratio=hit?(event.amount || 0)/Math.max(1,maxHp):0;
  // HP-relative damage controls force. A named finisher alone cannot fake a heavy hit.
  const force=hit?unit(ratio*2.6+(event?.crit ? .16:0)):0;
  const heavy=hit && (ratio>=.22 || (Boolean(event?.crit) && ratio>=.13));
  return {hit,ratio,force,heavy,cinematic:heavy && (ratio>=.32 || technique.weight>=1.5),
    hold:hit?Math.round(22+force*78):0};
}

// Hold at contact, then repay the held time before recovery. Absolute-time sampling
// keeps seek, reverse seek, pause and double speed identical to normal playback.
export function contactTime(local: number, contact: number, hold: number) {
  const age=local-contact;
  if(age<=0 || hold<=0) return local;
  if(age<hold) return contact;
  return local-hold*(1-ease((age-hold)/260));
}

export function plantedFoot(progress: number, start: number, distance: number, offset: number) {
  const steps=3;
  const phase=unit(progress)*steps+offset;
  const step=Math.floor(phase);
  const part=phase-step;
  const stride=distance/steps;
  // First half of each cycle stays fixed in world space; second half lifts to
  // the next contact. Return local coordinates relative to the moving pelvis.
  const swing=ease((part-.48)/.52);
  const world=start+(step-offset+swing)*stride;
  return [world-(start+distance*unit(progress)), -Math.sin(swing*Math.PI)*28] as const;
}
