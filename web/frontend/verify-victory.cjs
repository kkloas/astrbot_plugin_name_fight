const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const out=path.resolve(__dirname,'../../output/playwright');
  const fixtures=JSON.parse(fs.readFileSync(path.join(out,'martial-fixtures.json'),'utf8'));
  const base=fixtures.moves.find(i=>i.id==='sword_ittoryu-7').battle;
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1920,height:1080}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    const snapshot=await(await page.request.get('http://127.0.0.1:5175/api/session/bootstrap')).json();
    let current=base;
    await page.route('**/api/battles/duel',route=>route.fulfill({json:{...current,snapshot}}));
    await page.goto('http://127.0.0.1:5175');await page.getByRole('button',{name:'对战',exact:true}).click();
    const slider=page.getByRole('slider',{name:'战斗进度'});
    const canvas=page.locator('canvas');
    const seek=async t=>{await slider.fill(String(t));await page.waitForTimeout(50);};
    let first=true,frames=0;const images=[];
    for(const kind of ['quick','dominant','standard','clutch','judged','draw']) {
      const distinct=new Set();
      for(let variant=0;variant<3;variant++) {
        // Component coverage for all cosmetic choices. No request reaches the player DB.
        current=structuredClone(base);
        const victory=current.events.find(e=>e.type==='victory_start');
        Object.assign(victory,{victoryKind:kind,victoryVariant:variant,actor:kind==='draw'?undefined:'a'});
        if(first) {await page.getByRole('button',{name:'开始试炼',exact:true}).click();first=false;}
        else {await page.getByRole('button',{name:'跳过',exact:true}).click();await page.getByRole('button',{name:'再战一场',exact:true}).click();}
        await page.getByRole('button',{name:'暂停',exact:true}).click();
        await seek(victory.time);const initial=await canvas.evaluate(c=>c.toDataURL());
        await seek(victory.time+1150);const pose=await canvas.evaluate(c=>c.toDataURL());
        assert.notEqual(pose,initial,kind+' moves through a victory sequence');
        distinct.add(pose);frames++;
        await seek(0);await seek(victory.time+1150);assert.equal(await canvas.evaluate(c=>c.toDataURL()),pose);
        const image=await page.locator('.duel-arena').screenshot();
        images.push({label:kind+' '+variant,src:image.toString('base64')});
      }
      assert.equal(distinct.size,3,kind+' has three different presentations');
    }
    const sheet=await browser.newPage({viewport:{width:1500,height:1500}});
    await sheet.setContent(`<style>body{margin:0;display:grid;grid-template-columns:repeat(3,1fr);font:14px sans-serif}img{width:100%;display:block}p{margin:6px}</style>${images.map(i=>`<section><p>${i.label}</p><img src="data:image/png;base64,${i.src}"></section>`).join('')}`);
    await sheet.screenshot({path:path.join(out,'victory-variants.png'),fullPage:true});
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,victoryFrames:frames,errors}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
