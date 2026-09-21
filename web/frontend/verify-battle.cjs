/* Run against Vite with a recorded engine fixture; never posts to the player database. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const out = path.resolve(__dirname, '../../output/playwright');
  const battle = JSON.parse(fs.readFileSync(path.join(out, 'battle-fixture.json'), 'utf8'));
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const snapshot = await (await page.request.get('http://127.0.0.1:5175/api/session/bootstrap')).json();
    let duelRequests = 0;
    await page.route('**/api/battles/duel', route => {
      duelRequests++;
      return route.fulfill({ json: { ...battle, snapshot } });
    });
    await page.goto('http://127.0.0.1:5175');
    await page.getByRole('button', { name: '对战', exact: true }).waitFor();
    console.log('Initial navigation:', await page.locator('nav').innerText());
    await page.getByRole('button', { name: '对战', exact: true }).click();
    await page.getByRole('button', { name: '开始试炼', exact: true }).click();
    await page.getByRole('button', { name: '暂停', exact: true }).click();
    const slider = page.getByRole('slider', { name: '战斗进度' });
    const time = () => slider.inputValue().then(Number);
    const seek = async value => {
      await slider.fill(String(value));
      await page.waitForTimeout(80);
    };
    const pixels = () => page.locator('canvas').evaluate(c => c.toDataURL());
    await seek(0);
    const initial = await pixels();
    const alphaPixels = await page.locator('canvas').evaluate(c => {
      const data=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
      let count=0;for(let i=3;i<data.length;i+=4) if(data[i]>100) count++;
      return count;
    });
    assert(alphaPixels>1000, 'Canvas must contain visible fighters');
    await page.screenshot({ path: path.join(out,'battle-desktop.png'), fullPage: true });
    const hit=battle.events.find(e=>e.cause==='strike');
    await seek(hit.time+40);
    assert.notEqual(await pixels(), initial, 'Fighters and effects must move');
    const expected = {a:battle.attacker.stats.hp,b:battle.defender.stats.hp};
    for(const e of battle.events) if(e.time<=hit.time+40 && e.hpAfter!==undefined) expected[e.target]=e.hpAfter;
    assert.deepEqual(await page.getByRole('progressbar',{name:/气血$/}).evaluateAll(els=>els.map(e=>Number(e.getAttribute('aria-valuenow')))), [expected.a,expected.b]);
    await page.locator('.duel-stage').screenshot({ path:path.join(out,'battle-hit.png') });
    const frozen = await pixels();
    const frozenTime = await time();
    await page.waitForTimeout(260);
    assert.equal(await time(), frozenTime, 'Pause freezes clock');
    assert.equal(await pixels(), frozen, 'Pause freezes particles and poses');
    await page.getByLabel('播放倍速').selectOption('2');
    await page.getByRole('button',{name:'继续',exact:true}).click();
    await page.waitForTimeout(420);
    await page.getByRole('button',{name:'暂停',exact:true}).click();
    assert((await time())-frozenTime>550, 'Double speed advances the shared clock');
    const dodge=battle.events.find(e=>e.type==='dodge');
    if(dodge) {
      await seek(dodge.time+60);
      await page.locator('.duel-stage').screenshot({path:path.join(out,'battle-dodge.png')});
    }
    await page.getByRole('button',{name:'跳过',exact:true}).click();
    const final=battle.events[battle.events.length-1];
    assert.equal(await time(), final.time);
    assert.deepEqual(await page.getByRole('progressbar',{name:/气血$/}).evaluateAll(els=>els.map(e=>Number(e.getAttribute('aria-valuenow')))),[final.final.a.hp,final.final.b.hp]);
    assert.equal(await page.locator('.duel-log p').count(),battle.logs.length);
    assert(await page.locator('.duel-result').isVisible());
    await page.screenshot({path:path.join(out,'battle-ended.png'),fullPage:true});
    await page.getByRole('button',{name:'重播',exact:true}).click();
    await page.getByRole('button',{name:'暂停',exact:true}).click();
    assert((await time())<1500, 'Replay resets to beginning');
    assert.equal(duelRequests,1,'Replay and seeking must not create new battles');
    await seek(hit.time+40);
    assert.equal(await pixels(),frozen,'Seeking to same time produces identical pixels');
    for(const width of [1440,390]) {
      await page.setViewportSize({width,height:900});
      await page.locator('.ink-duel').scrollIntoViewIfNeeded();
      await page.waitForTimeout(150);
      await page.screenshot({path:path.join(out,`battle-${width}.png`),fullPage:true});
      const bounds=await page.locator('.ink-duel').boundingBox();
      assert(bounds.x>=0 && bounds.x+bounds.width<=width+1,`Battle fits ${width}px viewport`);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
      assert(!overflow,`No horizontal overflow at ${width}px`);
    }
    await page.getByRole('button',{name:'重播',exact:true}).click();
    await page.locator('.duel-result').waitFor({state:'visible',timeout:40000});
    assert.equal(await time(),final.time,'Playback naturally reaches the final frame');
    assert.equal(duelRequests,1,'A complete replay does not record a second battle');
    assert.deepEqual(errors,[],'No runtime errors');
    console.log(JSON.stringify({ok:true,alphaPixels,duelRequests,actions:battle.state.actions,events:battle.events.length,errors}));
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
