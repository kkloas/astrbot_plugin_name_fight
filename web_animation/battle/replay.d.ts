import type { ReplayBattle, BattleEvent, Side } from '../../web/frontend/src/battle/replay';
export const statusLabels: Record<string, string>;
export const victoryLabels: Record<string, string>;
export function stateAt(battle: ReplayBattle, time: number): {
  hp: Record<Side, number>; states: Record<Side, string[]>; stacks: Record<Side, number>;
  weaponsReady: Record<Side, boolean>; gauge: Record<Side, number>; speeds: Record<Side, number>;
  hasGauge: boolean; logs: string[]; turn?: BattleEvent; ended: boolean;
};
export function initiativeAt(battle: ReplayBattle, time: number, state?: ReturnType<typeof stateAt>): Record<Side, number>;
