import type { RigPose } from '../../web/frontend/src/battle/sampleMotion';

export const names: string[];
export const notes: string[];
export function qinPose(pose: RigPose, index: number, time: number): RigPose;
export function qinFX(ctx: CanvasRenderingContext2D, index: number, time: number, sourceX: number, targetX: number, hit: boolean): void;
export function qinTime(local: number, contact?: number): number;
