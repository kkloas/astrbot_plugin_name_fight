import type { NewEffectKind } from './newMartialMotion';
type Point = [number, number];
export type NewEffectFrame = {
    hand: Point;
    tip: Point;
    root: Point;
};
type EffectScore = {
    kind: NewEffectKind;
    power: number;
    strokes: [number, number][];
    signature?: boolean;
};
export declare function drawNewMartialEffects(ctx: CanvasRenderingContext2D, feather: boolean, local: number, sample: (t: number) => NewEffectFrame, dir: number, hitAge: number, hit: boolean, force: number, target: Point, definition?: EffectScore): void;
export {};
