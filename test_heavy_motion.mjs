import assert from 'node:assert/strict';
import {draw,poseAt} from './web_animation/battle/InkStage.js';
import {names,heavyMotion,heavyEffects,heavyTime,heavyReplayTime,heavyShake} from './web_animation/battle/heavyMotion.js';
function context(){const calls=[];return {calls,ctx:new Proxy({globalAlpha:1},{get(o,k){if(k in o)return o[k];return (...a)=>{assert.ok(a.every(v=>typeof v!=='number'||Number.isFinite(v)),String(k));calls.push([k,...a]);if(k==='measureText')return {width:30};if(k==='createRadialGradient'||k==='createLinearGradient')return {addColorStop(){}};};}})};}
for(const contact of [750,950,1050])for(const t of [0,400,950,1250])assert.ok(Math.abs(heavyTime(heavyReplayTime(t,contact),contact)-t)<1e-8);
assert.deepEqual(heavyShake(names[7],-1),[0,0]);assert.deepEqual(heavyShake(names[7],400),[0,0]);
const keyFrame=i=>heavyMotion({move:names[i]},950,365);
assert.ok(keyFrame(1).pose.sword < -1.4,'Second move must brace the blade upright');
assert.ok(Math.abs(keyFrame(2).pose.sword)<.1,'Third move must intercept horizontally');
assert.ok(keyFrame(3).pose.sword>.5,'Fourth move must slap diagonally');
let frames=0,maxGrip=0,minY=Infinity,maxY=-Infinity;
for(const move of names)for(const side of ['a','b'])for(const miss of [false,true])for(const width of [600,1000]){
 const target=side==='a'?'b':'a',fighter={name:'Heavy',stats:{hp:1000,spd:60},martialArt:{id:'sword_xuantie',type:'sword'}},enemy={name:'Enemy',stats:{hp:1000,spd:60},martialArt:{id:'sword_huashan',type:'sword'}},turn={type:'turn_start',time:300,actor:side,action:1},attack={type:'attack',time:850,action:1,actor:side,target,martialArtId:'sword_xuantie',move};
 const battle={attacker:side==='a'?fighter:enemy,defender:side==='a'?enemy:fighter,events:[{type:'battle_start',time:0},turn,attack,miss?{type:'dodge',time:1250,action:1,actor:side,target}:{type:'damage',time:1250,action:1,actor:side,target,cause:'strike',amount:280,hpAfter:720},{type:'turn_end',time:2100,action:1},{type:'battle_end',time:2500}]};
 const before=JSON.stringify(battle),dir=side==='a'?1:-1;
 for(let time=300;time<2400;time+=50){draw(context().ctx,battle,time,width,false,true,'mixed');frames++;const f=poseAt(battle,side,time,width,turn,'mixed'),p=f.pose.points,angle=f.pose.sword;if(time>500&&time<1700){const y=324+f.lift+p[6][1]+110*Math.sin(angle);minY=Math.min(minY,y);maxY=Math.max(maxY,y);if(move!==names[0])maxGrip=Math.max(maxGrip,Math.hypot(p[4][0]-(p[6][0]-17*Math.cos(angle)),p[4][1]-(p[6][1]-17*Math.sin(angle))));}}
 assert.equal(JSON.stringify(battle),before);
 if(!miss)assert.deepEqual(poseAt(battle,side,1250,width,turn,'current').pose,poseAt(battle,side,1330,width,turn,'current').pose,'Contact must hold before recovery');
 const sample=t=>{const f=poseAt(battle,side,300+t,width,turn,'current'),hand=[f.x+dir*f.pose.points[6][0],324+f.lift+f.pose.points[6][1]];return {hand,tip:[hand[0]+dir*Math.cos(f.pose.sword)*110,hand[1]+Math.sin(f.pose.sword)*110],root:[f.x,324+f.lift],frame:f}};
 const a=context(),b=context(),c=context();heavyEffects(a.ctx,attack,1230,sample,[width*.765,230],dir,280,true);heavyEffects(b.ctx,attack,1230,sample,[width*.765,230],dir,280,true);heavyEffects(c.ctx,attack,1230,sample,[width*.765,230],dir,280,false);assert.deepEqual(a.calls,b.calls);assert.ok(a.calls.length>c.calls.length,'Misses must omit rubble eruptions');
}
assert.ok(minY>=0&&maxY<330,`Blade clipping: ${minY}, ${maxY}`);assert.ok(maxGrip<2,`Grip drift: ${maxGrip}`);
console.log(`Heavy: ${frames} frames; distinct moves 2/3/4, hit/miss, both sides and widths, contact hold, grip, blade bounds, deterministic rubble passed.`);
