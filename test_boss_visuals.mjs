import assert from 'node:assert/strict';
import fs from 'node:fs';
import { draw, poseAt } from './web_animation/battle/InkStage.js';
import { visualBattle } from './web_animation/battle/bossVisuals.js';
const art = JSON.parse(fs.readFileSync(new URL('./configs/martial_arts.json', import.meta.url))).find(a => a.id === 'sword_huashan');
function context() {
    const calls=[];
    return { calls, ctx:new Proxy({globalAlpha:1}, {get(o,k) {
        if(k in o) return o[k];
        return (...args) => {
            for(const value of args) if(typeof value === 'number') assert.ok(Number.isFinite(value), String(k));
            calls.push([k,...args]);
            if(k==='measureText') return {width:30};
            if(k==='createRadialGradient'||k==='createLinearGradient') return {addColorStop(){}};
        };
    }})};
}
let frames=0;
for(const phase of [1,2]) for(const side of ['a','b']) for(const width of [600,1000]) for(const [index,move] of art.moves.entries()) {
    const target=side==='a'?'b':'a';
    const fighter={name:'Boss',bossKey:`dragon_chief_phase${phase}`,stats:{hp:1000,spd:90},martialArt:{id:art.id,name:art.name,type:art.type},neigong:{id:'shenzhao_jing'},qinggong:{id:'lightning_flash'}};
    const enemy={...fighter,bossKey:null,name:'Player'};
    const turn={type:'turn_start',time:300,actor:side,action:1};
    const attack={type:'attack',time:850,action:1,actor:side,target,martialArtId:art.id,move:`renamed-${index}`,visualMove:move.name,moveIndex:index};
    const battle={attacker:side==='a'?fighter:enemy,defender:side==='a'?enemy:fighter,boss:{phase,intro:true},events:[
        {type:'battle_start',time:0},turn,attack,{type:'damage',time:1250,action:1,actor:side,target,cause:'strike',amount:100,hpAfter:900},
        {type:'turn_end',time:2100,action:1},{type:'battle_end',time:2500}]};
    const before=JSON.stringify(battle);
    const original={...battle,events:battle.events.map(e=>e===attack?{...e,move:move.name,visualMove:undefined}:e)};
    assert.equal(visualBattle(battle),visualBattle(battle),'Visual mapping is cached');
    for(let time=0;time<=2500;time+=100) {
        const a=context(),b=context();
        draw(a.ctx,battle,time,width,false,true,'mixed');draw(b.ctx,battle,time,width,false,true,'mixed');
        assert.deepEqual(a.calls,b.calls,'Seeking must be deterministic');
        assert.deepEqual(poseAt(battle,side,time,width,turn,'current'),poseAt(original,side,time,width,turn,'current'),'Renaming must preserve the complete original motion');
        frames++;
    }
    assert.equal(JSON.stringify(battle),before,'Drawing must not mutate combat data');
    const disarmed={...battle,events:[...battle.events.slice(0,3),{type:'status_apply',time:900,target:side,status:'disarmed'},...battle.events.slice(3)]};
    assert.equal(poseAt(disarmed,side,1100,width,turn).armed,false);
}
console.log(`Boss visuals: ${frames} deterministic frames; 2 phases, 8 moves, both sides and widths, renamed motion and disarm passed.`);
