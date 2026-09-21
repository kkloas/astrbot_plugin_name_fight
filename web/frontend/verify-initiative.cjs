const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const out=path.resolve(__dirname,'../../output/playwright');
  const skills=JSON.parse(fs.readFileSync(path.join(out,'skill-fixtures.json'),'utf8'));
  const fixtures=JSON.parse(fs.readFileSync(path.join(out,'martial-fixtures.json'),'utf8'));
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1920,height:1080}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    const snapshot=await(await page.request.get('http://127.0.0.1:5175/api/session/bootstrap')).json();
    let current=skills[0].battle;
    await page.route('**/api/battles/duel',route=>route.fulfill({json:{...current,snapshot}}));
    await page.goto('http://127.0.0.1:5175');
    const contract=await page.evaluate(async fixtures=>{
      const {stateAt}=await import('/src/battle/replay.ts');
      let checks=0;const errors=[];
      const equal=(a,b)=>Math.abs(a-b)<1e-7;
      for(const item of fixtures) for(const e of item.battle.events) {
        if(e.gauge) {
          const s=stateAt(item.battle,e.type==='gauge_charge'?e.endTime:e.time);
          for(const side of ['a','b']) {
            if(!equal(s.gauge[side],e.gauge[side])) errors.push(item.id+': '+e.type+' gauge '+side);
            if(!equal(s.speeds[side],e.speeds[side])) errors.push(item.id+': '+e.type+' speed '+side);
            checks++;
          }
          if(e.type==='gauge_charge') {
            const middle=stateAt(item.battle,(e.time+e.endTime)/2);
            for(const side of ['a','b']) if(!equal(middle.gauge[side],(e.gaugeFrom[side]+e.gauge[side])/2)) errors.push('interpolation');
          }
        }
        if(e.gaugeValue!==undefined && !equal(stateAt(item.battle,e.time).gauge[e.target],e.gaugeValue)) errors.push('boost');
        if(e.speedAfter!==undefined && !equal(stateAt(item.battle,e.time).speeds[e.target],e.speedAfter)) errors.push('slow');
      }
      return {checks,errors};
    },[...skills,...fixtures.effects]);
    assert.deepEqual(contract.errors,[]);
    await page.getByRole('button',{name:'对战',exact:true}).click();
    const slider=page.getByRole('slider',{name:'战斗进度'});
    const canvas=page.locator('canvas');
    const seek=async t=>{await slider.fill(String(t));await page.waitForTimeout(60);};
    let first=true;
    const load=async battle=>{
      current=battle;
      if(first) {await page.getByRole('button',{name:'开始试炼',exact:true}).click();first=false;}
      else {
        const skip=page.getByRole('button',{name:'跳过',exact:true});
        if(await skip.isEnabled()) await skip.click();
        await page.getByRole('button',{name:'再战一场',exact:true}).click();
      }
      await page.getByRole('button',{name:'暂停',exact:true}).click();
    };
    const assertHud=async(battle,t)=>{
      const expected=await page.evaluate(async({battle,t})=>{
        const {stateAt,initiativeAt}=await import('/src/battle/replay.ts');
        const state=stateAt(battle,t);return {...state,gauge:initiativeAt(battle,t,state)};
      },{battle,t});
      assert.deepEqual(await page.getByRole('progressbar',{name:/行动条$/}).evaluateAll(es=>es.map(e=>+e.getAttribute('aria-valuenow'))),[expected.gauge.a,expected.gauge.b].map(n=>Math.min(100,Math.max(0,n))));
      assert.deepEqual(await page.getByRole('progressbar',{name:/气血$/}).evaluateAll(es=>es.map(e=>+e.getAttribute('aria-valuenow'))),[expected.hp.a,expected.hp.b]);
    };
    for(const item of skills) {
      await load(item.battle);await seek(item.time+240);
      await assertHud(item.battle,item.time+240);
      const frozen=await canvas.evaluate(c=>c.toDataURL());
      const hud=await page.locator('.duel-hud').innerText();
      await page.waitForTimeout(120);
      assert.equal(await canvas.evaluate(c=>c.toDataURL()),frozen);
      assert.equal(await page.locator('.duel-hud').innerText(),hud);
      await seek(0);await seek(item.time+240);
      assert.equal(await canvas.evaluate(c=>c.toDataURL()),frozen);
      assert((await page.locator('.duel-specials').innerText()).includes(item.battle.attacker.neigong.id===item.id?item.battle.attacker.neigong.name:item.battle.attacker.qinggong.name));
      await page.locator('.duel-stage').screenshot({path:path.join(out,`skill-${item.id}.png`)});
    }
    const smooth=await page.evaluate(async battle=>{
      const {initiativeAt}=await import('/src/battle/replay.ts');
      const turn=battle.events.find(e=>e.type==='turn_start');
      return [300,600,900,1200].map(offset=>initiativeAt(battle,turn.time+offset));
    },skills[0].battle);
    for(let i=1;i<smooth.length;i++) {
      assert(smooth[i].a>smooth[i-1].a,'Gauge grows during the attack animation');
      assert(smooth[i].b>smooth[i-1].b,'Both gauges grow continuously, not only between turns');
    }
    const slowContinuity=await page.evaluate(async battle=>{
      const {initiativeAt}=await import('/src/battle/replay.ts');
      const e=battle.events.find(e=>e.status==='slowed');
      return {before:initiativeAt(battle,e.time-1)[e.target],after:initiativeAt(battle,e.time+1)[e.target]};
    },fixtures.effects.find(i=>i.id==='slowed').battle);
    assert(slowContinuity.after>=slowContinuity.before,'Slowing down changes growth rate without resetting progress');
    assert(slowContinuity.after-slowContinuity.before<1,'Speed changes do not jump the gauge');
    for(const effect of ['battle_start_first_strike','low_hp_extra_action','slowed']) {
      const item=fixtures.effects.find(i=>i.id===effect);await load(item.battle);
      await seek(item.time);await assertHud(item.battle,item.time);
      await page.locator('.duel-stage').screenshot({path:path.join(out,`initiative-${effect}.png`)});
      const charge=item.battle.events.find(e=>e.type==='gauge_charge');
      await seek((charge.time+charge.endTime)/2);await assertHud(item.battle,(charge.time+charge.endTime)/2);
      await page.getByRole('button',{name:'跳过',exact:true}).click();
      assert((await page.locator('.duel-initiative').first().innerText()).includes('已结束'));
    }
    const item=fixtures.effects.find(i=>i.id==='burst_heal');await load(item.battle);await seek(item.time+240);
    for(const width of [1920,1440,768,390,320]) {
      await page.setViewportSize({width,height:1000});await page.locator('.ink-duel').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(out,`initiative-layout-${width}.png`),fullPage:true});
      const hud=await page.locator('.duel-hud').boundingBox(),arena=await page.locator('.duel-arena').boundingBox();
      assert(hud.y+hud.height<=arena.y+1,'HUD does not overlap the arena');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    }
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({ok:true,skills:skills.length,gaugeChecks:contract.checks,viewports:5,errors}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
