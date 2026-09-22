import { twoBone, rigLengths, type RigPose } from './sampleMotion';

type Point=[number,number];
const direction=(a:Point,b:Point,length:number):Point=>{
  const dx=b[0]-a[0],dy=b[1]-a[1],d=Math.hypot(dx,dy)||1;
  return [a[0]+dx/d*length,a[1]+dy/d*length];
};

// Resolve the final interpolated pose, not just individual attack keyframes.
// Hand/foot targets stay in place; the elbow/knee bends instead of stretching.
export function constrainRig(source:RigPose):RigPose {
  const p=source.points.map(v=>[...v] as Point);
  p[1]=direction(p[2],p[1],rigLengths.torso);
  p[0]=direction(p[1],p[0],21);
  const shoulders:[Point,Point]=[[p[1][0]-10,p[1][1]+6],[p[1][0]+10,p[1][1]+6]];
  for(const [root,joint,end,length,fallback] of [
    [shoulders[0],3,4,40,-1],[shoulders[1],5,6,40,1],
    [p[2],7,8,48,-1],[p[2],9,10,48,-1],
  ] as [Point,number,number,number,number][]) {
    // Fixed bend sides avoid elbow flips when interpolated legacy joints cross
    // the root-to-hand line on the way into the canonical rig.
    [p[joint],p[end]]=twoBone(root,p[end],length,fallback);
  }
  return {...source,points:p,shoulders};
}
