import { type RigPose } from './sampleMotion';
import type { BattleEvent } from './replay';
import type { Weapon } from './martialVisuals';
export declare function moveMotion(event: BattleEvent, t: number, travel: number, weapon: Weapon, missed?: boolean): {
    x: number;
    lift: number;
    pose: RigPose;
    opacity: number;
    blink: number;
} | undefined;
