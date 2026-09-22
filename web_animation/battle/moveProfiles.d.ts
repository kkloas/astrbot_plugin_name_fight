import type { BattleEvent } from './replay';
export type MoveStyle = 'thrust' | 'cross' | 'rise' | 'cleave' | 'sweep' | 'spin' | 'flurry' | 'leap' | 'draw' | 'palm' | 'shock' | 'kick' | 'hook' | 'coil' | 'fan' | 'needle' | 'rain' | 'pluck' | 'strum' | 'crescendo';
export type MoveTheme = 'snow' | 'petal' | 'cloud' | 'gold' | 'leaf' | 'wind' | 'ink' | 'vermilion' | 'jade' | 'silver' | 'mist' | 'sound';
export type MoveProfile = {
    style: MoveStyle;
    theme: MoveTheme;
    variation: number;
    anticipation: number;
    amplitude: number;
};
export declare const moveProfiles: Record<string, Record<string, MoveProfile>>;
export declare const themeColors: Record<MoveTheme, string>;
export declare function profileFor(event?: BattleEvent): MoveProfile;
