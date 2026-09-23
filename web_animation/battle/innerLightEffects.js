import {qishangBody} from './qishangMotion.js';
import {drawTrigger,drawAura,drawFootwork} from './inkEffects.js';
import {drawCalligraphicFeather} from './holyMotion.js';
const innerIds=['evergreen_breath','iron_wall_art','blood_moon_skill','golden_wind_record','hunyuan_qigong','biyun_xinfa','xiantian_qigong','shenzhao_jing','jinzhong_zhao','jiayi_shengong','zixia_shengong','qiankun_danuoyi'];
const lightIds=['cloud_step','shadow_drift','earth_root','lightning_flash','phantom_lotus','swan_shadow','shadow_fragrance','wind_rider','star_shifter'];
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)},mix=(a,b,p)=>a+(b-a)*p,seed=n=>{const x=Math.sin(n*127.1)*43758.54;return x-Math.floor(x)};
function line(ctx,pts,c,w=1,a=1){ctx.globalAlpha=clamp(a);ctx.strokeStyle=c;ctx.lineWidth=w;ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke();}
function ellipse(ctx,x,y,rx,ry,c,w=1,a=1){ctx.globalAlpha=clamp(a);ctx.strokeStyle=c;ctx.lineWidth=w;ctx.beginPath();ctx.ellipse(x,y,Math.max(.1,rx),Math.max(.1,ry),0,0,Math.PI*2);ctx.stroke();}
function dot(ctx,x,y,r,c,a=1){ctx.globalAlpha=clamp(a);ctx.fillStyle=c;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();}
function shards(ctx,x,y,age,count=36){const p=clamp(age/1000),a=(1-p)*ease(age/65);for(let j=0;j<count;j++){const an=j*2.399,v=45+seed(j)*105,px=x+Math.cos(an)*v*p,py=y+Math.sin(an)*v*p+p*p*42,s=2+seed(j+20)*5;ctx.save();ctx.translate(px,py);ctx.rotate(an+p*4);ctx.globalAlpha=a;ctx.fillStyle=j%3?'#b89a51':'#f2d78b';ctx.beginPath();ctx.moveTo(-s,-s*.5);ctx.lineTo(s*.7,-s*.8);ctx.lineTo(s,s*.3);ctx.lineTo(-s*.4,s*.7);ctx.closePath();ctx.fill();line(ctx,[[-s,-s*.5],[s*.7,-s*.8]],'#fff0ba',.8,a);ctx.restore();if(j%2===0)line(ctx,[[px,py],[px+Math.cos(an)*13,py+Math.sin(an)*13]],'#dbc371',1,a*.7);}}
function leaf(ctx,x,y,s,angle,c,a){ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.globalAlpha=clamp(a);ctx.fillStyle=c;ctx.beginPath();ctx.moveTo(-s,0);ctx.quadraticCurveTo(0,-s*.6,s,0);ctx.quadraticCurveTo(0,s*.6,-s,0);ctx.fill();line(ctx,[[-s,0],[s,0]],'#e8dbac',.6,a*.7);ctx.restore();}
function curve(ctx,points,c,w,a){ctx.globalAlpha=clamp(a);ctx.strokeStyle=c;ctx.lineWidth=w;ctx.beginPath();ctx.moveTo(...points[0]);ctx.bezierCurveTo(...points[1],...points[2],...points[3]);ctx.stroke();}
function spiral(ctx,x,y,r,c,a,phase=0,flat=1){const pts=[];for(let j=0;j<=70;j++){const u=j/70,an=u*Math.PI*4+phase;pts.push([x+Math.cos(an)*r*u,y+Math.sin(an)*r*u*flat]);}line(ctx,pts,c,1.3,a);}
function body(ctx,f,fn){const b=qishangBody(f,f.dir);ctx.save();ctx.transform(...b.right,...b.down,...b.center);fn();ctx.restore();}
function motes(ctx,c,age,origin=[0,0],count=24,spread=65,up=false){const p=clamp(age/950);for(let j=0;j<count;j++){const a=j*2.399,r=spread*(.2+seed(j)*.8)*p,x=origin[0]+Math.cos(a)*r,y=origin[1]+(up?-p*(20+seed(j+11)*100):Math.sin(a)*r+p*p*20);dot(ctx,x,y,1+seed(j+31)*1.8,c,(1-p)*.8);}}
function internal(ctx,i,f,t,layers,weak,otherX){
 const age=t-900;if(age<0)return;
 const p=clamp(age/1150),open=ease(age/250),fade=1-ease((age-650)/600),persist=ease(age/250)*(1-ease((t-3100)/450));
 const c=['#588a50','#78867c','#a14854','#bf983b','#9e8e61','#51a298','#bca968','#e6bd63','#c29c45','#b56344','#9568a4','#668b99'][i];
 body(ctx,f,()=>{
  if(i===0){for(let j=0;j<30;j++){const q=clamp((age-j*17)/1020),a=j*2.399,x=Math.cos(a)*(53-25*q),y=64-q*145;curve(ctx,[[x,64],[x-17,23],[x+18,-10],[x,y]],c,1.2,fade*.22);leaf(ctx,x,y,6+seed(j)*5,a-q*2,c,fade*.85);}motes(ctx,c,age,[0,35],40,65,true);}
  if(i===1){for(let j=0;j<7;j++){const x=(j%3-1)*24,y=Math.floor(j/3)*27-32;ctx.globalAlpha=fade*.26;ctx.fillStyle=c;ctx.beginPath();ctx.moveTo(x-13,y-16);ctx.lineTo(x+13,y-16);ctx.lineTo(x+16,y+9);ctx.lineTo(x,y+20);ctx.lineTo(x-16,y+9);ctx.closePath();ctx.fill();ctx.strokeStyle='#c8d2bf';ctx.lineWidth=1.5;ctx.stroke();line(ctx,[[x,y-12],[x,y+11]],'#e5e0be',1,fade*.8);}motes(ctx,'#9d9b74',age,[30,0],30,80);}
  if(i===2){ctx.save();ctx.beginPath();ctx.ellipse(0,0,23,43,0,0,Math.PI*2);ctx.clip();for(let j=0;j<13;j++){const pts=[];for(let k=0;k<=16;k++){const u=k/16;pts.push([(j-6)*3.5+Math.sin(u*15+j)*3,(u-.5)*90]);}line(ctx,pts,j%3?'#8e263b':'#cd4d58',j%3?1:1.8,fade*(.55+Math.sin(age*.016)*.15));}ctx.restore();for(let j=0;j<10;j++)dot(ctx,(seed(j)-.5)*28,(seed(j+40)-.5)*70,1.5,'#c23d50',fade*.85);}
  if(i===3){for(let j=0;j<13;j++){const a=j*2.399+age*.003,r=16+seed(j)*25;leaf(ctx,Math.cos(a)*r,Math.sin(a)*r,5+seed(j+20)*4,a,c,fade*.8);}spiral(ctx,0,0,45,c,fade*.5,age*.005);}
  if(i===4){for(let j=0;j<5;j++){const squeeze=1-Math.sin(p*Math.PI)*.25;ellipse(ctx,0,0,(28+j*9)*open*squeeze,(40+j*6)*open,c,j===0?4:1,fade*(.5-j*.07));}motes(ctx,c,age,[25,0],24,75);}
  if(i===5){const linger=1-ease((age-1650)/950);for(let j=0;j<6;j++){const y=45-j*19-open*17;curve(ctx,[[-55,y],[-35,y-24],[18,y+22],[60,y-12]],c,7-j*.7,linger*.16);curve(ctx,[[-55,y],[-35,y-24],[18,y+22],[60,y-12]],'#9dccb1',1.5,linger*.75);}for(let j=0;j<46;j++){const q=((age+j*41)%1500)/1500,a=j*2.399,r=(1-q)*82;dot(ctx,Math.cos(a)*r,Math.sin(a)*r,1.8,c,linger*.8*ease(age/180));}ellipse(ctx,0,0,35*open,63*open,c,1.3,linger*.4);}
  if(i===6){for(let j=0;j<3;j++)ellipse(ctx,0,2,33+j*7,66+j*4,c,j?1:2,persist*(.25+j*.1));for(let j=0;j<12;j++){const a=j*Math.PI/6+age*.0006;dot(ctx,Math.cos(a)*42,Math.sin(a)*70,1.4,'#e6d49a',persist*.75);}motes(ctx,c,age,[0,20],25,50,true);}
  if(i===8){const color=weak?'#a96044':c,shake=Math.sin(age*.05)*(1-p)*3;ctx.translate(shake,0);for(let j=0;j<3;j++){const w=43+j*3;curve(ctx,[[-w,72],[-w+14,15],[-43,-62],[0,-68-j*3]],color,2,fade*.8);curve(ctx,[[0,-68-j*3],[43,-62],[w-14,15],[w,72]],color,2,fade*.8);ellipse(ctx,0,72,w,8,color,2,fade*.8);}for(let j=0;j<4;j++)ellipse(ctx,0,76+j*3,45+open*(j+1)*13,7+j*2,c,1,fade*.4);if(weak){line(ctx,[[-4,9],[10,19],[-5,29],[9,39]],'#a73d2f',3,fade);motes(ctx,'#b88945',age,[0,24],26,60);}}
  if(i===11){for(let j=0;j<2;j++){const a=age*.007+j*Math.PI;const pts=[];for(let n=0;n<=42;n++){const an=a+n/42*Math.PI*1.5,r=34+n*.25;pts.push([Math.cos(an)*r,Math.sin(an)*r]);}line(ctx,pts,j?'#c1cbb9':c,j?2:4,fade*.8);}motes(ctx,c,age,[25,-5],16,45);}
 });
 // Replenishment travels back to its owner; counterforce travels toward the attacker.
 if(i===0){ellipse(ctx,f.x,326,35+open*28,7+open*4,c,1.8,fade*.75);ellipse(ctx,f.x,327,49+open*30,9+open*4,c,.9,fade*.35);}
 if(i===1||i===8){shards(ctx,f.x+27,239,age,i===8?48:38);}
 if(i===2&&age<1150){for(let j=0;j<33;j++){const local=age-j*15;if(local<0)continue;const scatter=clamp(local/180),q=clamp((local-140)/650),a=j*2.399,r=15+j%5*6,sx=otherX+Math.cos(a)*r*scatter,sy=239+Math.sin(a)*r*scatter;ctx.globalAlpha=fade*(1-q*.65)*.85;ctx.fillStyle=j%3?'#922b42':'#c34c59';ctx.beginPath();ctx.ellipse(mix(sx,f.x,q),mix(sy,248,q)-Math.sin(q*Math.PI)*(15+j%4*8),2+j%3,1.2+j%2,a,0,Math.PI*2);ctx.fill();}}
 if(i===3&&age<1150){for(let j=0;j<18;j++){const q=clamp((age-j*18-90)/650);leaf(ctx,mix(otherX,f.x,q),230-Math.sin(q*Math.PI)*(18+j%4*11),3+j%3,q*5+j,c,fade*.8);}}
 if((i===4||i===11)&&age<1400){for(let j=0;j<6;j++){const local=age-75*j;if(local<0||local>850)continue;const q=local/850,r=i===11?10+(j%3)*10+q*12:22+q*21,x=mix(f.x+20,otherX,ease(q)),a=(1-q)*.75;ellipse(ctx,x,246,r,r,i===11&&j%2?'#a7b4a7':c,2.3,a);ellipse(ctx,x,246,r+4,r+4,c,.7,a*.5);}}
}
function foot(ctx,i,x,y,a,t,layers){
 if(i===0){for(let j=0;j<3;j++)curve(ctx,[[x-32,y+j*3],[x-20,y-14-j*4],[x+12,y+12],[x+33,y-2]],'#7d9b90',2,a*.45);}
 if(i===1){curve(ctx,[[x-48,y-14],[x-31,y-36],[x-16,y+6],[x+12,y]],'#425d61',5,a*.3);}
 if(i===2){for(let j=0;j<10;j++){const px=x+(seed(j)-.5)*65,py=y-seed(j+10)*11;leaf(ctx,px,py,2+seed(j)*4,j,'#86775c',a*.7);}ellipse(ctx,x,y,35,5,'#9c9179',1,a*.3);}
 if(i===3){const bolt=[[x-62,y-2],[x-40,y-18],[x-28,y],[x-8,y-19],[x+17,y-5]];line(ctx,bolt,'#7655c9',5,a*.2);line(ctx,bolt,'#7163d9',2.3,a);line(ctx,bolt,'#c8d9ff',.8,a);line(ctx,[[x-28,y],[x-36,y-24],[x-21,y-31]],'#7f85eb',1,a*.75);for(let j=0;j<8;j++)dot(ctx,x-j*8,y-4-seed(j)*24,1.4,'#8e9bf1',a);}
 if(i===4){for(let j=0;j<7;j++){const an=j*Math.PI/3.5;leaf(ctx,x+Math.cos(an)*12,y+Math.sin(an)*5,13,an,'#779f8a',a*.6);}ellipse(ctx,x,y+3,31,6,'#8eb1a4',1,a*.6);ellipse(ctx,x,y+3,43,9,'#9fbbae',.7,a*.4);}
 if(i===5){drawCalligraphicFeather(ctx,x,y,40,3.35,.12,'#527f78','#acbba0',a*.65);}
 if(i===6){for(let j=0;j<4;j++)leaf(ctx,x+(j-2)*10,y-8-seed(j)*13,5,j+t*.001,'#846b8e',a*.65);curve(ctx,[[x-30,y],[x-23,y-20],[x+18,y+9],[x+24,y-6]],'#695c78',7,a*.14);}
 if(i===7){for(let j=0;j<layers+2;j++)curve(ctx,[[x-90-j*7,y],[x-70,y-75-j*12],[x+33,y-63-j*8],[x+38,y-5]],'#6c9d92',1.6,a*(.5-j*.04));}
 if(i===8){dot(ctx,x,y,8,'#bba0d8',a*.16);line(ctx,[[x-9,y],[x+9,y]],'#9b77bd',1.8,a);line(ctx,[[x,y-12],[x,y+12]],'#9b77bd',1.8,a);line(ctx,[[x-4,y-4],[x+4,y+4]],'#c0a6dc',1,a);line(ctx,[[x-4,y+4],[x+4,y-4]],'#c0a6dc',1,a);dot(ctx,x,y,2.4,'#f1e6ff',a);}
}

// Only real replay events emit bursts. Legacy revival, deferred damage and purple aura stay intact.
export function drawArtTrigger(ctx,event,frame,dir,other,age){
 const id=event.sourceSkill?.id,effect=event.effect||event.cause||event.status,i=innerIds.indexOf(id),layers=Math.max(1,Math.min(5,event.stacks||1));
 if(age<0)return;
 ctx.save();
 const eligible=event.type==='heal'||event.type==='guard'||['thorns','part_counter','crisis_defense'].includes(effect);
 if(i>=0&&![7,9,10].includes(i)&&eligible){
  if(age<=(i===5?2600:1400)){
   // Mirror the entire local scene while retaining the live torso orientation.
   ctx.translate(frame.x,0);ctx.scale(dir,1);
   const local={...frame,x:0,dir:1,pose:{...frame.pose,lean:frame.pose.lean*dir,roll:(frame.pose.roll||0)*dir}};
   internal(ctx,i,local,age+900,layers,(event.multiplier||1)>1,(other.x-frame.x)*dir);
  }
 }else{
  if(!((id==='wind_rider'&&effect==='action_spd_stack')||(id==='star_shifter'&&['dodge_damage_boost','next_attack_bonus'].includes(effect))))drawTrigger(ctx,event,frame.x,other.x,age);
  const fade=Math.sin(clamp(age/1150)*Math.PI),x=frame.x,y=324+(frame.lift||0);
  if(id==='swan_shadow'&&effect==='battle_start_first_strike'&&age<1150){for(const s of [-1,1])for(let j=0;j<7;j++)drawCalligraphicFeather(ctx,x,y-96,44+j*7,Math.PI+s*(.2+j*.14),s*.16,'#587d78','#bcc9b2',fade*.65);}
  if(id==='shadow_fragrance'&&effect==='low_hp_extra_action'&&age<1150){for(let j=0;j<18;j++){const an=j*2.399,r=45*fade;leaf(ctx,x+Math.cos(an)*r,y-84+Math.sin(an)*r,5,an+age*.003,'#826789',fade*.7);}}
  if(id==='wind_rider'&&effect==='action_spd_stack'&&age<1150)tornado(ctx,x,y,age,layers,fade);
  if(id==='star_shifter'&&['dodge_damage_boost','next_attack_bonus'].includes(effect)&&age<1150){const p=ease(age/1150),pts=[];for(let j=0;j<18;j++){const a=j*2.399,r=(1-p)*(28+seed(j)*65),sx=x+Math.cos(a)*r,sy=y-80+Math.sin(a)*r;pts.push([sx,sy]);foot(ctx,8,sx,sy,fade*(j%3===0?.95:.6),age,layers);}line(ctx,pts,'#a48bc1',.7,fade*.25);for(let j=0;j<24;j++)dot(ctx,x+(seed(j)-.5)*150*(1-p),y-80+(seed(j+40)-.5)*130*(1-p),1+seed(j)*1.3,'#b69ace',fade*.7);}
 }
 ctx.restore();
}
function tornado(ctx,x,y,t,layers,a){const height=105+layers*15;for(let j=0;j<layers+3;j++){const pts=[];for(let n=0;n<=90;n++){const u=n/90,ang=u*Math.PI*6+t*.007+j*.8,r=22+u*(35+layers*5);pts.push([x+Math.cos(ang)*r,y-u*height+Math.sin(ang)*8]);}line(ctx,pts,'#75a396',j%2?1:2,a*.28);}for(let j=0;j<20;j++){const u=(t*.0006+j/20)%1,ang=u*15+t*.003;dot(ctx,x+Math.cos(ang)*(25+u*50),y-u*height,1.2,'#a7c8ad',a*.65);}}
export function drawArtFootwork(ctx,id,x,dir,phase,time,trace=[],layers=1){
 const i=lightIds.indexOf(id);if(i<0){drawFootwork(ctx,id,x,dir,phase,time,trace);return;}
 ctx.save();ctx.translate(x,0);ctx.scale(dir,1);
 for(let j=trace.length-1;j>=0;j--){const p=trace[j];foot(ctx,i,(p.x-x)*dir,p.y+3,phase*(1-j/(trace.length+1)),time,layers);}
 ctx.restore();
}
export function drawArtAura(ctx,frame,dir,states,time,stacks){
 drawAura(ctx,frame.x,324+frame.lift,states.filter(s=>s!=='crisis_defense'),time,stacks);
 if(states.includes('crisis_defense')){ctx.save();body(ctx,{...frame,dir},()=>{for(let j=0;j<3;j++)ellipse(ctx,0,2,33+j*7,66+j*4,'#bca968',j?1:2,.25+j*.1);for(let j=0;j<12;j++){const a=j*Math.PI/6+time*.0006;dot(ctx,Math.cos(a)*42,Math.sin(a)*70,1.4,'#e6d49a',.75);}});ctx.restore();}
}
