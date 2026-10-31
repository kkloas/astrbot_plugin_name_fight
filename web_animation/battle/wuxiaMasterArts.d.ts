import type { BattleEvent, ReplayBattle, ReplayFighter, Side } from '../../web/frontend/src/battle/replay';
import type { RigPose } from '../../web/frontend/src/battle/sampleMotion';
import type { Technique } from '../../web/frontend/src/battle/martialVisuals';

export type SceneTheme = 'sunset' | 'snow' | 'bloodmoon' | 'classic';

export type MasterMove = {
    name: string;
    style: string;
    power: number;
    angle: number;
    lift: number;
    strokes: number;
    ranged: boolean;
    signature: boolean;
    ultimate: boolean;
};

export const masterArts: Record<string, {
    name: string;
    type: string;
    weapon: string;
    ink: string;
    glow: string;
    glowBright: string;
    sealColor: string;
    sash: string;
    sashHighlight: string;
    moves: MasterMove[];
}>;

export const masterMoves: { id: string; name: string; type: string; move: string; power: number }[];
export function isMasterArt(id?: string): boolean;
export function masterMoveFor(event?: BattleEvent): MasterMove | undefined;
export function masterTechnique(event?: BattleEvent, fighter?: ReplayFighter): Technique | undefined;
export function masterMotion(event: BattleEvent, time: number, travel: number, dodged?: boolean): {
    x: number;
    lift: number;
    opacity: number;
    blink: number;
    pose: RigPose;
} | undefined;
export function drawMasterSash(
    ctx: CanvasRenderingContext2D,
    side: Side,
    time: number,
    alpha: number,
    artId?: string,
    trailSamples?: { x: number; lift: number; pose: RigPose }[],
): void;
export function drawMasterFigure(
    ctx: CanvasRenderingContext2D,
    x: number,
    side: Side,
    pose: RigPose,
    time: number,
    weapon: string,
    alpha: number,
    lift: number,
    sheathed: boolean,
    artId?: string,
    trailSamples?: { x: number; lift: number; pose: RigPose }[],
): void;
export function drawTaijiBaguaSeal(
    ctx: CanvasRenderingContext2D,
    cx: number,
    cy: number,
    radius: number,
    rotation: number,
    glowColor: string,
    alpha: number,
    webEnhanced?: boolean,
): void;
export function drawMasterEffects(
    ctx: CanvasRenderingContext2D,
    event: BattleEvent,
    local: number,
    sampleAt: (t: number) => { tip: [number, number]; hand: [number, number]; root: [number, number] },
    target: [number, number],
    dir: number,
    impactAge: number,
    hit: boolean,
    width?: number,
    webEnhanced?: boolean,
): void;
export function drawWebSceneBackdrop(
    ctx: CanvasRenderingContext2D,
    width: number,
    time: number,
    sceneTheme?: SceneTheme,
    windImpulse?: number,
): void;
export function drawWebBattleStains(
    ctx: CanvasRenderingContext2D,
    battle: ReplayBattle,
    time: number,
    frameAt: (side: Side, at: number, turn?: BattleEvent) => { x: number },
): void;
export function drawWebSceneForeground(
    ctx: CanvasRenderingContext2D,
    width: number,
    time: number,
    sceneTheme?: SceneTheme,
    windImpulse?: number,
): void;
