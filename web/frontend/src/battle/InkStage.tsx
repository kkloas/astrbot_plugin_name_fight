import { useEffect, useRef } from 'react';
import { stateAt, type ReplayBattle } from './replay';
import { motionVariantFor, type MotionMode } from './motionVariants';
import { draw, poseAt } from '../../../../web_animation/battle/InkStage.js';
import { weaponFor } from '../../../../web_animation/battle/martialVisuals.js';
import type { SceneTheme } from '../../../../web_animation/battle/wuxiaMasterArts';
export { draw, poseAt };
export type { SceneTheme };

export function InkStage({
  battle,
  time,
  effects = true,
  motionMode = 'mixed',
  webEnhanced = true,
  sceneTheme = 'sunset',
}: {
  battle: ReplayBattle;
  time: number;
  effects?: boolean;
  motionMode?: MotionMode;
  webEnhanced?: boolean;
  sceneTheme?: SceneTheme;
}) {
  const canvas=useRef<HTMLCanvasElement>(null);
  const latest=useRef({battle,time,effects,motionMode,webEnhanced,sceneTheme});
  latest.current={battle,time,effects,motionMode,webEnhanced,sceneTheme};
  const paint=() => {
    const element=canvas.current;
    if(!element) return;
    const width=element.getBoundingClientRect().width;
    const logicalWidth=width<600?600:1000;
    element.style.aspectRatio=`${logicalWidth} / 430`;
    const ratio=Math.min(window.devicePixelRatio||1,2);
    const w=Math.max(1,Math.round(width*ratio));
    const h=Math.round(w*430/logicalWidth);
    if(element.width!==w || element.height!==h) {element.width=w;element.height=h;}
    const ctx=element.getContext('2d');
    if(ctx) {
      ctx.setTransform(w/logicalWidth,0,0,h/430,0,0);
      draw(
        ctx,
        latest.current.battle,
        latest.current.time,
        logicalWidth,
        window.matchMedia('(prefers-reduced-motion: reduce)').matches,
        latest.current.effects,
        latest.current.motionMode,
        { webEnhanced: latest.current.webEnhanced, sceneTheme: latest.current.sceneTheme },
      );
    }
  };
  useEffect(paint,[battle,time,effects,motionMode,webEnhanced,sceneTheme]);
  useEffect(()=>{
    const observer=new ResizeObserver(paint);
    if(canvas.current) observer.observe(canvas.current);
    return ()=>observer.disconnect();
  },[]);
  const turn=stateAt(battle,time).turn;
  const attack=turn && battle.events.find(e=>e.type==='attack' && e.action===turn.action);
  return <canvas ref={canvas} className="ink-duel-canvas" role="img" aria-label="水墨武学交手动画"
    data-motion-variant={motionVariantFor(battle,attack,motionMode)}
    data-scene-theme={sceneTheme}
    data-weapon-a={weaponFor(battle.attacker)} data-weapon-b={weaponFor(battle.defender)} />;
}
