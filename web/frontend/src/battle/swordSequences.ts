import { ease } from './choreography';
import { twoBone, sampleMotion, type RigPose } from './sampleMotion';
import type { BattleEvent } from './replay';

// Root progress, height, pelvis height, torso lean, front/rear arm angles,
// extension and blade angle. Whole-body scores, not variations of one thrust.
type Key=[number,number,number,number,number,number,number,number,number];
const guard:Key=[0,0,0,78,0,.4,2.6,58,-.55];
const end:Key=[1740,0,0,78,0,.4,2.6,58,-.55];
const scores:Record<string,Key[]>={
  '有凤来仪':[
    guard,[330,.08,0,73,-8,-1.7,2.7,55,-2.1],
    [560,.32,-65,76,-10,-.7,2.9,64,-.4],
    [730,.65,-100,79,14,-.45,3.6,67,-.15],
    [950,1,-55,74,20,.5,3.2,76,.59],
    [1080,1,0,58,18,.7,2.6,69,.6],
    [1200,1,0,76,4,.4,2.7,58,-.2],
    [1450,.48,-42,80,-9,-.6,3.4,60,-1.1],end,
  ],
  '天绅倒悬':[
    guard,[400,.32,0,73,-10,.8,2.8,55,.55],
    [680,.7,0,45,-16,1.15,3.5,62,.5],
    [820,.83,0,49,-4,.94,3.3,65,-.2],
    [950,1,0,53,13,.65,3.6,77,-.58],
    [1080,1,-22,83,12,-.9,2.6,75,-1.03],
    [1200,.96,0,80,3,-.5,2.7,61,-.7],
    [1460,.4,-37,80,-8,-.5,3,59,-.8],end,
  ],
  '无边落木':[
    guard,[390,.4,0,77,-8,-1.3,2.8,54,-1.65],
    [550,.69,0,77,16,-.24,3.3,77,-.34],
    [645,.67,0,72,-9,.9,2.8,40,-.4],
    [735,.84,-8,77,17,.12,3.4,77,.08],
    [835,.83,0,66,-8,1.1,2.7,42,.12],
    [950,1,0,68,22,.47,3.5,78,.28],
    [1070,1,0,68,22,.47,3.5,78,.28],
    [1210,.94,0,78,0,-.45,2.8,57,-.6],
    [1460,.42,-40,81,-9,-.6,3.1,60,-.9],end,
  ],
  '金雁横空':[
    guard,[360,.12,0,65,-12,2.5,3.7,63,-2.8],
    [590,.43,-64,76,-8,2.9,3.8,72,-2.9],
    [790,.7,-81,81,14,.9,3,77,-.15],
    [950,1,-47,76,22,.9,3.2,78,0],
    [1070,1.04,-15,76,12,1.05,2.5,70,1.1],
    [1200,1,0,70,0,.6,2.6,55,-.3],
    [1460,.43,-38,80,-9,-.5,3.2,61,-.9],end,
  ],
  '回风斩':[
    guard,[370,.26,0,77,-14,2.4,3.6,68,-2.8],
    [620,.72,0,76,20,-.6,2.7,78,-.8],
    [740,.77,0,72,3,1.3,2.8,69,.9],
    [830,.82,0,73,-14,2.65,3.9,71,2.9],
    [950,1,0,76,22,6.4,3.2,78,6.48],
    [1080,1,0,73,17,7.2,2.7,73,7.1],
    [1210,.94,0,78,0,6.68,2.6,58,5.73],
    [1460,.42,-40,80,-9,5.9,3.3,60,5.4],
    [1740,0,0,78,0,6.68,2.6,58,5.73],
  ],
  '青山隐隐':[
    guard,[400,0,0,77,-10,1.9,2.3,43,-2.4],
    [730,.04,0,75,-12,1.7,2.4,44,-2.6],
    [820,.1,-12,78,-9,1.45,2.8,47,-1.7],
    [950,1,0,77,21,.12,3.3,78,-.03],
    [1090,1,0,77,21,.12,3.3,78,-.03],
    [1210,.93,0,78,-2,.6,2.6,57,-.5],
    [1460,.42,-40,80,-9,-.55,3.2,60,-.9],end,
  ],
};
export function swordSequenceFor(event?:BattleEvent) {
  if(event?.martialArtId==='sword_huashan' || event?.martialArtId==='sword_falling_plum' && event.move==='回风斩') return scores[event.move || ''];
}
export function swordSequence(event:BattleEvent,t:number,travel:number,missed=false) {
  const keys=swordSequenceFor(event);
  if(!keys) return undefined;
  let k=keys[keys.length-1];
  for(let i=1;i<keys.length;i++) if(t<keys[i][0]) {
    const a=keys[i-1],b=keys[i],f=ease((t-a[0])/(b[0]-a[0]));
    k=a.map((v,j)=>v+(b[j]-v)*f) as Key;break;
  }
  const [,progress,lift,height,tilt,frontAngle,rearAngle,extension,angle]=k;
  const hip:[number,number]=[0,-height],neck:[number,number]=[tilt,-height-Math.sqrt(52*52-tilt*tilt)];
  const shoulders:[[number,number],[number,number]]=[[neck[0]-10,neck[1]+6],[neck[0]+10,neck[1]+6]];
  const target=(root:[number,number],a:number,r:number):[number,number]=>[root[0]+Math.cos(a)*r,root[1]+Math.sin(a)*r];
  const [elbow,hand]=twoBone(shoulders[1],target(shoulders[1],frontAngle,extension),40,1);
  const [backElbow,backHand]=twoBone(shoulders[0],target(shoulders[0],rearAngle,64),40,-1);
  const base=sampleMotion('sword',t,travel,missed);
  const stance=ease((t-330)/170)*(1-ease((t-1230)/160));
  const airborne=ease(-lift/35);
  const feet=base.pose.points;
  const footTarget=(index:number,groundX:number,airX:number,airY:number):[number,number]=>[
    feet[index][0]*(1-stance)+(groundX*(1-airborne)+airX*airborne)*stance,
    feet[index][1]*(1-stance)+airY*airborne*stance,
  ];
  const [backKnee,backFoot]=twoBone(hip,footTarget(8,-55,-63,-35),48,-1);
  const [knee,foot]=twoBone(hip,footTarget(10,43,55,-39),48,-1);
  const correction=Math.sin(angle)>0?Math.asin(Math.sin(angle))-Math.asin(Math.min(Math.sin(angle),Math.max(0,(-hand[1]-lift-5)/99))):0;
  const sword=angle+(Math.cos(angle)<0?correction:-correction);
  const pose:RigPose={points:[[neck[0],neck[1]-21],neck,hip,backElbow,backHand,elbow,hand,backKnee,backFoot,knee,foot],shoulders,sword,lean:0};
  return {pose,x:Math.max(0,travel-20)*progress,lift,opacity:1,blink:0};
}
