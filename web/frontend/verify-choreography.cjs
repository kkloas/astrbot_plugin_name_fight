const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const out=path.resolve(__dirname,'../../output/playwright');
  const fixtures=JSON.parse(fs.readFileSync(path.join(out,'martial-fixtures.json'),'utf8'));
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1920,height:1080}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    const snapshot=await(await page.request.get('http://127.0.0.1:5175/api/session/bootstrap')).json();
    let current=fixtures.moves[0].battle;
    await page.route('**/api/battles/duel',route=>route.fulfill({json:{...current,snapshot}}));
    await page.goto('http://127.0.0.1:5175');
    const numeric=await page.evaluate(async()=>{
      const {impactFor,contactTime,plantedFoot}=await import('/src/battle/choreography.ts');
      const t={motion:'cleave',trail:'edge',weight:1.8};
      const damage=(amount,crit=false)=>({type:'damage',cause:'strike',amount,crit});
      const profiles=[50,250,400].map(n=>impactFor(damage(n),1000,t));
      const clock=Array.from({length:801},(_,i)=>contactTime(800+i,950,100));
      const feet=[.03,.12].map(p=>plantedFoot(p,0,270,0)[0]+270*p);
      return {profiles,scaled:impactFor(damage(100),2000,t),
        dodge:impactFor({type:'dodge'},1000,t),chip:impactFor(damage(5,true),1000,t),
        monotonic:clock.every((v,i)=>!i||v>=clock[i-1]),hold:[970,1010].map(n=>contactTime(n,950,100)),
        catchup:contactTime(1400,950,100),feet,swing:plantedFoot(.25,0,270,0)[1]};
    });
    assert(numeric.profiles[0].force<numeric.profiles[1].force);
    assert(numeric.profiles[1].force<numeric.profiles[2].force);
    assert.equal(numeric.profiles[0].force,numeric.scaled.force);
    assert.equal(numeric.dodge.force,0);assert.equal(numeric.dodge.cinematic,false);
    assert.equal(numeric.chip.heavy,false);
    assert.equal(numeric.monotonic,true);assert.deepEqual(numeric.hold,[950,950]);
    assert.equal(numeric.catchup,1400);
    assert(Math.abs(numeric.feet[0]-numeric.feet[1])<1e-8,'Planted foot stays in world space');
    assert(numeric.swing<0,'Swinging foot lifts clear of the floor');
    await page.getByRole('button',{name:'对战',exact:true}).click();
    const slider=page.getByRole('slider',{name:'战斗进度'});
    const stage=page.locator('.duel-stage');
    const canvas=page.locator('canvas');
    const seek=async(t)=>{await slider.fill(String(t));await page.waitForTimeout(40);};
    let first=true;
    const load=async battle=>{
      current=battle;
      if(first) {await page.getByRole('button',{name:'开始试炼',exact:true}).click();first=false;}
      else {await page.getByRole('button',{name:'跳过',exact:true}).click();await page.getByRole('button',{name:'再战一场',exact:true}).click();}
      await page.getByRole('button',{name:'暂停',exact:true}).click();
    };
    const frames=[];
    for(const id of ['blade_chengyun-5','staff_yuejiaqiang-7','leg_shadow_whirl-1','hidden_baoyulihua-7','zither_duanzhi-7','sword_huashan-6']) {
      const item=fixtures.moves.find(i=>i.id===id);assert(item,id);await load(item.battle);
      const turn=item.battle.events.find(e=>e.type==='turn_start');
      const images=[];
      for(const local of [400,670,880,970,1350,1660]) {
        await seek(turn.time+local);
        const image=await stage.screenshot();images.push(image.toString('base64'));
        const pixels=await canvas.evaluate(c=>c.toDataURL());
        await seek(0);await seek(turn.time+local);
        assert.equal(await canvas.evaluate(c=>c.toDataURL()),pixels,`${id} deterministic frame ${local}`);
      }
      frames.push({id,images});
    }
    const grid=await browser.newPage({viewport:{width:1800,height:1600}});
    await grid.setContent(`<html><head><style>body{margin:0;background:#fff;font:16px sans-serif}section{display:grid;grid-template-columns:repeat(3,1fr)}h2{font-size:16px;margin:12px}img{width:100%;display:block}</style></head><body>${frames.map(row=>`<h2>${row.id}: 400 / 670 / 880 / 970 / 1350 / 1660 ms</h2><section>${row.images.map(src=>`<img src="data:image/png;base64,${src}">`).join('')}</section>`).join('')}</body></html>`);
    await grid.screenshot({path:path.join(out,'choreography-sequences.png'),fullPage:true});
    await grid.close();
    const heavy=fixtures.effects.find(i=>i.battle.events.some(e=>e.cause==='strike'&&e.actor==='b'&&e.amount/e.maxHp>=.3));
    assert(heavy,'Real high-damage right-side attack is available');
    if(heavy) {
      await load(heavy.battle);const event=heavy.battle.events.find(e=>e.cause==='strike'&&e.actor==='b'&&e.amount/e.maxHp>=.3);
      await seek(event.time+65);await stage.screenshot({path:path.join(out,'choreography-heavy.png')});
      assert.equal(await page.locator('.duel-move-heavy').count(),1);
      const normal=await canvas.evaluate(c=>c.toDataURL());
      await page.emulateMedia({reducedMotion:'reduce'});await seek(event.time+66);
      assert.equal(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),true);
      await seek(event.time+65);assert.notEqual(await canvas.evaluate(c=>c.toDataURL()),normal);
      for(const width of [390,768,1440]) {
        await page.setViewportSize({width,height:900});await seek(event.time+65);
        await page.locator('.ink-duel').scrollIntoViewIfNeeded();
        await page.screenshot({path:path.join(out,`choreography-heavy-${width}.png`),fullPage:true});
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      }
    }
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({ok:true,sequences:frames.length,frames:36,numeric,errors}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
