const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const out=path.resolve(__dirname,'../../output/playwright');
  const fixtures=JSON.parse(fs.readFileSync(path.join(out,'martial-fixtures.json'),'utf8'));
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1600,height:1000}});
    const errors=[],blocked=[];
    page.on('pageerror',e=>errors.push(e.message));
    const pve=await(await page.request.get('http://127.0.0.1:5175/api/pve')).json();
    const stage=pve.chapters.flatMap(c=>c.stages).find(s=>s.id===pve.nextStageId);
    pve.profile.energy=100;
    let current=fixtures.moves[0].battle,requests=0;
    // No mutation request may reach the backend, including accidental team saves.
    await page.route('**/api/**',route=>{
      const request=route.request(),url=new URL(request.url());
      if(request.method()==='GET') return url.pathname==='/api/pve'?route.fulfill({json:pve}):route.continue();
      if(url.pathname.endsWith('/challenge')) {
        requests++;
        const playerTeam=[current.attacker],enemyTeam=[current.defender];
        return route.fulfill({json:{stage,victory:true,stars:3,firstClear:false,bestStars:3,
          reward:{points:0,items:[]},profile:pve.profile,pve,playerTeam,enemyTeam,
          duels:[{...current,index:0,transition:'',traitDelta:0,displayLogs:[],playerTeam,enemyTeam}]}});
      }
      blocked.push(url.pathname);return route.abort();
    });
    await page.goto('http://127.0.0.1:5175');
    await page.getByRole('button',{name:'江湖历练',exact:true}).click();
    const slider=page.getByRole('slider',{name:'战斗进度'}),canvas=page.locator('canvas');
    const seek=async t=>{await slider.fill(String(t));await page.waitForTimeout(20);};
    let first=true;
    for(const item of [...fixtures.moves,...fixtures.effects]) {
      current=item.battle;
      if(first) {await page.getByRole('button',{name:/^挑战关卡/}).click();first=false;}
      else {
        await page.getByRole('button',{name:'跳至结算',exact:true}).click();
        await page.getByRole('button',{name:'再次挑战',exact:true}).click();
      }
      await page.getByRole('button',{name:'暂停',exact:true}).click();
      const attack=current.events.find(e=>e.type==='attack');
      const at=item.time===undefined?attack.time+430:item.time+180;
      await seek(at);
      const picture=await canvas.evaluate(c=>c.toDataURL());
      await seek(0);await seek(at);
      assert.equal(await canvas.evaluate(c=>c.toDataURL()),picture,`${item.id}: deterministic PVE replay`);
      const expected={a:current.attacker.currentHp??current.attacker.stats.hp,b:current.defender.currentHp??current.defender.stats.hp};
      for(const e of current.events) if(e.time<=at && e.hpAfter!==undefined) expected[e.target]=e.hpAfter;
      assert.deepEqual(await page.getByRole('progressbar',{name:/气血$/}).evaluateAll(es=>es.map(e=>+e.getAttribute('aria-valuenow'))),[expected.a,expected.b]);
      if(['sword_falling_plum-0','staff_yuejiaqiang-7','leg_shadow_whirl-1'].includes(item.id)) {
        await page.locator('.duel-stage').screenshot({path:path.join(out,`sample-pve-${item.id}.png`)});
        await page.setViewportSize({width:390,height:900});await seek(at);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
        await page.setViewportSize({width:1600,height:1000});await seek(at);
      }
    }
    await page.getByRole('button',{name:'跳过',exact:true}).click();
    await page.getByRole('button',{name:'整场重播',exact:true}).waitFor();
    await page.getByRole('button',{name:'整场重播',exact:true}).click();
    await page.getByRole('button',{name:'暂停',exact:true}).click();
    assert.equal(await canvas.count(),1);
    assert.deepEqual(errors,[]);assert.deepEqual(blocked,[]);
    console.log(JSON.stringify({ok:true,moves:fixtures.moves.length,effects:fixtures.effects.length,requests,errors,blocked}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
