const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1500,height:1000}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:5175/motion-preview.html');
    await page.getByRole('button',{name:'暂停',exact:true}).click();
    const arts=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../configs/martial_arts.json'),'utf8'));
    const result=await page.evaluate(async arts=>{
      const {poseAt}=await import('/src/battle/InkStage.tsx');
      const {drawCurvedFigure}=await import('/src/battle/curvedFigure.ts');
      const {weaponFor}=await import('/src/battle/martialVisuals.ts');
      const {stateAt}=await import('/src/battle/replay.ts');
      let frames=0,endpointError=0,weaponError=0,curves=0,pixels=0;
      const shots=[],weapons=new Set();
      const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
      for(const art of arts) for(const mode of ['legacy','current']) for(const side of ['a','b']) {
        const actor={name:'actor',stats:{hp:1000,spd:60},martialArt:art};
        const target=side==='a'?'b':'a';
        const base=[{type:'battle_start',time:0},{type:'turn_start',time:300,action:1,actor:side},
          {type:'attack',time:850,action:1,actor:side,target,martialArtId:art.id,move:art.moves[0].name,weaponType:art.type},
          {type:'damage',time:1250,action:1,actor:side,target,cause:'strike',amount:250,hpAfter:750,maxHp:1000},
          {type:'turn_end',time:2100,action:1},{type:'battle_end',time:4400}];
        for(const kind of ['idle','attack','dodge','disarmed','fallen','victory']) {
          const events=JSON.parse(JSON.stringify(base));let time=1250;
          if(kind==='idle') time=0;
          if(kind==='dodge'){events[2].actor=target;events[2].target=side;events[1].actor=target;events[3]={type:'dodge',time:1250,action:1,actor:target,target:side};time=1440;}
          if(kind==='disarmed'){events.push({type:'status_apply',time:1260,action:1,actor:target,target:side,status:'disarmed',duration:1});time=1320;}
          if(kind==='fallen'){events[3].target=side;events[3].hpAfter=0;events[3].amount=1000;time=1690;}
          if(kind==='victory'){events.push({type:'victory_start',time:2200,actor:side,victoryKind:'quick',victoryVariant:0});time=3600;}
          events.sort((a,b)=>a.time-b.time);
          const battle={attacker:actor,defender:{...actor,name:'opponent'},winner:kind==='victory'?'actor':null,events};
          const frame=poseAt(battle,side,time,1000,stateAt(battle,time).turn,mode),p=frame.pose.points;
          const original=JSON.stringify(frame);
          const canvas=document.createElement('canvas');canvas.width=1000;canvas.height=430;
          const ctx=canvas.getContext('2d'),calls=[],translations=[];
          const proxy=new Proxy(ctx,{get(target,key){
            const value=target[key];if(typeof value!=='function')return value;
            return (...args)=>{if(key==='quadraticCurveTo') calls.push(args);if(key==='translate')translations.push(args);return value.apply(target,args);};
          },set(target,key,value){target[key]=value;return true;}});
          drawCurvedFigure(proxy,500,side==='a'?1:-1,frame.pose,time,frame.weapon,1,frame.lift,frame.sheathed,art.id);
          if(calls.length<6) throw Error('All four limbs and both sashes must be curved');
          for(const [index,joint] of [[0,4],[1,8],[2,10],[3,6]]) endpointError=Math.max(endpointError,dist(calls[index].slice(2),p[joint]));
          if(!frame.sheathed) weaponError=Math.max(weaponError,dist(translations.at(-1),frame.weapon==='zither'?[5,-83]:p[6]));
          if(JSON.stringify(frame)!==original) throw Error('Renderer mutated the skeleton');
          const data=ctx.getImageData(0,0,1000,430).data;let filled=0;for(let i=3;i<data.length;i+=4) if(data[i]>20)filled++;
          if(filled<300)throw Error('Empty figure');pixels+=filled;frames++;curves+=calls.length;
          const weapon=weaponFor(actor);
          if(mode==='current' && side==='a' && (kind==='attack' && !weapons.has(weapon) || kind==='victory' && ['sword','zither'].includes(weapon))) {
            if(kind==='attack') weapons.add(weapon);
            shots.push({title:`${art.name} / ${kind}`,src:canvas.toDataURL()});
          }
        }
      }
      return {frames,endpointError,weaponError,curves,pixels,weapons:[...weapons],shots};
    },arts);
    assert.equal(result.endpointError,0);assert.equal(result.weaponError,0);assert.equal(result.weapons.length,8);
    const grid=await browser.newPage({viewport:{width:1600,height:1000}});
    await grid.setContent(`<meta charset="utf-8"><style>body{margin:0;background:#eeeee7;display:grid;grid-template-columns:repeat(4,1fr);font:16px sans-serif}section{min-width:0;border:1px solid #ccc}img{width:100%}h2{font-size:16px;margin:12px}</style>${result.shots.map(s=>`<section><h2>${s.title}</h2><img src="${s.src}"></section>`).join('')}`);
    await grid.screenshot({path:path.resolve(__dirname,'../../output/playwright/curved-weapon-families.png'),fullPage:true});
    const {shots,...metrics}=result;assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,...metrics,errors}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
