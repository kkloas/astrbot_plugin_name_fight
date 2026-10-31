import {serpentMotion,names} from './web_animation/battle/serpentMotion.js';
import {draw,poseAt} from './web_animation/battle/InkStage.js';
import assert from 'node:assert/strict';
let calls=0,frames=0;
const ctx=new Proxy({globalAlpha:1},{get(o,k){if(k in o)return o[k];if(k==='measureText')return ()=>({width:30});if(k.startsWith('create'))return ()=>({addColorStop(){}});return (...args)=>{for(const a of args)if(typeof a==='number'&&!Number.isFinite(a))throw Error(k+' nonfinite');calls++;}},set(o,k,v){if(typeof v==='number'&&!Number.isFinite(v))throw Error(k);o[k]=v;return true;}});
for(const width of [600,1000])for(const side of ['a','b'])for(const miss of [false,true])for(const move of names){const target=side==='a'?'b':'a',f={name:'test',stats:{hp:1000,spd:60},martialArt:{id:'whip_baimang',type:'flexible_weapon'}},e={...f,martialArt:{id:'sword_huashan',type:'sword'}};const battle={attacker:side==='a'?f:e,defender:side==='b'?f:e,events:[{type:'battle_start',time:0},{type:'turn_start',time:0,action:1,actor:side},{type:'attack',time:650,action:1,actor:side,target,martialArtId:'whip_baimang',move,weaponType:'flexible_weapon'},{type:miss?'dodge':'damage',time:950,action:1,actor:side,target,cause:'strike',amount:220,hpAfter:780,maxHp:1000,bodyPartKey:'chest'},{type:'turn_end',time:2750,action:1},{type:'battle_end',time:3100}]};for(let time=0;time<=3100;time+=50){draw(ctx,battle,time,width,false,true,'current');const m=serpentMotion({move},time,width*.53-210);for(const p of m.pose.points)if(!p.every(Number.isFinite))throw Error(move);frames++;}}
for(const side of ['a','b'])for(const webEnhanced of [false,true])for(const move of names){
 const target=side==='a'?'b':'a',f={name:'test',stats:{hp:1000,spd:60},martialArt:{id:'whip_baimang',type:'flexible_weapon'}},e={...f,martialArt:{id:'sword_huashan',type:'sword'}};
 const turn={type:'turn_start',time:0,action:1,actor:side},battle={attacker:side==='a'?f:e,defender:side==='b'?f:e,events:[turn,{type:'attack',time:550,action:1,actor:side,target,martialArtId:'whip_baimang',move},{type:'damage',time:950,action:1,actor:side,target,cause:'strike',amount:10,hpAfter:990,maxHp:1000},{type:'battle_end',time:5000}]};
 const before=poseAt(battle,side,1679,1000,turn,'current',webEnhanced),after=poseAt(battle,side,1681,1000,turn,'current',webEnhanced);
 const tip=before.pose.whip.at(-1),hand=after.pose.points[6],angle=after.pose.sword,dir=side==='a'?1:-1;
 const distance=Math.hypot(before.x+dir*tip[0]-(after.x+dir*(hand[0]+179*Math.cos(angle))),before.lift+tip[1]-(after.lift+hand[1]+179*Math.sin(angle)));
 assert.ok(distance<1,`${move} ${side} recovery jump: ${distance}`);
}
console.log(JSON.stringify({frames,calls,status:'passed'}));
