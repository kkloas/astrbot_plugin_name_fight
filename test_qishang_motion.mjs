import assert from 'node:assert/strict';
import {draw,poseAt} from './web_animation/battle/InkStage.js';
import {qishangBody,qishangEffects,qishangMotion,qishangTime,qishangReplayTime,names,colors} from './web_animation/battle/qishangMotion.js';
function context(){const calls=[];return {calls,ctx:new Proxy({globalAlpha:1},{get(o,k){if(k in o)return o[k];return (...args)=>{for(const n of args)if(typeof n==='number')assert.ok(Number.isFinite(n),String(k));if(k==='ellipse')assert.ok(args[2]>=0&&args[3]>=0);calls.push([k,...args]);if(k==='measureText')return {width:30};if(k.startsWith('create'))return {addColorStop(){}};};},set(o,k,v){if(typeof v==='number')assert.ok(Number.isFinite(v));o[k]=v;return true;}})};}
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
for(const contact of [750,950,1150])for(const t of [0,900,1800,2400,2830])close(qishangTime(qishangReplayTime(t,contact),contact),t);
assert.equal(new Set(colors).size,7);
const base={...qishangMotion({move:names[0]},1100,436),x:650,lift:-12};
for(const dir of [-1,1]){
 const a=qishangBody(base,dir),b=qishangBody({...base,x:base.x+75,lift:base.lift-28},dir);close(b.center[0]-a.center[0],75);close(b.center[1]-a.center[1],-28);
 const rotated=qishangBody({...base,pose:{...base.pose,lean:.4}},dir);assert.notDeepEqual(rotated.down,a.down);close(Math.hypot(...rotated.down),1);close(rotated.down[0]*rotated.right[0]+rotated.down[1]*rotated.right[1],0);
}
let frames=0;const motifs=[];
for(const width of [600,900,1000])for(const side of ['a','b'])for(const miss of [false,true])for(const move of names){
 const target=side==='a'?'b':'a',dir=side==='a'?1:-1,f={name:'Qishang',stats:{hp:1000,spd:60},martialArt:{id:'fist_qishang',type:'unarmed'}},e={...f,martialArt:{id:'sword_huashan',type:'sword'}},turn={type:'turn_start',time:300,action:1,actor:side},attack={type:'attack',time:850,action:1,actor:side,target,martialArtId:'fist_qishang',move,weaponType:'unarmed'};
 const battle={attacker:side==='a'?f:e,defender:side==='b'?f:e,events:[{type:'battle_start',time:0},turn,attack,miss?{type:'dodge',time:1250,action:1,actor:side,target}:{type:'damage',time:1250,action:1,actor:side,target,cause:'strike',amount:220,hpAfter:780,maxHp:1000,bodyPartKey:'chest'},{type:'turn_end',time:2100,action:1},{type:'battle_end',time:2500}]};
 const before=JSON.stringify(battle);
 for(let t=300;t<=2500;t+=50){draw(context().ctx,battle,t,width,false,true,'mixed');frames++;}
 assert.equal(JSON.stringify(battle),before);
 const sample=t=>({frame:poseAt(battle,side,300+qishangReplayTime(t,950),width,turn,'current')}),receiver=poseAt(battle,target,1400,width,turn,'current'),body=qishangBody(receiver,-dir),a=context(),b=context(),c=context();
 qishangEffects(a.ctx,attack,2020,sample,body.center,dir,220,true,receiver);qishangEffects(b.ctx,attack,2020,sample,body.center,dir,220,true,receiver);qishangEffects(c.ctx,attack,2020,sample,body.center,dir,220,false,receiver);
 assert.deepEqual(a.calls,b.calls);assert.ok(a.calls.some(call=>call[0]==='clip'));assert.ok(!c.calls.some(call=>call[0]==='clip'));
 assert.deepEqual(a.calls.find(call=>call[0]==='transform'),['transform',...body.right,...body.down,...body.center]);
 // Integration must pass the current victim pose, not the pose frozen at contact.
 const rendered=context();draw(rendered.ctx,battle,1400,width,false,true,'current');if(!miss)assert.ok(rendered.calls.some(call=>JSON.stringify(call)===JSON.stringify(['transform',...body.right,...body.down,...body.center])));
 if(width===900&&side==='a'&&!miss){const start=a.calls.findIndex(call=>call[0]==='clip');motifs.push(JSON.stringify(a.calls.slice(start)));}
 const recovery=poseAt(battle,side,1990,width,turn,'current');close(recovery.x,width*(side==='a'?.235:.765));
}
assert.equal(new Set(motifs).size,8,'All internal effects must have distinct geometry');
console.log(`Qishang: ${frames} frames; live torso anchoring, rotating body axes, eight motifs, hit-only bursts, replay timing and recovery passed.`);
