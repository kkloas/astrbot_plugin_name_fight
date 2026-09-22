import { type RigPose } from './sampleMotion';
import type { BattleEvent } from './replay';
type Key = [number, number, number, number, number, number, number, number, number];
export declare function swordSequenceFor(event?: BattleEvent): Key[] | undefined;
export declare function swordSequence(event: BattleEvent, t: number, travel: number, missed?: boolean): {
    pose: RigPose;
    x: number;
    lift: number;
    opacity: number;
    blink: number;
} | undefined;
export {};
