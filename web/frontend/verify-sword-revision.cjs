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
      const {poseAt}=await import('/src/battle/InkStage.tsx');
      const {swordSequence}=await import('/src/battle/swordSequences.ts');
      const names=['有凤来仪','天绅倒悬','无边落木','金雁横空','回风斩','青山隐隐'];
      const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
      let boneError=0,headError=0,shoulderError=0,maxJump=0,worst=null;
      for(const name of names) for(const side of ['a','b']) for(const outcome of ['damage','dodge','death','victory','skip']) {
        const target=side==='a'?'b':'a';
        const art={id:name==='回风斩'?'sword_falling_plum':'sword_huashan',type:'sword',name:'剑法'};
        const actor={name:'甲',stats:{hp:1000,spd:60},martialArt:art};
        const defender={...actor,name:'乙'};
        const turn={type:'turn_start',actor:side,action:1,time:300};
        const attack={type:'attack',actor:side,target,action:1,time:850,martialArtId:art.id,move:name,weaponType:'sword'};
        const events=[{type:'battle_start',time:0},turn,attack,
          outcome==='dodge'?{type:'dodge',actor:side,target,action:1,time:1250}:
          {type:'damage',actor:side,target,action:1,time:1250,cause:'strike',amount:outcome==='death'?1000:140,hpAfter:outcome==='death'?0:860,maxHp:1000},
          {type:'turn_end',action:1,time:2100}];
        if(outcome==='victory') events.push({type:'victory_start',time:2200,actor:side,victoryKind:'dominant',victoryVariant:1});
        if(outcome==='skip') events.push({type:'turn_skip',time:1400,action:1,actor:side,reason:'disarmed'});
        events.push({type:'battle_end',time:4200});events.sort((a,b)=>a.time-b.time);
        const battle={attacker:actor,defender,events,winner:null};
        for(const who of ['a','b']) {
          let previous;
          for(let t=0;t<=4200;t+=4) {
            const f=poseAt(battle,who,t,1000,t>=300 && t<2200?turn:undefined,'current'),p=f.pose.points;
            for(const [a,b,len] of [[3,4,40],[5,6,40],[2,7,48],[7,8,48],[2,9,48],[9,10,48],[1,2,52]]) boneError=Math.max(boneError,Math.abs(distance(p[a],p[b])-len));
            for(const [s,e] of [[0,3],[1,5]]) boneError=Math.max(boneError,Math.abs(distance(f.pose.shoulders[s],p[e])-40));
            headError=Math.max(headError,Math.abs(distance(p[0],p[1])-21));
            shoulderError=Math.max(shoulderError,Math.abs(distance(f.pose.shoulders[0],f.pose.shoulders[1])-20));
            if(previous && t>=304 && t<1900 && who===side && outcome==='damage') for(let i=0;i<p.length;i++) {
              const d=distance([f.x+p[i][0],f.lift+p[i][1]],[previous.x+previous.pose.points[i][0],previous.lift+previous.pose.points[i][1]]);
              if(d>maxJump){maxJump=d;worst={name,t,i,d};}
            }
            previous=f;
          }
        }
      }
      const event=name=>({martialArtId:'sword_huashan',move:name});
      const dive=swordSequence(event('有凤来仪'),950,320),rise=swordSequence(event('天绅倒悬'),950,320);
      const flurry=[550,645,735,835,950].map(t=>swordSequence(event('无边落木'),t,320).pose.points[6]);
      return {boneError,headError,shoulderError,maxJump,worst,dive:{lift:dive.lift,angle:dive.pose.sword},rise:{height:-rise.pose.points[2][1],angle:rise.pose.sword},flurry};
    });
    console.log(JSON.stringify(metrics));
    assert(metrics.boneError<1e-7 && metrics.headError<1e-7 && metrics.shoulderError<1e-7,'All final states have identical bone lengths and shoulder width');
    assert(metrics.maxJump<30,'No discontinuous attack pose');
    assert(metrics.dive.lift<-40 && metrics.dive.angle>.4,'Descending airborne thrust');
    assert(metrics.rise.height<60 && metrics.rise.angle<-.4,'Low rising thrust');
    assert(metrics.flurry[0][0]>metrics.flurry[1][0]+25 && metrics.flurry[2][0]>metrics.flurry[3][0]+25,'Three distinct extensions with retraction');
    const frames=[];
    const names=['有凤来仪','天绅倒悬','无边落木','金雁横空','回风斩','青山隐隐'];
    const select=page.getByLabel('招式',{exact:true});
    const options=await select.locator('option').evaluateAll(os=>os.map(o=>({value:o.value,label:o.textContent})));
    const seek=async t=>{await page.getByRole('slider',{name:'动作进度'}).fill(String(t));await page.waitForTimeout(40);};
    for(const name of names) {
      await select.selectOption(options.find(o=>o.label.endsWith('/ '+name)).value);
      const pause=page.getByRole('button',{name:'暂停',exact:true});if(await pause.count()) await pause.click();
      for(const time of [700,1035,1250,1380]) {
        await seek(time);
        const image=await page.locator('.preview-stages section').nth(1).screenshot();
        frames.push({name,time,src:image.toString('base64')});
        const before=await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL());
        await seek(0);await seek(time);assert.equal(await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL()),before);
      }
      for(const side of ['a','b']) for(const miss of [true,false]) {
        await page.getByLabel('出招方').selectOption(side);await page.getByLabel('闪避').setChecked(miss);
        const pause=page.getByRole('button',{name:'暂停',exact:true});if(await pause.count()) await pause.click();
        await seek(1320);
      }
      await page.getByLabel('出招方').selectOption('a');
      const pause2=page.getByRole('button',{name:'暂停',exact:true});if(await pause2.count()) await pause2.click();
    }
    for(const width of [768,390,320]) {
      await page.setViewportSize({width,height:1000});await seek(1250);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    }
    await page.screenshot({path:path.resolve(__dirname,'../../output/playwright/sword-revision-mobile.png'),fullPage:true});
    const grid=await browser.newPage({viewport:{width:2000,height:1200}});
    await grid.setContent(`<html><head><meta charset="utf-8"><style>body{margin:0;background:#fff;display:grid;grid-template-columns:repeat(4,1fr);font:16px sans-serif}section{min-width:0}h2{font-size:16px;margin:10px}img{width:100%}</style></head><body>${frames.map(f=>`<section><h2>${f.name} / ${f.time}ms</h2><img src="data:image/png;base64,${f.src}"></section>`).join('')}</body></html>`);
    await grid.screenshot({path:path.resolve(__dirname,'../../output/playwright/sword-revision.png'),fullPage:true});
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,moves:6,finalStateCases:60,frames:24,errors}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
