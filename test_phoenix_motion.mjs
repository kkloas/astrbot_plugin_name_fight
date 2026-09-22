import assert from 'node:assert/strict';
import {draw,poseAt} from './web_animation/battle/InkStage.js';
import {names,phoenixMotion,phoenixEffects,phoenixTime,phoenixReplayTime} from './web_animation/battle/phoenixMotion.js';
function context(){const calls=[];return {calls,ctx:new Proxy({globalAlpha:1},{get(o,k){if(k in o)return o[k];return (...a)=>{assert.ok(a.every(v=>typeof v!=='number'||Number.isFinite(v)),String(k));calls.push([k,...a]);if(k==='measureText')return {width:30};if(k==='createRadialGradient'||k==='createLinearGradient')return {addColorStop(){}};};}})};}
for(const move of names)for(const contact of [750,950,1400])for(const t of [0,500,1400,1900])assert.ok(Math.abs(phoenixTime(phoenixReplayTime(t,contact,move),contact,move)-t)<1e-8);
const landing=phoenixMotion({move:names[7]},1400,320),rest=phoenixMotion({move:names[7]},1730,320);
assert.deepEqual(landing,rest,'Landing must hold before fade');
const p=landing.pose.points[6];assert.ok(Math.abs(324+landing.lift+p[1]+140*Math.sin(landing.pose.sword)-329)<2,'Spear must reach the ground');
assert.equal(phoenixMotion({move:names[7]},1891,320).opacity,0);
let frames=0,maxGrip=0,minY=Infinity,maxY=-Infinity;
for(const move of names)for(const side of ['a','b'])for(const miss of [false,true])for(const width of [600,1000]){
 const target=side==='a'?'b':'a',fighter={name:'Heavy',stats:{hp:1000,spd:60},martialArt:{id:'staff_bainiaochaofeng',type:'staff'}},enemy={name:'Enemy',stats:{hp:1000,spd:60},martialArt:{id:'sword_huashan',type:'sword'}},turn={type:'turn_start',time:300,actor:side,action:1},attack={type:'attack',time:850,action:1,actor:side,target,martialArtId:'staff_bainiaochaofeng',move};
 const battle={attacker:side==='a'?fighter:enemy,defender:side==='a'?enemy:fighter,events:[{type:'battle_start',time:0},turn,attack,miss?{type:'dodge',time:1250,action:1,actor:side,target}:{type:'damage',time:1250,action:1,actor:side,target,cause:'strike',amount:280,hpAfter:720},{type:'turn_end',time:2100,action:1},{type:'battle_end',time:2500}]};
 const before=JSON.stringify(battle),dir=side==='a'?1:-1;
 for(let time=300;time<2400;time+=50){draw(context().ctx,battle,time,width,false,true,'mixed');frames++;const f=poseAt(battle,side,time,width,turn,'mixed'),p=f.pose.points,angle=f.pose.sword;if(time>500&&time<1700){const y=324+f.lift+p[6][1]+110*Math.sin(angle);minY=Math.min(minY,y);maxY=Math.max(maxY,y);if(move!==names[0])maxGrip=Math.max(maxGrip,Math.hypot(p[4][0]-(p[6][0]-17*Math.cos(angle)),p[4][1]-(p[6][1]-17*Math.sin(angle))));}}
 assert.equal(JSON.stringify(battle),before);
}
console.log(`Phoenix: ${frames} frames, time mapping, ground contact and landing hold passed.`);
