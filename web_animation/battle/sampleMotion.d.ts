import type { BattleEvent } from './replay';
type Point = [number, number];
export type RigPose = {
    points: Point[];
    sword: number;
    lean: number;
    shoulders?: [Point, Point];
};
export type SampleMove = 'sword' | 'spear' | 'kick';
export declare const rigLengths: {
    arm: number;
    leg: number;
    torso: number;
    grip: number;
    stride: number;
};
export declare function sampleMove(event?: BattleEvent): SampleMove | undefined;
export declare function twoBone(root: Point, target: Point, length: number, pole: number): [Point, Point];
export declare function walkContacts(progress: number, distance: number): {
    root: number;
    feet: Point[];
};
export declare function sampleMotion(kind: SampleMove, time: number, travel: number, missed?: boolean): {
    x: number;
    lift: number;
    pose: RigPose;
    opacity: number;
    blink: number;
};
export {};
