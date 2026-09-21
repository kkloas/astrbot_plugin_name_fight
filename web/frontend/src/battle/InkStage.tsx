import { useEffect, useRef } from 'react';
import { stateAt, statusLabels, type BattleEvent, type ReplayBattle, type Side } from './replay';
import { techniqueFor, weaponFor, type Weapon, type Technique } from './martialVisuals';
import { drawWeapon } from './inkWeapons';
import { drawAura, drawTrigger, drawFootwork } from './inkEffects';
import { drawTechnique, drawImpact, drawPreparation } from './inkStrikes';
import { contactTime, impactFor, plantedFoot } from './choreography';

type Point = [number, number];
type Pose = { points: Point[]; sword: number; lean: number };
// Head, neck, waist, rear elbow/hand, sword elbow/hand, rear knee/foot, front knee/foot.
const poses: Record<string, Pose> = {
  idle: { points: [[0,-137],[0,-116],[-7,-65],[-28,-95],[-19,-71],[24,-101],[39,-89],[-24,-34],[-39,0],[20,-34],[39,0]], sword: -.45, lean: 0 },
  gather: { points: [[-12,-129],[-10,-108],[-4,-59],[-34,-98],[-53,-113],[14,-102],[5,-128],[-28,-29],[-49,0],[24,-29],[50,0]], sword: -1.85, lean: -.06 },
  dash: { points: [[20,-119],[12,-99],[-10,-59],[-34,-85],[-61,-75],[31,-83],[51,-78],[-44,-21],[-70,-1],[27,-33],[51,0]], sword: -.2, lean: .06 },
  strike: { points: [[30,-114],[21,-94],[-11,-53],[-35,-76],[-65,-95],[49,-91],[79,-102],[-43,-26],[-75,0],[39,-41],[58,0]], sword: -.12, lean: 0 },
  hit: { points: [[-27,-126],[-21,-105],[1,-62],[-40,-85],[-48,-63],[4,-83],[24,-55],[-25,-29],[-39,0],[23,-32],[43,0]], sword: .8, lean: -.13 },
  dodge: { points: [[-37,-92],[-25,-77],[3,-45],[-46,-62],[-70,-70],[-3,-65],[24,-82],[-26,-20],[-50,0],[35,-24],[60,0]], sword: -.5, lean: -.12 },
  fallen: { points: [[-84,-17],[-63,-17],[-15,-14],[-54,-7],[-78,-2],[-33,-6],[-14,-2],[15,-5],[46,0],[16,-21],[49,0]], sword: .03, lean: 0 },
  salute: { points: [[0,-143],[0,-122],[0,-68],[-22,-106],[7,-100],[25,-103],[11,-100],[-15,-36],[-23,0],[13,-36],[22,0]], sword: 1.45, lean: 0 },
  slash: { points: [[22,-120],[16,-100],[-8,-57],[-35,-82],[-49,-57],[40,-74],[74,-69],[-42,-26],[-70,0],[32,-35],[55,0]], sword: .3, lean: .04 },
  rise: { points: [[15,-131],[10,-110],[-6,-62],[-31,-97],[-46,-72],[41,-129],[62,-153],[-39,-26],[-68,0],[28,-38],[45,0]], sword: -.85, lean: .05 },
  overhead: { points: [[-6,-131],[-6,-110],[-5,-60],[-18,-130],[2,-158],[15,-138],[11,-168],[-27,-29],[-43,0],[21,-32],[45,0]], sword: -2.4, lean: -.08 },
  low: { points: [[17,-92],[7,-74],[-16,-40],[-27,-67],[-54,-48],[39,-53],[74,-38],[-39,-18],[-66,0],[39,-18],[73,0]], sword: .02, lean: 0 },
  palmIdle: { points: [[-3,-137],[-2,-116],[-6,-65],[-17,-91],[5,-85],[23,-105],[39,-121],[-24,-34],[-39,0],[20,-34],[39,0]], sword: 0, lean: 0 },
  palm: { points: [[18,-121],[12,-102],[-8,-61],[-18,-85],[4,-92],[46,-95],[82,-100],[-33,-27],[-62,0],[24,-35],[49,0]], sword: 0, lean: .03 },
  kickGather: { points: [[-7,-139],[-6,-118],[-3,-66],[-32,-94],[-19,-72],[19,-96],[36,-119],[-21,-30],[-30,0],[32,-73],[29,-43]], sword: 0, lean: -.1 },
  kick: { points: [[-26,-138],[-21,-118],[-8,-70],[-42,-92],[-56,-106],[2,-107],[19,-126],[-24,-29],[-35,0],[50,-89],[105,-111]], sword: 0, lean: -.04 },
  lowKick: { points: [[-22,-92],[-12,-73],[-9,-39],[-31,-59],[-45,-29],[11,-65],[36,-76],[-31,-18],[-43,0],[43,-19],[106,-12]], sword: 0, lean: 0 },
  throwGather: { points: [[-6,-136],[-5,-115],[-4,-67],[-24,-96],[-13,-76],[-18,-117],[-35,-130],[-23,-34],[-39,0],[20,-34],[39,0]], sword: 0, lean: -.08 },
  throw: { points: [[12,-135],[8,-114],[-2,-66],[-19,-96],[-34,-82],[37,-106],[69,-104],[-28,-32],[-43,0],[20,-35],[40,0]], sword: -.1, lean: .04 },
  pluckIdle: { points: [[0,-140],[0,-119],[-3,-67],[-23,-96],[-29,-89],[23,-99],[34,-88],[-20,-34],[-36,0],[20,-34],[36,0]], sword: 0, lean: 0 },
  pluck: { points: [[4,-133],[4,-112],[-3,-67],[-21,-96],[-42,-83],[19,-91],[58,-81],[-20,-34],[-36,0],[20,-34],[36,0]], sword: 0, lean: .04 },
  pickup: { points: [[35,-75],[21,-59],[-11,-41],[-27,-27],[-29,-6],[42,-32],[48,-5],[-39,-22],[-50,0],[26,-24],[47,0]], sword: 0, lean: 0 },
  recoil: { points: [[-34,-109],[-23,-91],[4,-55],[-40,-78],[-57,-45],[0,-68],[28,-43],[-31,-24],[-50,0],[31,-24],[61,0]], sword: .95, lean: -.12 },
  bound: { points: [[9,-146],[4,-126],[-6,-77],[-30,-111],[-49,-123],[29,-115],[44,-134],[-35,-67],[-51,-40],[23,-52],[9,-25]], sword: -1.1, lean: .03 },
  reverse: { points: [[-9,-127],[-6,-108],[1,-62],[17,-93],[40,-102],[-35,-99],[-62,-122],[-27,-32],[-45,0],[30,-29],[51,0]], sword: -2.5, lean: -.02 },
  finish: { points: [[30,-103],[20,-85],[-6,-48],[-40,-76],[-58,-93],[49,-60],[78,-26],[-39,-25],[-74,0],[37,-25],[63,0]], sword: .78, lean: .03 },
  fan: { points: [[0,-137],[0,-115],[-4,-65],[-34,-111],[-65,-123],[38,-107],[70,-113],[-22,-32],[-42,0],[21,-34],[41,0]], sword: -.15, lean: 0 },
  strum: { points: [[12,-123],[8,-105],[-3,-64],[-29,-101],[-63,-113],[39,-84],[67,-65],[-27,-30],[-44,0],[24,-32],[46,0]], sword: 0, lean: .04 },
  victorySheath: { points: [[0,-146],[0,-124],[-1,-70],[-16,-88],[-1,-77],[18,-99],[5,-74],[-15,-36],[-25,0],[14,-36],[23,0]], sword: 2.95, lean: 0 },
  victoryRaise: { points: [[0,-146],[0,-124],[-1,-70],[-22,-104],[-29,-78],[28,-147],[32,-179],[-18,-35],[-30,0],[17,-37],[31,0]], sword: -1.45, lean: 0 },
  victoryBow: { points: [[24,-123],[16,-105],[-3,-64],[-13,-89],[13,-82],[32,-87],[17,-81],[-17,-32],[-29,0],[17,-34],[30,0]], sword: 1.5, lean: .02 },
  victoryRest: { points: [[-9,-138],[-6,-117],[0,-66],[-22,-90],[-11,-61],[16,-91],[28,-54],[-16,-32],[-28,0],[18,-32],[31,0]], sword: 1.12, lean: 0 },
  victoryKneel: { points: [[8,-109],[4,-89],[-10,-44],[-20,-73],[-9,-43],[23,-67],[35,-30],[-27,-19],[-41,-1],[31,-36],[51,0]], sword: 1.35, lean: .02 },
  victoryWipe: { points: [[0,-141],[0,-119],[-3,-68],[-20,-109],[10,-146],[20,-92],[33,-61],[-18,-34],[-29,0],[15,-34],[28,0]], sword: .95, lean: 0 },
  victoryBack: { points: [[-3,-145],[-2,-123],[0,-69],[-23,-94],[-15,-69],[-15,-94],[-24,-65],[-17,-33],[-28,0],[16,-35],[28,0]], sword: 1.1, lean: -.02 },
};

const clamp = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (x: number) => { const v = clamp(x); return v * v * (3 - 2 * v); };
function blend(a: Pose, b: Pose, t: number): Pose {
  const f = clamp(t);
  return { points: a.points.map((p, i) => [p[0] + (b.points[i][0] - p[0]) * f, p[1] + (b.points[i][1] - p[1]) * f]),
    sword: a.sword + (b.sword - a.sword) * f, lean: a.lean + (b.lean - a.lean) * f };
}

function stepping(pose: Pose, progress: number, distance: number, backwards=false): Pose {
  const result={...pose,points:pose.points.map(p=>[...p] as Point),lean:0};
  const sign=backwards?-1:1;
  const bob=Math.abs(Math.sin(progress*Math.PI*3))*4;
  for(let i=0;i<=6;i++) result.points[i][1]-=bob;
  for(const [knee,foot,offset] of [[7,8,0],[9,10,.5]]) {
    const [x,y]=plantedFoot(progress,0,distance,offset);
    const footX=sign*x+(offset===0?-20:20);
    result.points[foot]=[footX,y];
    const hip=result.points[2];
    const dx=footX-hip[0],dy=y-hip[1];
    const length=Math.max(1,Math.hypot(dx,dy));
    const bend=Math.sqrt(Math.max(0,48*48-length*length/4));
    result.points[knee]=[(hip[0]+footX)/2+dy/length*bend,(hip[1]+y)/2-dx/length*bend];
  }
  return result;
}

function sequence(entries: [number,Pose][], time: number): Pose {
  for(let i=1;i<entries.length;i++) if(time<entries[i][0]) {
    return blend(entries[i-1][1],entries[i][1],smooth((time-entries[i-1][0])/(entries[i][0]-entries[i-1][0])));
  }
  return entries[entries.length-1][1];
}

function stroke(ctx: CanvasRenderingContext2D, points: Point[], width: number, color: string) {
  ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = width;
  ctx.moveTo(...points[0]); points.slice(1).forEach(p => ctx.lineTo(...p)); ctx.stroke();
}

function fighter(ctx: CanvasRenderingContext2D, x: number, side: Side, pose: Pose, time: number, weapon: Weapon, alpha = 1, lift = 0, sheathed = false) {
  const dir = side === 'a' ? 1 : -1;
  const ink = side === 'a' ? '#222521' : '#515953';
  const p = pose.points;
  ctx.save(); ctx.globalAlpha *= alpha;
  ctx.translate(x, 324+lift); ctx.scale(dir, 1); ctx.rotate(pose.lean);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  // Rear limbs stay narrow. A tapered torso and sash give the simple figure weight.
  stroke(ctx, [p[1],p[3],p[4]], 7, ink);
  stroke(ctx, [p[2],p[7],p[8]], 10, ink);
  stroke(ctx, [p[2],p[9],p[10]], 12, ink);
  stroke(ctx, [[p[8][0]-6,p[8][1]],[p[8][0]+10,p[8][1]]], 6, ink);
  stroke(ctx, [[p[10][0]-5,p[10][1]],[p[10][0]+14,p[10][1]]], 6, ink);
  ctx.fillStyle = ink; ctx.beginPath();
  ctx.moveTo(p[1][0]-8,p[1][1]-1); ctx.lineTo(p[1][0]+10,p[1][1]+2);
  ctx.lineTo(p[2][0]+12,p[2][1]+10); ctx.lineTo(p[2][0]+26,p[2][1]+28);
  ctx.lineTo(p[2][0]-6,p[2][1]+15); ctx.lineTo(p[2][0]-29,p[2][1]+30);
  ctx.lineTo(p[2][0]-10,p[2][1]-2); ctx.closePath(); ctx.fill();
  stroke(ctx, [p[1],p[5],p[6]], 9, ink);
  ctx.beginPath(); ctx.ellipse(p[0][0],p[0][1],11,15,.08,0,Math.PI*2); ctx.fill();
  // A short headband and trailing sash, no face or portrait-specific features.
  const flutter = Math.sin(time / 190) * 5;
  const accent = side === 'a' ? '#87372d' : '#c0b99f';
  stroke(ctx, [[p[0][0]-10,p[0][1]-4],[p[0][0]+9,p[0][1]-4]],3,accent);
  stroke(ctx, [[p[0][0]-9,p[0][1]-3],[p[0][0]-30,p[0][1]-7+flutter],[p[0][0]-46,p[0][1]+flutter]],2.5,accent);
  stroke(ctx, [[p[2][0]-10,p[2][1]],[p[2][0]+10,p[2][1]-1]],4,accent);
  stroke(ctx, [[p[2][0]-9,p[2][1]], [p[2][0]-35,p[2][1]+5+flutter], [p[2][0]-52,p[2][1]+17+flutter]],4,accent);
  if(sheathed) {
    stroke(ctx,[[p[2][0]-70,p[2][1]+12],[p[2][0]+14,p[2][1]-4]],6,ink);
  } else {
    const hand: Point = weapon==='zither'?[5,-83]:p[6];
    ctx.translate(...hand); ctx.rotate(weapon==='zither'?0:pose.sword);
    drawWeapon(ctx,weapon,ink,time);
  }
  ctx.restore();
}

function motionPoses(technique: Technique, weapon: Weapon, type?: string) {
  const idle=weapon==='zither'?poses.pluckIdle:weapon==='unarmed'?poses.palmIdle:poses.idle;
  let gather=poses.gather;
  let strike=poses.strike;
  switch(technique.motion) {
    case 'slash': case 'flurry': strike=poses.slash;break;
    case 'rise': gather=poses.low;strike=poses.rise;break;
    case 'cleave': gather=poses.overhead;strike=weapon==='unarmed'?poses.palm:poses.finish;break;
    case 'sweep': gather=poses.gather;strike=type==='leg'?poses.lowKick:poses.low;break;
    case 'leap': gather=poses.low;strike=poses.slash;break;
    case 'draw': gather=poses.low;strike=poses.strike;break;
    case 'palm': gather=poses.palmIdle;strike=poses.palm;break;
    case 'kick': gather=poses.kickGather;strike=poses.kick;break;
    case 'throw': gather=poses.throwGather;strike=poses.throw;break;
    case 'pluck': gather=poses.pluckIdle;strike=poses.pluck;break;
  }
  if(technique.pattern==='fan' || technique.pattern==='rain') gather=poses.fan;
  if(technique.pattern==='crescendo') {gather=poses.fan;strike=poses.strum;}
  if(weapon==='spear') {
    // The rear hand holds the same shaft as the leading hand.
    strike={...strike,points:strike.points.map(p=>[...p] as Point)};
    strike.points[4]=[strike.points[6][0]-65*Math.cos(strike.sword),strike.points[6][1]-65*Math.sin(strike.sword)];
  }
  if(weapon==='katana' && technique.motion==='draw') {
    gather={...poses.low,points:poses.low.points.map(p=>[...p] as Point)};
    gather.points[5]=[15,-65];gather.points[6]=[3,-42];
    strike=poses.slash;
  }
  return {idle,gather,strike};
}

function poseAt(battle: ReplayBattle, side: Side, time: number, width: number, turn?: BattleEvent) {
  const dir = side === 'a' ? 1 : -1;
  const actor=side==='a'?battle.attacker:battle.defender;
  const weapon=weaponFor(actor);
  const home = width * (side === 'a' ? .235 : .765);
  const ranged=weapon==='needles'||weapon==='zither';
  const reach=weapon==='spear'?210:weapon==='brush'?113:weapon==='unarmed'?94:165;
  const travel = ranged?0:width * .53 - reach;
  let x = home;
  let lift=0;
  const state=stateAt(battle,time);
  const hp = state.hp[side];
  const victory=battle.events.find(e=>e.type==='victory_start' && e.time<=time);
  let victorySheathed=false;
  const local = turn ? time - turn.time : -1;
  const events = turn ? battle.events.filter(e => e.action === turn.action) : [];
  const attack = events.find(e => e.type === 'attack');
  const technique=techniqueFor(attack,actor);
  const motion=motionPoses(technique,weapon,actor.martialArt.type);
  let pose = blend(motion.idle, motion.gather, .05 + Math.sin(time/530)*.025);
  const outcome = events.find(e => e.type === 'dodge' || (e.type === 'damage' && e.cause === 'strike'));
  const victim=turn?.actor==='a'?battle.defender:battle.attacker;
  const impact=impactFor(outcome,victim.stats.hp,technique);
  const contact=outcome && turn?outcome.time-turn.time:950;
  const actionTime=contactTime(local,contact,impact.hold);
  if (turn && attack && local >= 0 && local < 1740) {
    if (turn.actor === side) {
      const t=actionTime;
      const stepProgress=clamp((t-380)/460);
      const p=actor.qinggong?.id==='lightning_flash'?smooth(stepProgress**1.5):
        actor.qinggong?.id==='shadow_drift'?smooth(stepProgress):stepProgress;
      const aerial=technique.motion==='leap'||technique.motion==='kick';
      const draw=technique.motion==='draw';
      const advance=draw?smooth((t-745)/205):p*.76+smooth((t-840)/110)*.24;
      x+=dir*travel*advance;
      pose=sequence([[0,motion.idle],[240,blend(motion.idle,motion.gather,.4)],[420,motion.gather],
        [790,motion.gather],[950,motion.strike],[1040,motion.strike],[1190,blend(motion.strike,motion.idle,.32)]],t);
      if(!ranged && !draw && t>380 && t<840) {
        if(aerial) {
          pose=sequence([[380,motion.gather],[570,poses.bound],[780,motion.gather],[950,motion.strike]],t);
          lift=-70*Math.sin(Math.PI*clamp((t-380)/610));
        } else {
          const gait=stepping(blend(poses.dash,motion.gather,p*.65),p,travel*.76);
          pose=blend(motion.gather,gait,smooth((t-380)/60)*(1-smooth((t-780)/60)));
        }
      }
      if(aerial && t>=840 && t<990) lift=-70*Math.sin(Math.PI*clamp((t-380)/610));
      if(technique.motion==='flurry' && t>=770 && t<1190) {
        const cut=technique.pattern==='fall'?poses.overhead:poses.reverse;
        pose=sequence([[770,cut],[840,poses.slash],[890,poses.rise],[950,motion.strike],[1060,cut],[1140,poses.finish],[1190,motion.strike]],t);
      }
      if(technique.pattern==='wheel' && t>700 && t<950) {
        pose=sequence([[700,motion.gather],[805,poses.reverse],[870,poses.overhead],[950,motion.strike]],t);
      }
      if(technique.motion==='pluck' && t>600 && t<1160) {
        pose=sequence([[600,motion.gather],[720,poses.pluck],[805,motion.gather],[950,motion.strike],[1060,poses.strum],[1160,motion.strike]],t);
      }
      if(technique.motion==='throw' && technique.pattern==='rain' && t>630 && t<1100) {
        pose=sequence([[630,poses.fan],[780,poses.overhead],[950,poses.throw],[1100,poses.fan]],t);
      }
      if(technique.feint) {
        if(t<745) {x-=dir*38*Math.sin(Math.PI*clamp(t/745));pose=sequence([[0,motion.idle],[300,poses.reverse],[620,poses.low],[745,motion.gather]],t);}
        else if(t<950) pose=blend(poses.reverse,motion.strike,smooth((t-745)/205));
      }
      if(t>=1190) {
        const retreat=smooth((t-1190)/490);
        x=home+dir*travel*(1-retreat);
        if((weapon==='spear'||weapon==='brush') && travel>0) {
          pose=stepping(blend(motion.strike,motion.idle,retreat),retreat,travel,true);
          pose=blend(pose,motion.idle,smooth((t-1570)/110));
        } else if(!ranged && travel>0) {
          // Backward bound: fold the legs in flight, then absorb the landing.
          lift=-46*Math.sin(Math.PI*retreat);
          pose=sequence([[1190,motion.strike],[1290,poses.bound],[1500,poses.low],[1630,motion.idle]],t);
        } else pose=blend(motion.strike,motion.idle,retreat);
      }
    } else if (outcome) {
      const age=time-outcome.time;
      if (outcome.type === 'dodge' && age > -120 && age < 630) {
        const f=age<80?smooth((age+120)/200):1-smooth((age-130)/500);
        const footwork=actor.qinggong?.id;
        const avoid=footwork==='earth_root'?poses.low:footwork==='swan_shadow'||footwork==='phantom_lotus'?poses.bound:
          footwork==='lightning_flash'?poses.dash:poses.dodge;
        pose=blend(motion.idle,avoid,f); x-=dir*(footwork==='earth_root'?22:footwork==='lightning_flash'?80:62)*f;
        if(footwork==='swan_shadow') lift=-48*f;
        if(footwork==='phantom_lotus') lift=-32*f;
      } else if (outcome.type === 'damage' && age>=0 && age<720) {
        const held=contactTime(age,35,impact.hold);
        const f=held<85?smooth(held/85):1-smooth((held-170)/480);
        const reaction=outcome.bodyPartKey==='leg'?poses.low:outcome.bodyPartKey==='abdomen'?poses.recoil:poses.hit;
        pose=blend(motion.idle,reaction,f); x-=dir*(16+impact.force*52)*f;
        if(impact.heavy) lift=-12*Math.sin(Math.PI*clamp(held/380));
        if(held>200 && impact.heavy) pose=blend(pose,stepping(motion.idle,clamp((held-200)/430),32,true),.35*(1-f));
      }
    }
  }
  const skip=turn?battle.events.find(e=>e.type==='turn_skip' && e.action===turn.action && e.actor===side && e.time<=time):undefined;
  const skipAge=skip?time-skip.time:-1;
  if(skip && skipAge>=0 && skipAge<1520 && hp>0) {
    pose=blend(motion.idle,skip.reason==='disarmed'?poses.pickup:poses.hit,Math.sin(Math.PI*clamp(skipAge/1520))*.85);
  }
  if (hp <= 0) {
    const death = battle.events.filter(e => e.target===side && e.hpAfter===0 && e.time<=time).pop();
    pose = blend(poses.hit,poses.fallen,smooth((time-(death?.time||time))/560));
    const deathTurn = battle.events.find(e => e.type==='turn_start' && e.action===death?.action);
    const deathAttack = battle.events.find(e => e.type==='attack' && e.action===death?.action);
    const deathLocal = death && deathTurn ? death.time-deathTurn.time : 0;
    x=home;
    if(deathTurn?.actor===side && deathAttack && deathLocal>=550) {
      x+=dir*travel*(deathLocal<950?smooth((deathLocal-550)/370):deathLocal<1100?1:1-smooth((deathLocal-1100)/550));
    }
    if(death?.cause==='strike') x-=dir*(18+impact.force*40)*smooth((time-death.time)/240);
  } else if(victory) {
    const variant=(victory.victoryVariant || 0)%3;
    const kind=victory.victoryKind || 'standard';
    const won=victory.actor===side;
    const options:Record<string,Pose[]>={
      quick:[poses.victorySheath,poses.victoryBack,poses.victoryRest],
      dominant:[poses.victoryRaise,poses.victoryBack,poses.salute],
      standard:[poses.salute,poses.victoryBow,poses.victoryWipe],
      clutch:[poses.victoryKneel,poses.victoryRest,poses.victoryWipe],
      judged:[poses.victoryBow,poses.victoryWipe,poses.salute],
      draw:[poses.salute,poses.victoryBow,motion.idle],
    };
    let finish=won||kind==='draw'?options[kind][variant]:poses.victoryRest;
    if(weapon==='zither') finish=variant===0?poses.pluckIdle:variant===1?poses.victoryBow:poses.victoryRest;
    const age=time-victory.time;
    const preparation=kind==='clutch'?poses.recoil:kind==='quick' && variant===2?poses.slash:motion.gather;
    pose=sequence([[0,motion.idle],[260,preparation],[950,finish],[1800,finish]],age);
    x=home;lift=0;
    if(kind==='clutch' && won && age>950) pose=blend(finish,poses.victoryRest,.06+.04*Math.sin(age/190));
    const length=({sword:99,katana:112,blade:107,spear:140,brush:45} as Partial<Record<Weapon,number>>)[weapon];
    if(length && pose.sword>0 && pose.sword<Math.PI/2) {
      pose={...pose,sword:Math.min(pose.sword,Math.asin(clamp((-pose.points[6][1]-5)/length)))};
    }
    victorySheathed=won && kind==='quick' && variant===0 && age>740 && ['sword','katana','blade'].includes(weapon);
  } else if (time >= (battle.events[battle.events.length-1]?.time||Infinity)) {
    pose=weapon==='zither'?poses.pluckIdle:poses.salute; x=home;
  }
  const sheathed=victorySheathed || (weapon==='katana' && technique.motion==='draw' && attack?.actor===side && local>=0 && local<830);
  return { x, pose, lift, weapon:state.weaponsReady[side]?weapon:'unarmed' as Weapon, technique, armed:state.weaponsReady[side], sheathed };
}

function draw(ctx: CanvasRenderingContext2D, battle: ReplayBattle, time: number, width: number, reducedMotion: boolean) {
  ctx.clearRect(0,0,width,430);
  const state=stateAt(battle,time);
  const frames={a:poseAt(battle,'a',time,width,state.turn),b:poseAt(battle,'b',time,width,state.turn)};
  const turn=state.turn;
  const attack=turn && battle.events.find(e=>e.action===turn.action && e.type==='attack');
  const striker=attack?.actor==='a'?battle.attacker:battle.defender;
  const technique=techniqueFor(attack,striker);
  const outcome=attack && battle.events.find(e=>e.action===attack.action && (e.cause==='strike'||e.type==='dodge'));
  const victim=attack?.actor==='a'?battle.defender:battle.attacker;
  const force=impactFor(outcome,victim.stats.hp,technique);
  const impactAge=outcome?time-outcome.time:-1;
  ctx.save();
  if(force.cinematic && impactAge>-160 && impactAge<480) {
    const focus=impactAge<0?smooth((impactAge+160)/160):1-smooth((impactAge-80)/400);
    ctx.fillStyle=`rgba(32,39,35,${focus*.17})`;ctx.fillRect(0,0,width,430);
    if(!reducedMotion) {
      const zoom=1+focus*.035;
      ctx.translate(width/2,255);ctx.scale(zoom,zoom);ctx.translate(-width/2,-255);
    }
  }
  if(!reducedMotion && force.heavy && impactAge>=0 && impactAge<220) {
    const shake=(1-impactAge/220)*force.force*5;
    ctx.translate(Math.sin(impactAge*.09)*shake,Math.cos(impactAge*.13)*shake*.4);
  }
  ctx.lineCap='round';
  stroke(ctx,[[width*.065,329],[width*.4,329],[width*.72,330],[width*.94,329]],1,'rgba(44,49,40,.25)');
  stroke(ctx,[[width*.159,333],[width*.396,333]],.6,'rgba(44,49,40,.15)');
  for(const side of ['a','b'] as Side[]) {
    const frame=frames[side];
    const actor=side==='a'?battle.attacker:battle.defender;
    const {x,pose,weapon,lift}=frame;
    const dir=side==='a'?1:-1;
    ctx.fillStyle='rgba(30,35,29,.13)';ctx.beginPath();ctx.ellipse(x,330,52+lift*.3,6,0,0,Math.PI*2);ctx.fill();
    if(state.hp[side]>0) drawAura(ctx,x,324+lift,state.states[side],time);
    const local=turn?time-turn.time:-1;
    if(attack?.actor===side) drawPreparation(ctx,technique,x,dir,local,['needles','zither'].includes(weapon));
    const dodging=battle.events.find(e=>e.type==='dodge' && e.target===side && time>=e.time-100 && time<e.time+550);
    const moving=attack?.actor===side && ((local>430 && local<960)||(local>1210 && local<1660)) && !['needles','zither'].includes(weapon);
    if(moving || dodging) {
      const qinggong=actor.qinggong?.id;
      const shadows=qinggong==='earth_root'?0:qinggong==='shadow_drift'||qinggong==='shadow_fragrance'?4:2;
      for(let i=shadows;i>0;i--) {
        const past=poseAt(battle,side,Math.max(0,time-i*35),width,turn);
        fighter(ctx,past.x,side,past.pose,time-i*35,past.weapon,.18/i,past.lift,past.sheathed);
      }
      const trace=Array.from({length:4},(_,i)=>{
        const past=poseAt(battle,side,Math.max(turn?.time || 0,time-i*60),width,turn);
        return {x:past.x,y:324+past.lift};
      });
      drawFootwork(ctx,qinggong,x,dir,.85,time,trace);
    }
    fighter(ctx,x,side,pose,time,weapon,1,lift,frame.sheathed);
    if(!frame.armed && weaponFor(actor)!=='unarmed') {
      const disarm=battle.events.filter(e=>e.type==='status_apply' && e.status==='disarmed' && e.target===side && e.time<=time).pop();
      const age=time-(disarm?.time||0);
      const f=clamp(age/430);
      ctx.save();ctx.translate(x-dir*(30+f*14),230+94*f-40*Math.sin(f*Math.PI));
      ctx.scale(dir,1);ctx.rotate(f*3.2);
      drawWeapon(ctx,weaponFor(actor),'#52574c',time);ctx.restore();
    }
  }
  if(attack?.actor) {
    const side=attack.actor;
    const actor=side==='a'?battle.attacker:battle.defender;
    const dir=side==='a'?1:-1;
    const frame=frames[side];
    const outcome=battle.events.find(e=>e.action===attack.action && (e.cause==='strike'||e.type==='dodge'));
    const heights:Record<string,number>={head:190,chest:230,abdomen:259,arm:240,leg:291};
    const y=heights[outcome?.bodyPartKey||'chest']||230;
    const targetSide=side==='a'?'b':'a';
    // A missed attack passes through the original position instead of tracking
    // the dodging fighter and looking like a successful hit.
    const targetX=outcome?.type==='dodge'?width*(side==='a'?.765:.235):frames[targetSide].x;
    const age=contactTime(time-attack.time,(outcome?.time || attack.time+400)-attack.time,force.hold);
    const emission=outcome && time>outcome.time?poseAt(battle,side,outcome.time,width,turn):frame;
    drawTechnique(ctx,techniqueFor(attack,actor),weaponFor(actor),
      [emission.x+dir*60,236+emission.lift],[targetX,y],dir,age,force.force);
    drawImpact(ctx,targetX,y,dir,impactAge,force,attack.action||0);
  }
  for(const event of battle.events) {
    const age=time-event.time;
    if(age<0 || age>1150) continue;
    const side=event.target || event.actor;
    if(!side) continue;
    const eventTurn=battle.events.find(e=>e.type==='turn_start' && e.action===event.action);
    const x=poseAt(battle,side,event.time,width,eventTurn).x;
    const otherSide=event.fromSide || (event.actor!==side?event.actor:side==='a'?'b':'a');
    const otherX=otherSide?poseAt(battle,otherSide,event.time,width,eventTurn).x:x;
    // Reflection originates at the defender, while the HP event targets the attacker.
    const liveX=frames[side].x;
    const liveOtherX=otherSide?frames[otherSide].x:otherX;
    drawTrigger(ctx,event,event.cause==='thorns'?liveOtherX:liveX,event.cause==='thorns'?liveX:liveOtherX,age);
    if(age>850) continue;
    if(!['damage','heal','dodge','status_apply','turn_skip'].includes(event.type)) continue;
    if(event.type==='turn_skip' && event.reason==='fallen') continue;
    const phase=age/850;
    ctx.save();ctx.globalAlpha=Math.min(1,(850-age)/200);
    if(event.type==='damage' && event.cause!=='strike' && age<360) {
      ctx.fillStyle=event.crit?'#863b2d':'#353c32';
      for(let i=0;i<9;i++) {
        const angle=i*2.399+(event.action||0);
        const r=(13+(age/360)*57)*(i%3+1)/3;
        ctx.beginPath();ctx.ellipse(x+Math.cos(angle)*r,230+Math.sin(angle)*r,1.5+i%3,1+i%2,angle,0,Math.PI*2);ctx.fill();
      }
    }
    const text=event.type==='damage'?`${event.crit?'暴击 ':event.cause==='thorns'?'反震 ':event.cause==='bleeding'?'流血 ':event.cause==='poisoned'?'毒伤 ':''}-${event.amount}`:
      event.type==='heal'?`+${event.amount}`:event.type==='dodge'?'闪':
      event.type==='turn_skip'?(event.reason==='disarmed'?(weaponFor(side==='a'?battle.attacker:battle.defender)==='unarmed'?'重整架势':'拾回兵刃'):'气机受阻'):
      statusLabels[event.status||'']||'运功';
    const lane=battle.events.filter(e=>e.action===event.action && e.type===event.type && e.target===event.target && e.time<event.time).length;
    const labelY=event.type==='status_apply'||event.type==='turn_skip'?353+Math.min(lane,1)*21:145-(event.type==='heal'?25:0)-Math.min(lane,1)*23;
    const major=event===outcome && force.heavy;
    ctx.font=`${major?'bold 34':event.crit?'bold 29':'24'}px "STKaiti", "KaiTi", serif`;
    ctx.textAlign='center';ctx.fillStyle=event.type==='heal'?'#405b45':event.type==='damage'?'#892f27':'#353b32';
    ctx.strokeStyle='rgba(250,249,237,.88)';ctx.lineWidth=3;
    ctx.strokeText(text,x,labelY-phase*22);ctx.fillText(text,x,labelY-phase*22);ctx.restore();
  }
  ctx.restore();
}

export function InkStage({ battle, time }: { battle: ReplayBattle; time: number }) {
  const canvas=useRef<HTMLCanvasElement>(null);
  const latest=useRef({battle,time}); latest.current={battle,time};
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
    if(ctx) {ctx.setTransform(w/logicalWidth,0,0,h/430,0,0);draw(ctx,latest.current.battle,latest.current.time,logicalWidth,window.matchMedia('(prefers-reduced-motion: reduce)').matches);}
  };
  useEffect(paint,[battle,time]);
  useEffect(()=>{
    const observer=new ResizeObserver(paint);
    if(canvas.current) observer.observe(canvas.current);
    return ()=>observer.disconnect();
  },[]);
  return <canvas ref={canvas} className="ink-duel-canvas" role="img" aria-label="水墨武学交手动画"
    data-weapon-a={weaponFor(battle.attacker)} data-weapon-b={weaponFor(battle.defender)} />;
}
