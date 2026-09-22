import { type impactFor } from './choreography';
import { type MoveProfile } from './moveProfiles';
type Point = [number, number];
type Impact = ReturnType<typeof impactFor>;
export declare function drawMoveTheme(ctx: CanvasRenderingContext2D, p: MoveProfile, tip: Point, target: Point, dir: number, age: number, impact: Impact): void;
export {};
