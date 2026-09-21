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
    let requests=0;
    await page.route('**/api/battles/duel',route=>{requests++;return route.fulfill({json:{...current,snapshot}});});
    await page.goto('http://127.0.0.1:5175');
    await page.getByRole('button',{name:'对战',exact:true}).click();
    const mapped=await page.evaluate(async()=>Object.fromEntries(Object.entries((await import('/src/battle/martialVisuals.ts')).techniques).map(([id,moves])=>[id,Object.keys(moves)])));
    const slider=page.getByRole('slider',{name:'战斗进度'});
    const canvas=page.locator('canvas');
    const seek=async(t)=>{await slider.fill(String(t));await page.waitForTimeout(45);};
    const pixels=()=>canvas.evaluate(c=>c.toDataURL());
    let first=true;
    const load=async(battle)=>{
      current=battle;
      if(first) {await page.getByRole('button',{name:'开始试炼',exact:true}).click();first=false;}
      else {
        await page.getByRole('button',{name:'跳过',exact:true}).click();
        await page.getByRole('button',{name:'再战一场',exact:true}).click();
      }
      await page.getByRole('button',{name:'暂停',exact:true}).click();
    };
    const weapons=new Set();
    const frames=new Set();
    for(const item of fixtures.moves) {
      const battle=item.battle;
      const attack=battle.events.find(e=>e.type==='attack');
      assert(mapped[attack.martialArtId]?.includes(attack.move),`Explicit mapping: ${item.id}`);
      await load(battle);
      await seek(0);const idle=await pixels();
      await seek(attack.time+475);const strike=await pixels();
      assert.notEqual(idle,strike,`Animated move: ${item.id}`);
      frames.add(strike);
      const weapon=await canvas.getAttribute('data-weapon-a');
      if(!weapons.has(weapon)||attack.move.startsWith('绝')) {
        await page.locator('.duel-stage').screenshot({path:path.join(out,`martial-${item.id}.png`)});
      }
      weapons.add(weapon);
      const expected={a:battle.attacker.stats.hp,b:battle.defender.stats.hp};
      for(const e of battle.events) if(e.time<=attack.time+475 && e.hpAfter!==undefined) expected[e.target]=e.hpAfter;
      assert.deepEqual(await page.getByRole('progressbar',{name:/气血$/}).evaluateAll(es=>es.map(e=>+e.getAttribute('aria-valuenow'))),[expected.a,expected.b]);
      const before=await pixels();await page.waitForTimeout(20);assert.equal(await pixels(),before);
    }
    assert.equal(weapons.size,8,'All weapon silhouettes render, including the katana override');
    assert(frames.size>30,'Moves must be visibly varied, not renamed sword swings');
    for(const item of fixtures.effects) {
      await load(item.battle);await seek(item.time+240);
      if(['regeneration','vampirism','thorns','burst_heal','crisis_defense','battle_start_first_strike','low_hp_extra_action'].includes(item.id)) {
        const captions=await page.locator('.duel-specials').innerText();
        assert(captions.trim(),`Named special effect caption: ${item.id}`);
      }
      await page.locator('.duel-stage').screenshot({path:path.join(out,`effect-${item.id}.png`)});
      const original=await pixels();
      await seek(0);await seek(item.time+240);
      assert.equal(await pixels(),original,`Deterministic effect replay: ${item.id}`);
      if(item.id==='disarmed') {
        const e=item.battle.events.find(e=>e.status==='disarmed');
        const state=await page.evaluate(async({battle,time})=>(await import('/src/battle/replay.ts')).stateAt(battle,time),{battle:item.battle,time:item.time+240});
        assert.equal(state.weaponsReady[e.target],false);
      }
    }
    await page.setViewportSize({width:390,height:900});
    for(const type of ['staff','musical_instrument','hidden_weapon','leg']) {
      const item=fixtures.moves.find(i=>i.battle.attacker.martialArt.type===type);
      await load(item.battle);
      const attack=item.battle.events.find(e=>e.type==='attack');
      await seek(attack.time+350);
      await page.locator('.ink-duel').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(out,`mobile-${type}.png`),fullPage:true});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    }
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({moves:fixtures.moves.length,effects:fixtures.effects.length,weapons:[...weapons],uniqueFrames:frames.size,requests,errors}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
