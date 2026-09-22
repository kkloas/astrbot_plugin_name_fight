import type { BattleEvent, ReplayBattle } from './replay';
export type MotionVariant = 'legacy' | 'current';
export type MotionMode = MotionVariant | 'mixed';
export declare function motionVariantFor(battle: ReplayBattle, event?: BattleEvent, mode?: MotionMode): MotionVariant;
