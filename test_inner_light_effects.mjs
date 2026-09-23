import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {drawArtTrigger,drawArtFootwork,drawArtAura} from './web_animation/battle/innerLightEffects.js';
import {drawTrigger} from './web_animation/battle/inkEffects.js';
import {draw,poseAt} from './web_animation/battle/InkStage.js';
function context(){const calls=[];return {calls,ctx:new Proxy({globalAlpha:1},{get(o,k){if(k in o)return o[k];return (...args)=>{for(const n of args)if(typeof n==='number')assert.ok(Number.isFinite(n),String(k));calls.push([k,...args]);if(k==='measureText')return {width:30};if(k.startsWith('create'))return {addColorStop(){}};};},set(o,k,v){if(typeof v==='number')assert.ok(Number.isFinite(v));o[k]=v;return true;}})};}
const arts=JSON.parse(readFileSync('configs/neigong.json','utf8')),steps=JSON.parse(readFileSync('configs/qinggong.json','utf8'));
const fighter={name:'Test',stats:{hp:1000,spd:60},martialArt:{id:'fist_qishang',type:'unarmed'}};
let frames=0;
for(const side of ['a','b'])for(const art of [...arts,...steps]){
 const effect=art.passives?.[0]?.type||art.special_effect_data?.type;
 const event={type:['regeneration','vampirism','burst_heal'].includes(effect)?'heal':['thorns','part_counter'].includes(effect)?'damage':'passive_trigger',time:100,actor:side,target:side,cause:effect,effect,sourceSkill:{id:art.id},stacks:5,amount:5,hpAfter:900};
 const battle={attacker:{...fighter,neigong:art,qinggong:art},defender:{...fighter,neigong:art,qinggong:art},events:[event]},before=JSON.stringify(battle);
 const f=poseAt(battle,side,250,900),other=poseAt(battle,side==='a'?'b':'a',250,900),dir=side==='a'?1:-1;
 for(let age=0;age<=2800;age+=50){const a=context(),b=context();drawArtTrigger(a.ctx,event,f,dir,other,age);drawArtTrigger(b.ctx,event,f,dir,other,age);assert.deepEqual(a.calls,b.calls);draw(context().ctx,battle,age+100,900,false,true,'mixed');frames++;}
 for(const layers of [1,3,5])drawArtFootwork(context().ctx,art.id,f.x,dir,.8,500,[{x:f.x,y:324},{x:f.x-dir*20,y:324}],layers);
 drawArtAura(context().ctx,f,dir,['crisis_defense'],500,3);
 assert.equal(JSON.stringify(battle),before);
 if(art.id==='biyun_xinfa'){const c=context();drawArtTrigger(c.ctx,event,f,dir,other,2200);assert.ok(c.calls.some(c=>c[0]==='stroke'));const end=context();drawArtTrigger(end.ctx,event,f,dir,other,2700);assert.ok(!end.calls.some(c=>c[0]==='stroke'));}
 if(['shenzhao_jing','jiayi_shengong','zixia_shengong'].includes(art.id)){const a=context(),b=context();drawArtTrigger(a.ctx,event,f,dir,other,300);drawTrigger(b.ctx,event,f.x,other.x,300);assert.deepEqual(a.calls.slice(1,-1),b.calls);}
}
console.log(`Inner/light: ${frames} deterministic event frames, both sides, all 21 arts, original effects and prolonged healing passed.`);
