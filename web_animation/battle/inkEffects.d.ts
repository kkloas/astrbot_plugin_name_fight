import type { BattleEvent } from './replay';
export declare function drawAura(ctx: CanvasRenderingContext2D, x: number, y: number, states: string[], time: number, stacks?: number): void;
export declare function drawTrigger(ctx: CanvasRenderingContext2D, event: BattleEvent, x: number, otherX: number, age: number): void;
export type FootTrace = {
    x: number;
    y: number;
};
export declare function drawFootwork(ctx: CanvasRenderingContext2D, id: string | undefined, x: number, dir: number, phase: number, time: number, trace?: FootTrace[]): void;
