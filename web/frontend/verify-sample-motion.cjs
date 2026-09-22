const assert=require('node:assert/strict');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1600,height:1000}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:5175/motion-preview.html');
    await page.getByRole('button',{name:'暂停',exact:true}).click();
    const metrics=await page.evaluate(async()=>{
      const {sampleMotion,walkContacts,rigLengths}=await import('/src/battle/sampleMotion.ts');
      const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
      let boneError=0,gripError=0,jump=0,underground=0;
      const jumps=[];
      for(const kind of ['sword','spear','kick']) for(const travel of [108,153,224,320,365,436]) for(const missed of [false,true]) {
        let previous;
        for(let t=0;t<=1730;t++) {
          const frame=sampleMotion(kind,t,travel,missed),p=frame.pose.points;
          for(const [a,b,len] of [[3,4,rigLengths.arm],[5,6,rigLengths.arm],[2,7,48],[7,8,48],[2,9,48],[9,10,48],[1,2,52]]) boneError=Math.max(boneError,Math.abs(distance(p[a],p[b])-len));
          for(const [i,elbow] of [[0,3],[1,5]]) boneError=Math.max(boneError,Math.abs(distance(frame.pose.shoulders[i],p[elbow])-rigLengths.arm));
          if(kind==='spear') {
            const grip=[p[6][0]-rigLengths.grip*Math.cos(frame.pose.sword),p[6][1]-rigLengths.grip*Math.sin(frame.pose.sword)];
            gripError=Math.max(gripError,distance(grip,p[4]));
          }
          underground=Math.max(underground,p[8][1]+frame.lift,p[10][1]+frame.lift);
          if(previous) for(let i=0;i<p.length;i++) {
            const delta=distance([frame.x+p[i][0],frame.lift+p[i][1]],[previous.x+previous.pose.points[i][0],previous.lift+previous.pose.points[i][1]]);
            if(delta>jump) {jump=delta;jumps.push({kind,travel,missed,t,delta,joint:i});}
          }
          previous=frame;
        }
      }
      const planted=[.03,.1].map(p=>walkContacts(p,320).feet[1]);
      const runHeight=['sword','spear','kick'].map(kind=>-sampleMotion(kind,310,320).pose.points[2][1]);
      const airborne=['sword','spear','kick'].map(kind=>sampleMotion(kind,1450,320).lift);
      const blink=[520,590,640,750].map(t=>sampleMotion('spear',t,320).opacity);
      const kickApex=sampleMotion('kick',920,320).lift;
      const openRun=['sword','kick'].map(kind=>{
        const p=sampleMotion(kind,310,320).pose.points;
        return p[6][0]-p[4][0];
      });
      const maxStride=['sword','spear','kick'].map(kind=>Math.max(...Array.from({length:250},(_,i)=>{
        const p=sampleMotion(kind,190+i,320).pose.points;
        return Math.abs(p[10][0]-p[8][0]);
      })));
      const thrusts=['sword','spear'].map(kind=>{
        const start=sampleMotion(kind,800,320),end=sampleMotion(kind,950,320),length=kind==='sword'?99:140;
        const tip=f=>f.x+f.pose.points[6][0]+Math.cos(f.pose.sword)*length;
        return {distance:tip(end)-tip(start),arm:distance(end.pose.shoulders[1],end.pose.points[6])};
      });
      return {boneError,gripError,jump,underground,jumps:jumps.slice(-5),planted,runHeight,airborne,blink,kickApex,openRun,maxStride,thrusts};
    });
    console.log(JSON.stringify(metrics));
    assert(metrics.boneError<1e-7,'Bones retain fixed length');
    assert(metrics.gripError<1e-7,'Both spear hands stay on the shaft');
    assert(metrics.underground<.01,'Feet never penetrate the floor');
    assert(metrics.jump<8,'No single-frame pose jumps');
    assert.deepEqual(metrics.planted[0],metrics.planted[1]);
    assert(metrics.runHeight.every(height=>height>=80),'Running pelvis stays high instead of crouching');
    assert(metrics.airborne.every(lift=>lift<-45),'All recoveries include a real backward leap');
    assert.deepEqual(metrics.blink,[1,0,0,1],'Spear vanishes in flight and reappears before contact');
    assert(metrics.kickApex<-55,'Kick has a clear airborne apex');
    assert(metrics.openRun.every(span=>span>90),'Hands remain separated during the run');
    assert(metrics.maxStride.every(span=>span>105),'Each approach includes a wide split stride');
    assert(metrics.thrusts[0].distance>180 && metrics.thrusts[1].distance>130,'Sword and spear have a long forward thrust');
    assert(metrics.thrusts.every(t=>t.arm>73),'Thrust extends the arm instead of stopping at the chest');
    const slider=page.getByRole('slider',{name:'动作进度'});
    const seek=async time=>{await slider.fill(String(time));await page.waitForTimeout(35);};
    const frames=[];
    for(let move=0;move<3;move++) {
      await page.getByLabel('招式',{exact:true}).selectOption(String(move));
      const pause=page.getByRole('button',{name:'暂停',exact:true});if(await pause.count()) await pause.click();
      const images=[];
      for(const t of [600,780,925,1025,1250,1710]) {
        await seek(t);
        const before=await page.locator('canvas').first().evaluate(c=>c.toDataURL());
        await seek(0);await seek(t);
        assert.equal(await page.locator('canvas').first().evaluate(c=>c.toDataURL()),before,'Seek is deterministic');
        images.push((await page.locator('.preview-stages section').first().screenshot()).toString('base64'));
      }
      frames.push({move,images});
      await seek(1250);
      assert.notEqual(await page.locator('canvas').nth(0).evaluate(c=>c.toDataURL()),await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL()));
      if(move===0) {
        await seek(1320);
        const blue=await page.locator('canvas').nth(1).evaluate(c=>{
          const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
          let n=0;for(let i=0;i<d.length;i+=4) if(d[i+3]>50 && d[i+2]-d[i]>20 && d[i+1]>d[i]) n++;
          return n;
        });
        assert(blue>80,'Cold Branch Snow includes visible blue-white sword energy');
        await page.locator('.preview-stages').screenshot({path:path.resolve(__dirname,'../../output/playwright/motion-snow-thrust.png')});
      }
    }
    for(const side of ['a','b']) for(const missed of [true,false]) {
      await page.getByLabel('出招方').selectOption(side);
      await page.getByLabel('闪避').setChecked(missed);
      const pause=page.getByRole('button',{name:'暂停',exact:true});if(await pause.count()) await pause.click();
      for(const width of [1600,768,390,320]) {
        await page.setViewportSize({width,height:1000});await seek(1250);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
        assert(await page.locator('canvas').first().evaluate(c=>{
          const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
          let n=0;for(let i=3;i<d.length;i+=4) if(d[i]>100) n++;return n>150;
        }),'Canvas renders nonblank figures');
      }
    }
    await page.screenshot({path:path.resolve(__dirname,'../../output/playwright/motion-sample-mobile.png'),fullPage:true});
    await page.setViewportSize({width:1600,height:1000});
    await page.getByRole('button',{name:'重播',exact:true}).click();
    await page.getByLabel('倍速').selectOption('2');
    await page.waitForTimeout(1800);
    assert.equal(Number(await slider.inputValue()),2500,'Playback reaches the last frame');
    assert.equal(await page.getByRole('button',{name:'播放',exact:true}).count(),1);
    const grid=await browser.newPage({viewport:{width:1800,height:1400}});
    await grid.setContent(`<html><head><style>body{margin:0;background:#fff;font:16px sans-serif}section{display:grid;grid-template-columns:repeat(3,1fr)}h2{font-size:16px;margin:12px}img{width:100%;display:block}</style></head><body>${frames.map(row=>`<h2>${['Sword','Spear','Kick'][row.move]}: 300 / 480 / 625 / 725 / 950 / 1410 ms</h2><section>${row.images.map(src=>`<img src="data:image/png;base64,${src}">`).join('')}</section>`).join('')}</body></html>`);
    await grid.screenshot({path:path.resolve(__dirname,'../../output/playwright/motion-samples.png'),fullPage:true});
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,frames:18,viewports:4,errors}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
