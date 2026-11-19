import type { BattleEvent } from '../../web/frontend/src/battle/replay';
import type { RigPose } from '../../web/frontend/src/battle/sampleMotion';

export const xianglongArt: {
    name: string;
    type: string;
    weapon: string;
    ink: string;
    glow: string;
    glowBright: string;
    sealColor: string;
    sash: string;
    sashHighlight: string;
    moves: {
        name: string;
        style: string;
        power: number;
        angle: number;
        lift: number;
        strokes: number;
        ranged: boolean;
        signature: boolean;
        ultimate: boolean;
    }[];
};

export function drawStripSlicedImage(
    ctx: CanvasRenderingContext2D,
    img: HTMLImageElement | undefined,
    originX: number,
    originY: number,
    drawW: number,
    drawH: number,
    opts?: {
        slices?: number;
        amp?: number;
        freq?: number;
        phase?: number;
        dir?: number;
        angle?: number;
        alpha?: number;
        reveal?: number;
        travelOffset?: number;
        rigidFrom?: number;
        featherRight?: number;
        clipMinX?: number;
        clipMaxX?: number;
    },
): void;

export function xianglongMotion(event: BattleEvent, time: number, travel: number, dodged?: boolean): {
    x: number;
    lift: number;
    opacity: number;
    blink: number;
    pose: RigPose;
} | undefined;

export function drawXianglongEffects(
    ctx: CanvasRenderingContext2D,
    event: BattleEvent,
    local: number,
    sampleAt: (t: number) => { tip: [number, number]; hand: [number, number]; rearHand?: [number, number]; root: [number, number]; frame?: unknown },
    target: [number, number],
    dir: number,
    impactAge: number,
    hit: boolean,
    width?: number,
    webEnhanced?: boolean,
): void;
