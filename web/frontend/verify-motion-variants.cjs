const assert=require('node:assert/strict');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:5175/motion-preview.html');
    await page.getByRole('button',{name:'暂停',exact:true}).click();
    const metrics=await page.evaluate(async()=>{
      const {motionVariantFor}=await import('/src/battle/motionVariants.ts');
      const {poseAt}=await import('/src/battle/InkStage.tsx');
      const {stateAt}=await import('/src/battle/replay.ts');
      const {legacyTechniqueFor,techniqueFor}=await import('/src/battle/martialVisuals.ts');
      const fighter={name:'试招',stats:{hp:1000,spd:60},martialArt:{id:'sword_huashan',type:'sword',name:'华山剑法'}};
      const turns=Array.from({length:1000},(_,i)=>({type:'turn_start',time:i*1900+300,action:i+1,actor:i%2?'b':'a'}));
      const attacks=turns.map(t=>({...t,type:'attack',time:t.time+550,target:t.actor==='a'?'b':'a',martialArtId:'sword_huashan',weaponType:'sword',move:'无边落木'}));
      const events=turns.flatMap((t,i)=>[t,attacks[i],{type:'damage',actor:t.actor,target:attacks[i].target,time:t.time+950,action:t.action,cause:'strike',amount:1,hpAfter:999-i,maxHp:1000}]);
      const battle={attacker:fighter,defender:{...fighter,name:'对手'},events,winner:null};
      const original=JSON.stringify(battle),choices=attacks.map(a=>motionVariantFor(battle,a));
      const cloned=JSON.parse(original),clonedAttacks=cloned.events.filter(e=>e.type==='attack');
      const cloneStable=choices.every((v,i)=>motionVariantFor(cloned,clonedAttacks[i])===v);
      const seekStable=[...attacks].reverse().every((a,i)=>motionVariantFor(battle,a)===choices[choices.length-i-1]);
      const stateBefore=JSON.stringify(stateAt(battle,1400));
      let boneError=0,matchingFrames=0,differentFrames=0;
      const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
      for(let i=0;i<40;i++) for(const t of [100,700,950,1100,1550]) {
        const turn=turns[i],time=turn.time+t,side=turn.actor;
        const old=poseAt(battle,side,time,1000,turn,'legacy'),current=poseAt(battle,side,time,1000,turn,'current');
        const mixed=poseAt(battle,side,time,1000,turn);
        if(JSON.stringify(mixed)===JSON.stringify(choices[i]==='legacy'?old:current)) matchingFrames++;
        if(JSON.stringify(old.pose)!==JSON.stringify(current.pose)) differentFrames++;
        for(const f of [old,current]) {
          const p=f.pose.points;
          for(const [a,b,len] of [[3,4,40],[5,6,40],[2,7,48],[7,8,48],[2,9,48],[9,10,48],[1,2,52]]) boneError=Math.max(boneError,Math.abs(dist(p[a],p[b])-len));
          for(const [s,e] of [[0,3],[1,5]]) boneError=Math.max(boneError,Math.abs(dist(f.pose.shoulders[s],p[e])-40));
        }
      }
      const art={...fighter,martialArt:{id:'staff_yuejiaqiang',name:'岳家枪法',type:'staff'}};
      const event={martialArtId:'staff_yuejiaqiang',move:'蛟龙出水'};
      return {legacy:choices.filter(v=>v==='legacy').length,current:choices.filter(v=>v==='current').length,cloneStable,seekStable,
        unchanged:original===JSON.stringify(battle)&&stateBefore===JSON.stringify(stateAt(battle,1400)),boneError,matchingFrames,differentFrames,
        oldMapping:legacyTechniqueFor(event,art).motion,newMapping:techniqueFor(event,art).motion};
    });
    console.log(JSON.stringify(metrics));
    assert(metrics.legacy>400 && metrics.legacy<600,'Balanced per-action choices for repeated same move');
    assert(metrics.cloneStable && metrics.seekStable && metrics.unchanged,'Stable choices, no combat mutation');
    assert.equal(metrics.matchingFrames,200,'Every mixed frame matches its chosen complete animation');
    assert(metrics.differentFrames>150,'Old and new poses genuinely differ');
    assert(metrics.boneError<1e-7,'Both variants preserve fixed bones');
    assert.equal(metrics.oldMapping,'rise');assert.equal(metrics.newMapping,'thrust');
    const options=await page.getByLabel('招式',{exact:true}).locator('option').evaluateAll(os=>os.filter(o=>!/丹羽剑法|惊潮刀法/.test(o.textContent)).map(o=>({value:o.value,name:o.textContent})));
    const seek=async t=>{await page.getByRole('slider',{name:'动作进度'}).fill(String(t));await page.waitForTimeout(25);};
    const shots=[];
    let distinct=0;
    for(const option of options) {
      await page.getByLabel('招式',{exact:true}).selectOption(option.value);
      const pause=page.getByRole('button',{name:'暂停',exact:true});if(await pause.count()) await pause.click();
      const images=[];
      for(const mode of ['legacy','current']) {
        await page.getByLabel('动画版本').selectOption(mode);await seek(1200);
        assert.equal(await page.locator('canvas').first().getAttribute('data-motion-variant'),mode);
        const image=await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL());
        await seek(0);await seek(1200);assert.equal(await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL()),image);
        images.push(image);
        if(/寒枝点雪|回马枪|穿云踢|有凤来仪|无边落木/.test(option.name)) shots.push({name:option.name,mode,src:(await page.locator('.preview-stages section').nth(1).screenshot()).toString('base64')});
      }
      if(images[0]!==images[1]) distinct++;
    }
    assert.equal(distinct,70);
    await page.getByLabel('动画版本').selectOption('mixed');await seek(1200);
    const choice=await page.locator('canvas').first().getAttribute('data-motion-variant');
    const image=await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL());
    await page.getByRole('button',{name:'重播',exact:true}).click();await page.getByRole('button',{name:'暂停',exact:true}).click();await seek(1200);
    assert.equal(await page.locator('canvas').first().getAttribute('data-motion-variant'),choice);
    assert.equal(await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL()),image);
    for(const mode of ['legacy','current','mixed']) for(const width of [768,390,320]) {
      await page.getByLabel('动画版本').selectOption(mode);await page.setViewportSize({width,height:1000});await seek(1200);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    }
    const grid=await browser.newPage({viewport:{width:1600,height:1000}});
    await grid.setContent(`<html><head><meta charset="utf-8"><style>body{margin:0;background:white;font:18px sans-serif;display:grid;grid-template-columns:1fr 1fr}section{min-width:0}h2{margin:10px;font-size:18px}img{width:100%}</style></head><body>${shots.map(f=>`<section><h2>${f.name} / ${f.mode==='legacy'?'旧版':'新版'}</h2><img src="data:image/png;base64,${f.src}"></section>`).join('')}</body></html>`);
    await grid.screenshot({path:path.resolve(__dirname,'../../output/playwright/motion-variants.png'),fullPage:true});
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,moves:70,renderings:140,distinct,errors}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
