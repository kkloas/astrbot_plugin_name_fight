import type { BattleEvent, ReplayFighter } from './replay';
export type Weapon = 'sword' | 'katana' | 'blade' | 'spear' | 'brush' | 'unarmed' | 'needles' | 'zither' | 'tokens' | 'heavy_sword' | 'whip';
export type Motion = 'thrust' | 'slash' | 'rise' | 'cleave' | 'sweep' | 'flurry' | 'leap' | 'draw' | 'palm' | 'kick' | 'throw' | 'pluck';
export type Trail = 'edge' | 'point' | 'wave' | 'dust' | 'needles' | 'sound' | 'vortex' | 'mist';
export type Pattern = 'direct' | 'cross' | 'wheel' | 'fall' | 'fan' | 'rain' | 'spiral' | 'focus' | 'crescendo';
export type Technique = {
    motion: Motion;
    trail: Trail;
    weight: number;
    flourish?: 'plum' | 'cloud' | 'crimson' | 'phantom';
    feint?: boolean;
    pattern?: Pattern;
    color?: string;
};
export declare const techniques: Record<string, Record<string, Technique>>;
export declare function weaponFor(fighter: ReplayFighter): Weapon;
export declare function legacyTechniqueFor(event: BattleEvent | undefined, fighter: ReplayFighter): Technique;
export declare function techniqueFor(event: BattleEvent | undefined, fighter: ReplayFighter): Technique;
export declare const effectLabels: Record<string, string>;
