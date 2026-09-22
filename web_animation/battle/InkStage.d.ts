import type { ReplayBattle, BattleEvent, Side } from '../../web/frontend/src/battle/replay';
import type { RigPose } from '../../web/frontend/src/battle/sampleMotion';
import type { MotionMode } from '../../web/frontend/src/battle/motionVariants';
export function draw(ctx: CanvasRenderingContext2D, battle: ReplayBattle, time: number, width: number, reducedMotion: boolean, effects: boolean, mode?: MotionMode): void;
export function poseAt(battle: ReplayBattle, side: Side, time: number, width: number, turn?: BattleEvent, mode?: MotionMode): { x: number; lift: number; opacity: number; blink: number; pose: RigPose; weapon: string; armed: boolean; sheathed: boolean; variant: string };
