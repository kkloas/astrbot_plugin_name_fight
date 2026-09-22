import { twoBone } from './sampleMotion.js';
export const names=['举重若轻','大巧不工','铁锁横江','拍击','顺水推舟','泰山压顶','横扫千军','绝技·破天'];
export const notes=['单手提剑 / 缓进重压 / 无锋撞击','竖剑如盾 / 沉肩踏撞 / 正面压垮','横剑封路 / 定势截击 / 短促横推','侧肩高蓄 / 宽面斜拍 / 单侧飞岩','蓄步前送 / 人剑一体 / 攻城撞击','双手举剑 / 腾跃砸落 / 山崩裂地','拧腰蓄势 / 扇形横斩 / 罡气撕风','高空蓄重 / 黑色陨星 / 破天轰落'];
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>{x=clamp(x);return x*x*(3-2*x)};
const mix=(a,b,u)=>a+(b-a)*u;
const k=(t,x,h,lean,g,angle,lift=0)=>({t,x,h,lean,g,angle,lift});
const idle=t=>k(t,0,72,-8,[33,-87],.38);
export function heavyMotion(event,time,travel){
 const index=names.indexOf(event.move);if(index<0)return;
 if(time>700&&time<950)time=700+250*Math.pow((time-700)/250,1.65);
 const near=Math.max(0,travel-18),slam=travel+56;
 let keys;
 switch(index){
 case 0:keys=[idle(0),k(410,0,69,-12,[18,-72],.56),k(660,near*.3,70,2,[42,-95],.03),k(845,near*.76,68,15,[61,-97],.08),k(950,near,64,25,[74,-99],.08),k(1120,near,62,23,[69,-96],.1),k(1390,near*.57,66,-4,[39,-85],.34),idle(1700)];break;
 case 1:keys=[idle(0),k(430,-12,50,-18,[25,-61],-1.54),k(710,near*.4,49,12,[42,-57],-1.54),k(850,near*.77,49,24,[59,-56],-1.53),k(950,near+106,48,29,[66,-57],-1.52),k(1140,near+106,44,25,[63,-56],-1.52),k(1370,near*.64,57,4,[35,-70],-1.35),idle(1700)];break;
 case 2:keys=[idle(0),k(410,-9,56,-12,[14,-91],-.08),k(700,near*.8,55,5,[35,-99],-.02),k(830,near*.8,53,-4,[30,-100],-.02),k(950,near+22,52,19,[60,-103],-.02),k(1130,near+22,51,14,[57,-103],-.02),k(1390,near*.55,60,-6,[30,-91],.18),idle(1700)];break;
 case 3:keys=[idle(0),k(490,-18,66,-29,[-4,-123],-2.65),k(735,near*.45,66,-22,[6,-139],-2.4),k(855,near*.77,69,-12,[24,-146],-1.65),k(950,near+60,57,30,[65,-130],.65),k(1120,near+60,45,31,[70,-63],.47),k(1400,near*.58,57,2,[36,-83],.58),idle(1700)];break;
 case 4:keys=[idle(0),k(550,-22,51,-27,[-9,-87],-.07),k(760,near*.35,52,27,[39,-90],-.02),k(885,near*.81,53,37,[65,-90],-.03),k(950,near+22,55,38,[77,-96],-.02),k(1160,near+22,52,29,[66,-85],.07),k(1410,near*.57,61,6,[35,-88],.34),idle(1700)];break;
 case 5:keys=[idle(0),k(440,-8,43,-14,[2,-116],-1.67),k(680,near*.38,69,-12,[0,-151],-1.72,-47),k(790,slam*.77,75,-10,[4,-154],-1.58,-49),k(870,slam*.95,69,17,[34,-148],-.79,-52),k(950,slam,46,31,[65,-85],.83),k(1110,slam,37,25,[61,-72],.68),k(1290,slam*.8,48,18,[48,-75],.68),idle(1740)];break;
 case 6:keys=[idle(0),k(570,-22,53,-32,[-6,-97],-2.75),k(760,near*.56,53,-15,[19,-115],-2.1),k(875,near*.89,57,6,[46,-115],-1.05),k(950,near+17,55,30,[73,-102],.08),k(1130,near+17,47,30,[69,-63],.35),k(1440,near*.58,61,7,[32,-84],.45),idle(1740)];break;
 case 7:keys=[idle(0),k(470,-18,40,-18,[-8,-113],-1.95),k(665,near*.26,65,-22,[-6,-139],-1.85,-43),k(790,slam*.65,74,-17,[0,-149],-1.7,-56),k(870,slam*.94,70,23,[37,-143],-.71,-68),k(950,slam+8,44,30,[64,-91],.91),k(1160,slam+8,33,22,[58,-67],.6),k(1370,slam*.77,48,9,[38,-80],.63),idle(1740)];break;
 }
 let a=keys[0],b=a,u=0;for(let j=1;j<keys.length;j++){a=keys[j-1];b=keys[j];u=ease((time-a.t)/(b.t-a.t));if(time<=b.t)break;}
 const v={};for(const key of ['x','h','lean','angle','lift'])v[key]=mix(a[key],b[key],u);
 const hip=[0,-v.h],neck=[v.lean,-v.h-Math.sqrt(52*52-v.lean*v.lean)],shoulders=[[neck[0]-10,neck[1]+6],[neck[0]+10,neck[1]+6]];
 let grip=a.g.map((x,j)=>mix(x,b.g[j],u)),angle=v.angle;
 // Keep both hands on the short hilt while respecting both arm reach discs.
 for(let j=0;j<16;j++)for(const [root,offset]of [[shoulders[1],0],[shoulders[0],17]]){
 const dx=grip[0]-Math.cos(angle)*offset-root[0],dy=grip[1]-Math.sin(angle)*offset-root[1],d=Math.hypot(dx,dy);
 if(d>77){grip[0]-=dx*(1-77/d);grip[1]-=dy*(1-77/d);}}
 if(Math.sin(angle)>0&&angle<Math.PI/2)angle=Math.min(angle,Math.asin(clamp((-grip[1]-v.lift-5)/110)));
 let rear=[grip[0]-Math.cos(angle)*17,grip[1]-Math.sin(angle)*17];
 if(index===0)rear=[shoulders[0][0]-24,shoulders[0][1]+40];
 const [be,bh]=twoBone(shoulders[0],rear,40,-1),[fe,fh]=twoBone(shoulders[1],grip,40,1);
 const active=ease((time-500)/250)*(1-ease((time-1210)/490)),stride=35+active*(index===4?29:18);
 const airborne=v.lift<-8,feet=airborne?[[-38,-27],[31,-36]]:[[-stride,0],[stride,0]];
 const [bk,bf]=twoBone(hip,feet[0],48,-1),[fk,ff]=twoBone(hip,feet[1],48,-1);
 return {x:v.x,lift:v.lift,opacity:1,blink:0,pose:{points:[[neck[0],neck[1]-21],neck,hip,be,bh,fe,fh,bk,bf,fk,ff],shoulders,sword:angle,lean:0}};
}
export function heavyEffects(ctx,event,time,sampleAt,target,dir,impactAge,hit){
 const index=names.indexOf(event.move);if(index<0||time<260||time>2100)return;
 const black='#202622',ink='#363c32',gray='#6d6e58',gold='#b78b3f',light='#efcf85';
 const fade=1-ease((time-1670)/380),slam=index===5||index===7,ultimate=index===7;
 const line=(pts,c=black,w=1,a=1)=>{ctx.strokeStyle=c;ctx.lineWidth=w;ctx.globalAlpha=a*fade;ctx.beginPath();pts.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke()};
 const seed=n=>{const x=Math.sin(n*127.1+index*213.7)*43758.5453;return x-Math.floor(x)};
 const polygon=(pts,c,a)=>{ctx.fillStyle=c;ctx.globalAlpha=a*fade;ctx.beginPath();pts.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.fill()};
 const rock=(x,y,size,rotation,id,alpha)=>{
 ctx.save();ctx.translate(x,y);ctx.rotate(rotation);
 const vertices=Array.from({length:6},(_,j)=>{const a=j*Math.PI/3,r=size*(.68+seed(id*8+j)*.37);return [Math.cos(a)*r,Math.sin(a)*r]});
 polygon(vertices,black,alpha);polygon([vertices[0],vertices[1],vertices[2],[-size*.16,size*.06]],'#777461',alpha*.95);
 polygon([vertices[2],vertices[3],vertices[4],[-size*.16,size*.06]],'#434a40',alpha);
 line([vertices[4],vertices[5],vertices[0]],gold,Math.max(.7,size*.06),alpha*.78);
 if(size>10)line([vertices[1],[-size*.12,size*.03],vertices[4]],'#a19570',.65,alpha*.55);
 ctx.restore();};
 ctx.save();ctx.lineCap='round';ctx.lineJoin='round';const now=sampleAt(time),root=now.root;
 const charge=ease((time-260)/400)*(1-ease((time-780)/90));
 if(charge>0){line([now.hand,now.tip],gold,13,charge*.12);line([now.hand,now.tip],light,.9,charge*.7);
 for(let j=0;j<18;j++){const x=root[0]+(seed(j)-.5)*105,y=326-seed(j+30)*charge*9;rock(x,y,1.3+seed(j+60)*2,j,j,charge*.55);}}
 // Dense black sweep follows the blade; broken gold edges preserve brush texture.
 for(let j=1;j<=(index===1?6:index===2?9:23);j++){
 const at=Math.min(time,1080)-j*9;if(at<690||time>1350)continue;
 const a=sampleAt(at),b=sampleAt(at+9),alpha=(1-j/24)*(1-ease((time-1100)/250));
 polygon([a.hand,a.tip,b.tip,b.hand],black,alpha*(index===6?.55:.36));
 line([a.tip,b.tip],ink,11*(1-j/25),alpha*.66);
 if(j%4!==0)line([a.tip,b.tip],j%3?gold:light,1.3+(1-j/24)*1.5,alpha*.88);
 const inner=a.hand.map((v,i)=>v+(a.tip[i]-v)*.75),end=b.hand.map((v,i)=>v+(b.tip[i]-v)*.75);
 if(j%3!==0)line([inner,end],gold,.7,alpha*.45);
 }
 // Broken concentric brush strands follow the blade's swept surface.
 if(index!==1&&index!==2&&time>800&&time<1270){
 const strength=ease((time-800)/65)*(1-ease((time-1030)/240));
 for(let strand=0;strand<8;strand++){
 const points=[],portion=.53+strand*.066;
 for(let j=0;j<=26;j++){
 const at=Math.max(700,Math.min(time,1030)-225+j*225/26),pose=sampleAt(at);
 points.push([pose.hand[0]+(pose.tip[0]-pose.hand[0])*portion,
 pose.hand[1]+(pose.tip[1]-pose.hand[1])*portion+Math.sin(j*2.3+strand)*1.1]);
 }
 line(points,strand%3?black:gold,strand%3?3.2:1.4,strength*(strand%3?.45:.72));
 if(strand%2===0)for(let j=2;j<points.length-1;j+=4)line([points[j],points[j+1]],light,.65,strength*.78);
 }
 }
 if((index===1||index===2)&&time>730&&time<1260){
 const strength=ease((time-730)/140)*(1-ease((time-1060)/200));
 const a=now.hand,b=now.tip;
 for(let j=0;j<5;j++){
 const offset=dir*(j*7+4);line([[a[0]-offset,a[1]],[b[0]-offset,b[1]]],j%2?black:gold,j===0?8:1.2,strength*(.64-j*.1));
 }
 if(index===1)for(let j=0;j<9;j++){
 const y=a[1]-12-j*11;line([[a[0]-dir*45,y],[a[0]+dir*10,y]],j%3?black:gold,j%3?2.3:1,strength*.5);
 }
 if(index===2){line([[a[0]-dir*15,a[1]+7],[b[0]+dir*12,b[1]+7]],gold,2,strength*.8);}
 }
 const rush=ease((time-805)/100)*(1-ease((time-1040)/200));
 if(rush>0){
 // Frayed blade-wind tongues, never free-standing circular waves.
 const prev=sampleAt(Math.max(740,Math.min(time,970)-70));
 let dx=now.tip[0]-prev.tip[0],dy=now.tip[1]-prev.tip[1],len=Math.hypot(dx,dy);
 if(len<1){dx=dir;dy=slam?1:0;len=Math.hypot(dx,dy);}dx/=len;dy/=len;
 if(index===1||index===2){dx=dir;dy=0;}
 for(let j=0;j<9;j++){const spread=(j-4)*6,tail=40+seed(j+100)*(ultimate?135:82);
 const head=[now.tip[0]-dy*spread,now.tip[1]+dx*spread],back=[head[0]-dx*tail,head[1]-dy*tail];
 line([back,head],j%3?black:gold,j%3?4+seed(j+120)*7:1.5,rush*(j%3?.42:.84));}
 if(ultimate){const tail=sampleAt(Math.max(790,Math.min(time,970)-115)).tip;
 const nx=-dy,ny=dx;polygon([[tail[0]-dx*35,tail[1]-dy*35],[now.tip[0]+nx*26,now.tip[1]+ny*26],now.tip,[now.tip[0]-nx*26,now.tip[1]-ny*26]],black,rush*.64);
 line([tail,now.tip],gold,3,rush*.7);line([tail,now.tip],light,.8,rush*.9);}
 }
 if(hit&&impactAge>=0){
 const age=impactAge/1000,p=clamp(impactAge/950),power=ultimate?1.45:slam?1.2:index===6?1.12:.9;
 const contact=sampleAt(950),cx=slam?contact.tip[0]:target[0],ground=329;
 // Jagged craters spread from the sword contact, with gold seams at the first beat.
 const spread=ease(impactAge/160),seam=1-ease((impactAge-160)/540);
 for(let branch=0;branch<(slam?7:4);branch++){
 const sign=branch%2?1:-1,length=(70+seed(branch+190)*105)*power*spread;
 const points=Array.from({length:9},(_,j)=>[cx+sign*j/8*length,ground+(branch-3)*2+j/8*(branch%3-1)*11+(seed(j+branch*10+200)-.5)*9]);
 line(points,black,4.2, .78*(1-ease((impactAge-680)/350)));
 line(points,gold,1.5,seam*.9);if(branch%2===0)line(points,light,.55,seam*.7);
 }
 // Broad, low dust fronts: irregular overlapping smudges, no outlined ellipses.
 for(let j=0;j<20;j++){
 const sign=j%2?1:-1,d=(15+age*(120+seed(j+250)*175))*power,r=11+age*22+seed(j+280)*12;
 ctx.globalAlpha=fade*(1-ease((impactAge-350)/650))*(j%3?.14:.22);ctx.fillStyle=j%3?'#8a846a':ink;
 ctx.beginPath();ctx.ellipse(cx+sign*d,ground-3-seed(j+300)*14-Math.sin(p*Math.PI)*8,r*1.65,r*.38,-sign*.08,0,Math.PI*2);ctx.fill();
 }
 // Layered ballistic rubble: large tumbling blocks, then chips and black grit.
 const count=ultimate?86:slam?70:index===6?56:43;
 for(let j=0;j<count;j++){
 const delay=seed(j+350)*.055,t=Math.max(0,age-delay);if(age<delay)continue;
 const large=j<(ultimate?16:slam?12:7),size=large?9+seed(j+380)*(ultimate?15:11):2+seed(j+380)*5;
 const sign=j%2?1:-1,originX=cx+(seed(j+410)-.5)*(slam?62:38);
 const vx=(slam?sign*(95+seed(j+440)*270):dir*(95+seed(j+440)*260)+(seed(j+445)-.5)*100)*power;
 const vy=-(slam?270+seed(j+470)*350:170+seed(j+470)*270)*(large?1:.82);
 const gravity=1030,land=-2*vy/gravity;
 let flight=t,drop=vy*t+.5*gravity*t*t,rotation=seed(j+500)*6+t*(seed(j+530)-.5)*11;
 let px=originX+vx*t,py=ground-size+drop;
 if(t>land){const bounce=t-land,bv=-Math.abs(vy)*.2,bt=-2*bv/gravity;flight=land+Math.min(bounce,bt)*.38;
 px=originX+vx*flight;py=ground-size+(bounce<bt?bv*bounce+.5*gravity*bounce*bounce:0);rotation=seed(j+500)*6+flight*(seed(j+530)-.5)*11;}
 const alpha=(large?.96:.76)*(1-ease((impactAge-650)/470));
 // Sparse gold speed scratches show the stones' upward impulse.
 if(t<.22&&large)line([[px-vx*.035,py-(vy+gravity*t)*.035],[px,py]],j%3?black:gold,1.3,alpha*.6);
 rock(px,py,size,rotation,j+600,alpha);
 }
 // Chipped gold-black contact spray replaces the former chest rings.
 const flash=1-ease(impactAge/210);
 if(flash>0)for(let j=0;j<24;j++){const a=j*2.399,r=(10+impactAge*.34)*(1+seed(j+760));const start=[cx+Math.cos(a)*r*.32,(slam?315:target[1])+Math.sin(a)*r*.3],end=[cx+Math.cos(a)*r,(slam?315:target[1])+Math.sin(a)*r*.72];line([start,end],j%3?gold:light,j%4?1.5:3,flash*.9);}
 }
 ctx.restore();
}
export function heavyTime(local, contact = 950) {
 return local <= contact ? local * 950 / Math.max(1, contact) : 950 + local - contact;
}
export function heavyReplayTime(local, contact = 950) {
 return local <= 950 ? local * Math.max(1, contact) / 950 : contact + local - 950;
}
export function heavyHold(move) { return move === '绝技·破天' ? 155 : 125; }
export function heavyShake(move, age) {
 if(age<0||age>=390)return [0,0];
 const strength=move==='绝技·破天'?13:move==='泰山压顶'?10:7;
 const envelope=Math.exp(-age/115)*(1-age/390);
 return [Math.sin(age*.105)*strength*envelope,Math.cos(age*.13)*strength*.62*envelope];
}