import { type impactFor } from './choreography';
import type { BattleEvent } from './replay';
type Point = [number, number];
export declare function swordEmphasis(event: BattleEvent): 0 | 1 | 2;
export declare function drawSwordSequenceEffects(ctx: CanvasRenderingContext2D, event: BattleEvent, local: number, tipAt: (time: number) => Point, dir: number, impact: ReturnType<typeof impactFor>): void;
export {};
