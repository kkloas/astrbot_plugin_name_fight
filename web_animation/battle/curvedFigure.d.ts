import type { RigPose } from './sampleMotion';
import type { Weapon } from './martialVisuals';
export declare function drawCurvedFigure(ctx: CanvasRenderingContext2D, x: number, dir: number, pose: RigPose, time: number, weapon: Weapon, alpha: number, lift: number, sheathed: boolean, artId?: string): void;
