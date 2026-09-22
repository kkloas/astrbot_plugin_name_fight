const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1600,height:1000}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:5175/motion-preview.html');
    await page.getByRole('button',{name:'暂停',exact:true}).click();
    const config=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../configs/martial_arts.json'),'utf8'));
    const metrics=await page.evaluate(async config=>{
      const {moveProfiles}=await import('/src/battle/moveProfiles.ts');
      const {moveMotion}=await import('/src/battle/moveMotion.ts');
      const {weaponFor}=await import('/src/battle/martialVisuals.ts');
      const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
      let boneError=0,gripError=0,jump=0,underground=0,tipUnderground=0,worst=null;
      const coverage=[],signatures=new Set();
      for(const [id,profiles] of Object.entries(moveProfiles)) {
        const art=(Array.isArray(config)?config:config.martial_arts).find(a=>a.id===id);
        const weapon=weaponFor({martialArt:art});
        for(const name of Object.keys(profiles)) {
          coverage.push(`${id}/${name}`);
          const event={martialArtId:id,move:name,weaponType:art.type};
          const signature=[];
          for(const travel of [108,320,436]) {
            let previous;
            for(let t=0;t<=1730;t+=2) {
              const frame=moveMotion(event,t,travel,weapon),p=frame.pose.points;
              for(const [a,b,len] of [[3,4,40],[5,6,40],[2,7,48],[7,8,48],[2,9,48],[9,10,48],[1,2,52]]) boneError=Math.max(boneError,Math.abs(distance(p[a],p[b])-len));
              for(const [i,j] of [[0,3],[1,5]]) boneError=Math.max(boneError,Math.abs(distance(frame.pose.shoulders[i],p[j])-40));
              if(weapon==='spear') gripError=Math.max(gripError,distance([p[6][0]-68*Math.cos(frame.pose.sword),p[6][1]-68*Math.sin(frame.pose.sword)],p[4]));
              underground=Math.max(underground,p[8][1]+frame.lift,p[10][1]+frame.lift);
              const length=({sword:99,blade:107,katana:112,spear:140,brush:45})[weapon];
              if(length) tipUnderground=Math.max(tipUnderground,frame.lift+p[6][1]+Math.sin(frame.pose.sword)*length);
              if(previous) for(let i=0;i<p.length;i++) {
                const d=distance([frame.x+p[i][0],frame.lift+p[i][1]],[previous.x+previous.pose.points[i][0],previous.lift+previous.pose.points[i][1]]);
                if(d>jump) {jump=d;worst={id,name,t,joint:i,d};}
              }
              if(travel===320 && [600,800,950,1100].includes(t)) signature.push(frame);
              previous=frame;
            }
          }
          signatures.add(JSON.stringify(signature));
        }
      }
      const arts=Array.isArray(config)?config:config.martial_arts;
      return {boneError,gripError,jump,underground,tipUnderground,worst,coverage,unique:signatures.size,configKeys:arts.flatMap(a=>a.moves.map(m=>`${a.id}/${m.name}`))};
    },config);
    console.log(JSON.stringify(metrics));
    assert.deepEqual([...metrics.coverage].sort(),[...metrics.configKeys].sort());
    assert(metrics.boneError<1e-7,'Fixed bone lengths');
    assert(metrics.gripError<.05,'Both spear hands share one shaft');
    assert(metrics.underground<.01,'Feet above ground');
    assert(metrics.tipUnderground<1,'Weapon tips above ground');
    assert(metrics.jump<16,'Continuous poses at 2ms samples');
    assert(metrics.unique>=60,'Named move motion variants');
    const select=page.getByLabel('招式',{exact:true});
    const options=await select.locator('option').evaluateAll(os=>os.map(o=>({value:o.value,name:o.textContent})));
    assert.equal(options.length,70);
    const seek=async t=>{await page.getByRole('slider',{name:'动作进度'}).fill(String(t));await page.waitForTimeout(35);};
    const frames=[];
    for(const option of options) {
      await select.selectOption(option.value);
      const pause=page.getByRole('button',{name:'暂停',exact:true});if(await pause.count()) await pause.click();
      await seek(1250);
      const first=await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL());
      await seek(0);await seek(1250);
      assert.equal(await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL()),first,'Deterministic move effects');
      assert.notEqual(first,await page.locator('canvas').first().evaluate(c=>c.toDataURL()),'Effects visible');
      if(/回风斩|白虹贯日|破云见空|蛟龙出水|断岳震|扫叶势|铁画银钩|一之太刀|暴雨梨花$|广陵绝响/.test(option.name)) {
        frames.push({name:option.name,src:(await page.locator('.preview-stages section').nth(1).screenshot()).toString('base64')});
      }
    }
    for(const width of [768,390,320]) {
      await page.setViewportSize({width,height:1000});
      await page.getByLabel('出招方').selectOption('b');
      await page.getByLabel('闪避').setChecked(true);
      const pause=page.getByRole('button',{name:'暂停',exact:true});if(await pause.count()) await pause.click();
      await seek(1250);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    }
    const grid=await browser.newPage({viewport:{width:1600,height:1000}});
    await grid.setContent(`<html><head><meta charset="utf-8"><style>body{margin:0;background:white;font:18px sans-serif;display:grid;grid-template-columns:1fr 1fr}section{min-width:0}h2{margin:10px;font-size:18px}img{width:100%}</style></head><body>${frames.map(f=>`<section><h2>${f.name}</h2><img src="data:image/png;base64,${f.src}"></section>`).join('')}</body></html>`);
    await grid.screenshot({path:path.resolve(__dirname,'../../output/playwright/move-profiles.png'),fullPage:true});
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,moves:options.length,errors}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
