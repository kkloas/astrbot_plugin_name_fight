import assert from 'node:assert/strict';
import { draw, poseAt } from './web_animation/battle/InkStage.js';
import { names, holyTime, holyReplayTime, holySample, holyEffects } from './web_animation/battle/holyMotion.js';
function context(){const calls=[];const ctx=new Proxy({globalAlpha:1},{get(o,k){if(k in o)return o[k];return (...args)=>{assert.ok(args.every(v=>typeof v!=='number'||Number.isFinite(v)),String(k));calls.push([k,...args]);if(k==='measureText')return {width:30};if(k==='createRadialGradient'||k==='createLinearGradient')return {addColorStop(){}};};}});return {ctx,calls};}
for(const contact of [750,950,1050])for(const local of [0,400,950,1250])assert.ok(Math.abs(holyTime(holyReplayTime(local,contact),contact)-local)<1e-8);
let frames=0;const signatures=new Set();
for(const move of names)for(const side of ['a','b'])for(const miss of [false,true]){
 const target=side==='a'?'b':'a';
 const actor={name:'Holy',stats:{hp:1000,spd:60},martialArt:{id:'short_shenghuoling',type:'short_weapon'}};
 const enemy={name:'Sword',stats:{hp:1000,spd:60},martialArt:{id:'sword_huashan',type:'sword'}};
 const turn={type:'turn_start',time:300,actor:side,action:1};
 const attack={type:'attack',time:850,action:1,actor:side,target,martialArtId:'short_shenghuoling',move};
 const battle={attacker:side==='a'?actor:enemy,defender:side==='a'?enemy:actor,events:[{type:'battle_start',time:0},turn,attack,miss?{type:'dodge',time:1250,actor:side,target,action:1}:{type:'damage',time:1250,actor:side,target,action:1,cause:'strike',amount:180,hpAfter:820},{type:'turn_end',time:2100,action:1},{type:'battle_end',time:2500}]};
 const before=JSON.stringify(battle);
 for(const mode of ['legacy','current','mixed'])for(let t=300;t<2100;t+=75){draw(context().ctx,battle,t,1000,false,true,mode);frames++;}
 assert.equal(JSON.stringify(battle),before);
 const at=t=>holySample(poseAt(battle,side,300+t,1000,turn,'current'),side==='a'?1:-1);
 const strike=at(950);if(side==='a'&&!miss)signatures.add(JSON.stringify(strike.frame.pose.points));
 if(move==='影不留踪')assert.equal(strike.frame.pose.facing,-1);
 if(move==='绊马索')for(let t=520;t<=840;t+=10){const f=at(t).frame,hip=f.pose.points[2],r=f.pose.roll||0;for(const p of f.pose.points)assert.ok(324+f.lift+hip[1]+(p[0]-hip[0])*Math.sin(r)+(p[1]-hip[1])*Math.cos(r)<335);}
 const first=context(),again=context(),empty=context();
 holyEffects(first.ctx,attack,1120,at,[765,230],1,170,true);
 holyEffects(again.ctx,attack,1120,at,[765,230],1,170,true);
 holyEffects(empty.ctx,attack,1120,at,[765,230],1,170,false);
 assert.deepEqual(first.calls,again.calls);
 assert.ok(first.calls.length>empty.calls.length,'Miss must omit impact');
}
assert.equal(signatures.size,8);
console.log(`Holy: ${frames} frames, distinct poses, both sides, hit/miss, modes, roll clearance, timing and deterministic plumes passed.`);
