import type { BattleEvent } from './replay';
import type { Technique } from './martialVisuals';
export declare const unit: (n: number) => number;
export declare const ease: (n: number) => number;
export declare function impactFor(event: BattleEvent | undefined, maxHp: number, technique: Technique): {
    hit: boolean;
    ratio: number;
    force: number;
    heavy: boolean;
    cinematic: boolean;
    hold: number;
};
export declare function contactTime(local: number, contact: number, hold: number): number;
export declare function plantedFoot(progress: number, start: number, distance: number, offset: number): readonly [number, number];
