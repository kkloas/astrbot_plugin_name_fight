import { type impactFor } from './choreography';
import type { Technique, Weapon } from './martialVisuals';
type Point = [number, number];
type Impact = ReturnType<typeof impactFor>;
export declare function drawPreparation(ctx: CanvasRenderingContext2D, t: Technique, x: number, dir: number, local: number, ranged: boolean): void;
export declare function drawTechnique(ctx: CanvasRenderingContext2D, t: Technique, weapon: Weapon, origin: Point, target: Point, dir: number, age: number, force?: number): void;
export declare function drawImpact(ctx: CanvasRenderingContext2D, x: number, y: number, dir: number, age: number, impact: Impact, seed: number): void;
export declare function drawSampleAccent(ctx: CanvasRenderingContext2D, kind: 'sword' | 'spear' | 'kick', tip: Point, target: Point, dir: number, age: number, impact: Impact): void;
export {};
