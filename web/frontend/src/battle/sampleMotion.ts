import { ease, unit } from './choreography';
import type { BattleEvent } from './replay';

type Point = [number, number];
export type RigPose = { points: Point[]; sword: number; lean: number; shoulders?: [Point,Point] };
export type SampleMove = 'sword' | 'spear' | 'kick';
export const rigLengths = { arm: 40, leg: 48, torso: 52, grip: 68, stride: 150 };
const mix = (a: number, b: number, t: number) => a + (b-a)*t;
const point = (a: Point, b: Point, t: number): Point => [mix(a[0],b[0],t),mix(a[1],b[1],t)];
function curve(t: number, keys: [number, number][]) {
  for(let i=1;i<keys.length;i++) if(t<keys[i][0]) {
    return mix(keys[i-1][1],keys[i][1],ease((t-keys[i-1][0])/(keys[i][0]-keys[i-1][0])));
  }
  return keys[keys.length-1][1];
}

export function sampleMove(event?: BattleEvent): SampleMove | undefined {
  if(event?.martialArtId==='sword_falling_plum' && event.move==='寒枝点雪') return 'sword';
  if(event?.martialArtId==='staff_yuejiaqiang' && event.move==='绝招·回马枪') return 'spear';
  if(event?.martialArtId==='leg_shadow_whirl' && event.move==='穿云踢') return 'kick';
}

// Clamp unreachable targets, not bone lengths. The pole chooses the elbow/knee side.
export function twoBone(root: Point, target: Point, length: number, pole: number): [Point, Point] {
  const dx=target[0]-root[0],dy=target[1]-root[1];
  const raw=Math.hypot(dx,dy),d=Math.max(.001,Math.min(length*2-2,raw));
  const ux=raw>.001?dx/raw:0,uy=raw>.001?dy/raw:1;
  const end:Point=[root[0]+ux*d,root[1]+uy*d];
  const bend=Math.sqrt(length*length-d*d/4)*pole;
  return [[root[0]+ux*d/2-uy*bend,root[1]+uy*d/2+ux*bend],end];
}

// Alternating foot contacts in world coordinates. The planted foot never follows
// the pelvis; only the other foot lifts and swings to its next contact.
export function walkContacts(progress: number, distance: number) {
  const count=Math.max(1,Math.ceil(Math.abs(distance)/rigLengths.stride));
  const phase=unit(progress)*count,index=Math.min(count-1,Math.floor(phase));
  const f=ease(phase-index),sign=distance<0?-1:1;
  const feet:Point[]=[[-39,0],[39,0]];
  for(let i=0;i<=index;i++) {
    const leg=(i+(sign<0?1:0))%2;
    const end=(i+1)*distance/count+sign*48;
    if(i<index) feet[leg]=[end,0];
    else feet[leg]=[mix(feet[leg][0],end,f),-Math.sin(Math.PI*f)*48];
  }
  return {root:(index+f)*distance/count,feet};
}

export function sampleMotion(kind: SampleMove, time: number, travel: number, missed=false) {
  const t=Math.max(0,time);
  // A fully extended arm reaches farther; stop the body short of the opponent.
  travel=Math.max(0,travel-(kind==='kick'?0:28));
  const runEnd=kind==='spear'?440:kind==='kick'?540:680;
  const staging=kind==='spear'?travel*.22:kind==='kick'?travel*.48:Math.max(0,travel-92);
  const run=walkContacts((t-180)/(runEnd-180),staging);
  const progress=unit((t-180)/(runEnd-180));
  const strides=Math.max(1,Math.ceil(Math.abs(staging)/rigLengths.stride));
  const cadence=progress*strides*Math.PI;
  const running=Math.sin(Math.PI*progress);
  let x=run.root,lift=-28*Math.abs(Math.sin(cadence))*running;
  let opacity=1,blink=0;
  let feet=run.feet.map(p=>[p[0]-x,p[1]] as Point);
  const step=Math.min(strides-1,Math.floor(progress*strides));
  const spread=Math.sin(Math.PI*(progress*strides-step))*running;
  feet=feet.map((p,i)=>point(p,i===step%2?[68,-45]:[-79,-26],spread));
  let hip:Point=[-7,-82];
  let tilt=curve(t,[[0,7],[180,7],[300,16],[runEnd,9]]);
  let front:Point=[61+Math.sin(cadence)*18*running,-116-Math.cos(cadence)*18*running];
  let rear:Point=[-47-Math.sin(cadence)*12*running,-116+Math.cos(cadence)*20*running];
  let angle=-.45;
  const endFeet=walkContacts(1,staging).feet;
  const drive=ease((t-790)/160);
  const settle=ease((t-1080)/160);
  if(t>=runEnd) {
    x=curve(t,[[runEnd,staging],[790,staging],[950,travel],[1080,travel+(missed?12:0)],[1240,travel]]);
    feet=endFeet.map(p=>[p[0]-x,p[1]] as Point);
    // Open into a broad stance before the shoulder and striking arm follow.
    for(const i of [0,1]) {
      const start=i===0?runEnd:800,end=i===0?790:925;
      const step=ease((t-start)/(end-start));
      feet[i]=[mix(endFeet[i][0],travel+(i===0?-55:45),step)-x,-Math.sin(Math.PI*step)*25];
    }
    hip=[-7+14*drive,-82+6*drive-7*settle];
    tilt=curve(t,[[runEnd,9],[800,9],[885,20],[950,24],[1080,24],[1240,7]]);
  }
  if(kind==='sword') {
    const extend=ease((t-830)/120)*(1-ease((t-(missed?1100:1060))/180));
    const chamber=ease((t-680)/110)*(1-extend);
    front=point(point(front,[-14,-100],chamber),[hip[0]+tilt+86,-104],extend);
    rear=point(rear,[-66,-136],ease((t-805)/120)*(1-settle));
    angle=curve(t,[[0,-.45],[550,-.65],[800,-.08],[950,-.02],[1080,-.02],[1240,-.45]]);
  } else if(kind==='spear') {
    tilt=curve(t,[[0,7],[440,9],[580,-12],[710,-12],[895,18],[1060,18],[1240,7]]);
    angle=curve(t,[[0,-.45],[440,-.65],[580,-2.8],[710,-2.8],[830,-.08],[950,-.02],[1080,-.02],[1240,-.45]]);
    if(t>=runEnd) {
      const flight=unit((t-470)/330);
      x=curve(t,[[440,staging],[510,staging+18],[710,travel-85],[800,travel-85],[950,travel],[1080,travel+(missed?12:0)],[1240,travel]]);
      lift=-58*Math.sin(Math.PI*flight);
      hip=[-7+14*drive,curve(t,[[440,-82],[470,-76],[570,-84],[750,-84],[805,-76],[850,-82],[950,-76],[1240,-83]])];
      const fold=ease((t-470)/95),land=ease((t-725)/75);
      feet=feet.map((p,i)=>point(point([endFeet[i][0]-x,0],i===0?[-70,-30]:[57,-46],fold),[travel+(i===0?-55:45)-x,-lift],land));
      opacity=1-ease((t-525)/45)+ease((t-675)/65);
      blink=Math.sin(Math.PI*unit((t-510)/80))*.7+Math.sin(Math.PI*unit((t-665)/95));
    }
  } else {
    const flight=unit((t-640)/550);
    if(t>=runEnd) {
      x=curve(t,[[540,staging],[640,staging+12],[950,travel],[1090,travel+(missed?14:0)],[1240,travel]]);
      lift=-62*Math.sin(Math.PI*flight);
      hip=[-7,curve(t,[[540,-82],[630,-75],[780,-83],[950,-81],[1090,-83],[1190,-74],[1240,-83]])];
      tilt=curve(t,[[540,9],[650,10],[850,-15],[950,-22],[1100,-7],[1240,7]]);
      const chamber=ease((t-540)/100),extend=ease((t-850)/100),retract=ease((t-1030)/95);
      const kneeUp:Point=[29,-40],extended:Point=[79,-35];
      feet[1]=point(point([endFeet[1][0]-x,0],kneeUp,chamber),extended,extend);
      feet[1]=point(feet[1],kneeUp,retract);
      feet[0]=point([endFeet[0][0]-x,-lift],[-74,-34],ease((t-640)/120));
      const landing=ease((t-1120)/70);
      feet[0]=point(feet[0],[-28,-lift],landing);
      feet[1]=point(feet[1],[28,-lift],ease((t-1125)/85));
      rear=point(rear,[-92,-144],extend);
      front=point(front,[44,-160],extend);
    }
    angle=0;
  }
  // Recovery is a backward leap with a clear airborne arc and a short landing
  // compression. The torso stays upright instead of shuffling home in a squat.
  if(t>=1240) {
    const flight=unit((t-1270)/350),fold=ease((t-1270)/100),land=ease((t-1530)/90);
    const entry=ease((t-1240)/80);
    x=travel*(1-ease(flight));lift=-52*Math.sin(Math.PI*flight);
    feet=feet.map((p,i)=>point(point(p,i===0?[-76,-36]:[61,-24],fold),[i===0?-39:39,-lift],land));
    hip=point(hip,[-7,curve(t,[[1240,-83],[1270,-76],[1390,-84],[1560,-84],[1620,-74],[1730,-82]])],entry);
    tilt=mix(tilt,-8,entry)*(1-ease((t-1580)/150))+7*ease((t-1580)/150);
    front=point(front,[54,-144],entry);rear=point(rear,[-63,-122],entry);angle=mix(angle,kind==='kick'?0:-.55,entry);
    // Recover below the shoulder, not through the arm's IK anchor.
    if(kind==='sword') front[1]+=30*Math.sin(Math.PI*entry);
  }
  // The hip moves first; shoulder rotation and hand extension are delayed above.
  const neck:Point=[hip[0]+tilt,hip[1]-Math.sqrt(52*52-tilt*tilt)];
  const shoulders:[Point,Point]=[[neck[0]-10,neck[1]+6],[neck[0]+10,neck[1]+6]];
  if(kind==='spear') {
    const thrust=ease((t-830)/120)*(1-ease((t-(missed?1110:1080))/150));
    const returnGrip=ease((t-1240)/120),turn=ease((t-890)/60);
    const center:Point=[neck[0]+mix(mix(-6,48,thrust),8,returnGrip),neck[1]+mix(mix(44,24,turn),28,returnGrip)];
    front=[center[0]+34*Math.cos(angle),center[1]+34*Math.sin(angle)];
    rear=[center[0]-34*Math.cos(angle),center[1]-34*Math.sin(angle)];
  }
  const [backElbow,backHand]=twoBone(shoulders[0],rear,rigLengths.arm,-1);
  const [elbow,hand]=twoBone(shoulders[1],front,rigLengths.arm,1);
  const [backKnee,backFoot]=twoBone(hip,feet[0],48,-1);
  const [knee,foot]=twoBone(hip,feet[1],48,-1);
  const pose:RigPose={points:[[neck[0],neck[1]-21],neck,hip,backElbow,backHand,elbow,hand,backKnee,backFoot,knee,foot],sword:angle,lean:0,shoulders};
  return {x,lift,pose,opacity,blink};
}
