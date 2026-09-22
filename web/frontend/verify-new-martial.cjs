const assert=require('node:assert/strict');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:5175/motion-preview.html?art=sword_danyu');
    const pause=async()=>{const p=page.getByRole('button',{name:'暂停',exact:true});if(await p.count()) await p.click();};
    await pause();
    const metrics=await page.evaluate(async()=>{
      const {poseAt}=await import('/src/battle/InkStage.tsx');
      const {newMotionSamples,newMotionMoves,newMartialMotion,newMoveFor}=await import('/src/battle/newMartialMotion.ts');
      const {motionVariantFor}=await import('/src/battle/motionVariants.ts');
      const {drawNewMartialEffects}=await import('/src/battle/newMartialEffects.ts');
      const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
      let boneError=0,maxStep=0,mirrorError=0,lowest=0,top=430,worst=null,topWorst=null;
      const motionSignatures=new Set();
      for(const art of newMotionMoves) for(const missed of [false,true]) for(const width of [600,1000]) {
        motionSignatures.add(JSON.stringify([500,700,815,950,1080].map(t=>newMartialMotion({martialArtId:art.id,move:art.move},t,365))));
        const subject={name:'new',stats:{hp:1000,spd:60},martialArt:art};
        const other={name:'old',stats:{hp:1000,spd:60},martialArt:{id:'sword_huashan',type:'sword',name:'华山剑法'}};
        const make=side=>{
          const target=side==='a'?'b':'a',turn={type:'turn_start',time:300,action:1,actor:side};
          const attack={...turn,type:'attack',time:850,target,martialArtId:art.id,move:art.move,weaponType:art.type};
          return {attacker:side==='a'?subject:other,defender:side==='b'?subject:other,winner:null,events:[{type:'battle_start',time:0},turn,attack,
            missed?{type:'dodge',time:1250,action:1,actor:side,target}:{type:'damage',time:1250,action:1,actor:side,target,cause:'strike',amount:340,hpAfter:660,maxHp:1000},
            {type:'turn_end',time:2100,action:1},{type:'battle_end',time:2500}]};
        };
        const a=make('a'),b=make('b');let prev;
        for(const mode of ['legacy','current','mixed']) if(motionVariantFor(a,a.events[2],mode)!=='current') throw Error('New arts must not select legacy');
        for(let t=0;t<=2200;t+=4) {
          const f=poseAt(a,'a',t,width,t>=300?a.events[1]:undefined),mirror=poseAt(b,'b',t,width,t>=300?b.events[1]:undefined),p=f.pose.points;
          mirrorError=Math.max(mirrorError,Math.abs(f.x+mirror.x-width));
          for(const [i,j,len] of [[3,4,40],[5,6,40],[2,7,48],[7,8,48],[2,9,48],[9,10,48],[1,2,52]]) boneError=Math.max(boneError,Math.abs(dist(p[i],p[j])-len));
          for(const [s,i] of [[0,3],[1,5]]) boneError=Math.max(boneError,Math.abs(dist(f.pose.shoulders[s],p[i])-40));
          for(const i of [8,10]) lowest=Math.max(lowest,f.lift+p[i][1]);
          const blade=art.type==='blade'?[104,-23]:[99,0];
          const tipY=324+f.lift+p[6][1]+Math.sin(f.pose.sword)*blade[0]+Math.cos(f.pose.sword)*blade[1];
          if(tipY<top) {top=tipY;topWorst={art:art.id,move:art.move,t};}
          if(prev && t>=304 && t<2036) for(let i=0;i<p.length;i++) {
            const d=dist([f.x+p[i][0],f.lift+p[i][1]],[prev.x+prev.pose.points[i][0],prev.lift+prev.pose.points[i][1]]);
            if(d>maxStep){maxStep=d;worst={art:art.id,move:art.move,t,i};}
          }
          prev=f;
        }
      }
      const sample=t=>({hand:[250+t*.03,160],tip:[350+t*.03,190],root:[250,324]});
      const render=(hit,age)=>{
        const c=document.createElement('canvas');c.width=1000;c.height=430;
        drawNewMartialEffects(c.getContext('2d'),true,1100,sample,1,age,hit,.8,[700,230]);return c.toDataURL();
      };
      const samplePoses=newMotionSamples.map(s=>({art:s.id,apex:newMartialMotion({martialArtId:s.id,move:s.move},740,365).lift,
        contact:newMartialMotion({martialArtId:s.id,move:s.move},950,365).pose.sword}));
      const multistroke=[['sword_danyu','双燕分波',2],['sword_danyu','千翎竞发',3],['blade_jingchao','踏浪连环',2],['blade_jingchao','千涛叠岸',2]]
        .every(([id,move,count])=>newMoveFor({martialArtId:id,move}).strokes.length===count);
      return {boneError,maxStep,mirrorError,lowest,top,topWorst,worst,samplePoses,motions:motionSignatures.size,multistroke,hitChanges:render(true,150)!==render(false,150),missStable:render(false,150)===render(false,300)};
    });
    console.log(JSON.stringify(metrics));
    assert(metrics.boneError<1e-7 && metrics.mirrorError<1e-7);
    assert(metrics.maxStep<32,'No discontinuous whole-body pose');
    assert(metrics.lowest<1,'Feet must stay above ground');
    assert(metrics.top>10,'Weapon remains inside the canvas at the apex');
    assert(metrics.samplePoses[0].apex<-80 && metrics.samplePoses[1].apex===0);
    assert(metrics.hitChanges && metrics.missStable,'Contact particles require a true hit');
    assert.equal(metrics.motions,16,'Sixteen distinct authored whole-body motions');assert(metrics.multistroke);
    const options=await page.getByLabel('招式',{exact:true}).locator('option').evaluateAll(os=>os.map(o=>({value:o.value,name:o.textContent})));
    const shots=[];
    const seek=async t=>{await page.getByRole('slider',{name:'动作进度'}).fill(String(t));await page.waitForTimeout(45);};
    for(const option of options.filter(o=>/丹羽剑法|惊潮刀法/.test(o.name))) {
      await page.getByLabel('招式',{exact:true}).selectOption(option.value);await pause();
      for(const t of [700,1040,1250,1390,1750]) {
        await seek(t);
        const image=await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL());
        await seek(0);await seek(t);assert.equal(await page.locator('canvas').nth(1).evaluate(c=>c.toDataURL()),image);
        shots.push({name:option.name,t,src:(await page.locator('.preview-stages section').nth(1).screenshot()).toString('base64')});
      }
      for(const side of ['a','b']) for(const missed of [false,true]) {
        await page.getByLabel('出招方').selectOption(side);await page.getByLabel('闪避').setChecked(missed);await pause();await seek(1360);
        const pixels=await page.locator('canvas').nth(1).evaluate(c=>{
          const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4) if(d[i]>20)n++;return n;
        });assert(pixels>1000,'Nonblank canvas');
      }
      await page.getByLabel('出招方').selectOption('a');await page.getByLabel('闪避').setChecked(false);await pause();
    }
    for(const width of [1920,1280,768,390,320]) {
      await page.setViewportSize({width,height:1000});await seek(1250);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    }
    await page.screenshot({path:path.resolve(__dirname,'../../output/playwright/new-martial-mobile.png'),fullPage:true});
    const sheet=await browser.newPage({viewport:{width:2400,height:850}});
    await sheet.setContent(`<meta charset="utf-8"><style>body{margin:0;display:grid;grid-template-columns:repeat(5,1fr);font:16px sans-serif;background:#f4f4ee}section{min-width:0;border:1px solid #bbb}h2{font-size:16px;padding:8px}img{width:100%}</style>${shots.map(s=>`<section><h2>${s.name} / ${s.t} ms</h2><img src="data:image/png;base64,${s.src}"></section>`).join('')}`);
    await sheet.screenshot({path:path.resolve(__dirname,'../../output/playwright/new-martial-samples.png'),fullPage:true});
    for(let i=0;i<shots.length;i+=20) {
      await sheet.setContent(`<meta charset="utf-8"><style>body{margin:0;display:grid;grid-template-columns:repeat(5,1fr);font:16px sans-serif;background:#f4f4ee}section{min-width:0;border:1px solid #bbb}h2{font-size:16px;padding:8px}img{width:100%}</style>${shots.slice(i,i+20).map(s=>`<section><h2>${s.name} / ${s.t} ms</h2><img src="data:image/png;base64,${s.src}"></section>`).join('')}`);
      await sheet.screenshot({path:path.resolve(__dirname,`../../output/playwright/new-martial-group-${i/20+1}.png`),fullPage:true});
    }
    assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,moves:16,frames:shots.length,errors}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
