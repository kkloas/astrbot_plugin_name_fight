import type { BattleEvent } from '../../web/frontend/src/battle/replay';
import type { poseAt } from './InkStage';
type Frame = ReturnType<typeof poseAt>;
export function drawArtTrigger(ctx: CanvasRenderingContext2D, event: BattleEvent, frame: Frame, dir: number, other: Frame, age: number): void;
export function drawArtFootwork(ctx: CanvasRenderingContext2D, id: string | undefined, x: number, dir: number, phase: number, time: number, trace?: {x: number; y: number}[], layers?: number): void;
export function drawArtAura(ctx: CanvasRenderingContext2D, frame: Frame, dir: number, states: string[], time: number, stacks: number): void;
