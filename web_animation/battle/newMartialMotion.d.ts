import { type RigPose } from './sampleMotion';
import type { BattleEvent } from './replay';
export declare const newArtIds: readonly ["sword_danyu", "blade_jingchao"];
export declare const isNewArt: (id?: string) => boolean;
export declare const newMotionSamples: {
    id: string;
    name: string;
    type: string;
    move: string;
}[];
export declare const isNewMove: (event?: BattleEvent) => boolean;
type Key = [number, number, number, number, number, number, number, number, number, number, number, number];
export type NewEffectKind = 'rise' | 'point' | 'return' | 'skim' | 'cross' | 'dive' | 'flurry' | 'phoenix' | 'sweep' | 'break' | 'undertow' | 'cascade' | 'surge' | 'divide';
type NewMove = {
    keys: Key[];
    strokes: [number, number][];
    kind: NewEffectKind;
    power: number;
    signature?: boolean;
};
export declare const newMartialScores: Record<string, Record<string, NewMove>>;
export declare const newMotionMoves: {
    id: string;
    name: string;
    type: string;
    move: string;
}[];
export declare function newMoveFor(event?: BattleEvent): NewMove;
export declare function newMartialMotion(event: BattleEvent, time: number, travel: number): {
    pose: RigPose;
    x: number;
    lift: number;
    opacity: number;
    blink: number;
} | undefined;
export {};
