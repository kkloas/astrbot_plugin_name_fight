import { twoBone } from './sampleMotion.js';
import { drawCurvedFigure } from './curvedFigure.js';
export const names=['诡步欺身','火树银花','夺刃式','影不留踪','焚心似火','绊马索','圣火燎原','绝技·明王降世'];
export const notes=['反拧肩胯 / 假退侧进 / 死角拍击','双令交击 / 银花爆闪 / 反弧急削','贴刃缠绞 / 反腕锁势 / 击向持械手','低身潜入 / 掠过盲区 / 背身短打','屈身暴起 / 双令怪圈 / 沉肩重击','伏身翻滚 / 令锋贴地 / 勾扫下盘','交错疾步 / 赤芒短刺 / 双令连凿','异位残身 / 多向绞击 / 炽焰收束'];
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>{x=clamp(x);return x*x*(3-2*x)};
const lerp=(a,b,u)=>a+(b-a)*u;
const k=(t,x,h,lean,f,r,angle,lift=0,roll=0,facing=1)=>({t,x,h,lean,f,r,angle,lift,roll,facing});
const idle=t=>k(t,0,72,-5,[47,-94],[-33,-93],-.55);
export function holyMotion(event,time,travel){
 const index=names.indexOf(event.move);if(index<0)return;
 const near=travel+48,back=travel+248;
 let keys;
 switch(index){
 case 0: keys=[idle(0),k(350,-20,67,-28,[-28,-115],[36,-97],-2.1),k(560,near*.18,51,29,[23,-80],[-32,-63],1.2),k(750,near*.86,60,-27,[-16,-121],[54,-85],-1.7),k(950,near,69,27,[76,-101],[13,-122],.18),k(1080,near-12,65,9,[43,-80],[-39,-105],1.1),idle(1690)];break;
 case 1: keys=[idle(0),k(380,0,70,-11,[15,-129],[22,-132],-1.9),k(610,near*.42,63,17,[21,-126],[23,-125],-1),k(735,near*.82,70,-15,[-12,-146],[57,-84],-2.5),k(850,near,65,25,[73,-82],[-28,-119],.42),k(950,near,67,19,[67,-112],[46,-71],-.45),k(1110,near-8,65,4,[43,-73],[-28,-120],1.4),idle(1690)];break;
 case 2: keys=[idle(0),k(420,-8,65,-18,[27,-109],[-4,-123],-1.5),k(720,near*.86,72,13,[57,-108],[29,-89],-.45),k(850,near,68,23,[72,-105],[56,-110],.25),k(950,near+8,65,-9,[59,-81],[43,-101],1.5),k(1110,near-12,70,-18,[18,-103],[35,-94],2.1),idle(1690)];break;
 case 3: keys=[idle(0),k(380,-12,44,27,[37,-65],[-24,-50],.5),k(570,near*.28,39,35,[64,-53],[-19,-42],.8),k(710,back*.79,40,31,[51,-62],[-29,-50],.65),k(825,back,51,-20,[20,-98],[-30,-68],-1.1,0,0,-1),k(950,back,67,28,[76,-99],[25,-124],.05,0,0,-1),k(1100,back,52,-12,[28,-80],[-35,-60],1.1,0,0,-1),k(1330,near*.65,42,-20,[35,-72],[-35,-55],.7),idle(1690)];break;
 case 4: keys=[idle(0),k(440,-10,45,-18,[-27,-87],[37,-61],-2.3),k(650,near*.44,66,5,[9,-151],[-47,-108],-2.6,-34),k(790,near*.85,76,-15,[57,-139],[12,-151],-.85,-45),k(950,near,59,29,[77,-78],[22,-118],.55),k(1090,near,51,20,[46,-46],[-16,-88],1.1),idle(1690)];break;
 case 5: keys=[idle(0),k(390,-8,42,30,[41,-48],[-21,-58],.9),k(520,near*.13,47,20,[34,-61],[-26,-53],.7,-39,0),k(680,near*.52,47,14,[35,-58],[-31,-65],.8,-39,Math.PI),k(840,near*.93,47,18,[35,-59],[-30,-65],.6,-39,Math.PI*2),k(950,near,34,31,[77,-19],[-7,-67],.08),k(1120,near-20,41,18,[47,-39],[-19,-69],.65),idle(1690)];break;
 case 6: keys=[idle(0),k(420,-16,61,-24,[6,-132],[41,-80],-1.6),k(650,near*.67,66,19,[69,-108],[-18,-91],-.12),k(750,near-15,57,-22,[10,-126],[62,-94],-1.5),k(840,near+6,67,23,[73,-96],[-12,-119],.1),k(900,near-4,57,-12,[9,-135],[59,-89],-1.5),k(950,near+9,63,27,[77,-105],[53,-87],-.12),k(1090,near-10,61,-15,[23,-93],[-25,-125],1),idle(1690)];break;
 case 7: keys=[idle(0),k(390,-18,53,-24,[-23,-119],[29,-134],-2.1),k(600,near*.5,64,22,[60,-115],[-25,-83],-.4,-18),k(730,near*.86,55,-28,[-15,-130],[63,-79],-2,-28),k(840,near+28,76,-8,[47,-154],[9,-138],-1.3,-33),k(950,near+12,58,30,[77,-87],[52,-121],.3),k(1130,near-8,49,14,[41,-47],[-38,-101],1.2),idle(1690)];break;
 }
 let a=keys[0],b=keys[0],u=0;
 for(let i=1;i<keys.length;i++){a=keys[i-1];b=keys[i];u=ease((time-a.t)/(b.t-a.t));if(time<=b.t)break;}
 const v={};for(const key of ['x','h','lean','angle','lift','roll'])v[key]=lerp(a[key],b[key],u);
 for(const key of ['f','r'])v[key]=a[key].map((x,i)=>lerp(x,b[key][i],u));
 const facing=u<.5?a.facing:b.facing;
 const hip=[0,-v.h],neck=[v.lean,-v.h-Math.sqrt(52*52-v.lean*v.lean)],shoulders=[[neck[0]-10,neck[1]+6],[neck[0]+10,neck[1]+6]];
 const [be,bh]=twoBone(shoulders[0],v.r,40,-1),[fe,fh]=twoBone(shoulders[1],v.f,40,1);
 const moving=ease((time-410)/120)*(1-ease((time-1150)/320)),step=Math.sin(time*.023)*moving;
 const feet=index===5&&time>480&&time<850?[[-30,-25],[32,-23]]:[[-34-step*17,-Math.max(0,step)*15],[39+step*12,-Math.max(0,-step)*13]];
 const [bk,bf]=twoBone(hip,feet[0],48,-1),[fk,ff]=twoBone(hip,feet[1],48,-1);
 const veil=index===3?(ease((time-725)/40)*(1-ease((time-855)/40))*.72+ease((time-1170)/35)*(1-ease((time-1370)/45))*.6):0;
 return {x:v.x,lift:v.lift,opacity:1-veil,blink:0,pose:{points:[[neck[0],neck[1]-21],neck,hip,be,bh,fe,fh,bk,bf,fk,ff],shoulders,sword:v.angle,lean:0,roll:v.roll,facing}};
}
// Tapered ink feather with broken shaft highlights and asymmetric flame barbs.
export function drawCalligraphicFeather(ctx,x,y,length,angle,curvature,coreColor,accentColor,alpha=1){
 if(length<=.1||alpha<=0)return;
 ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.globalAlpha=alpha;
 const spine=u=>[length*u,Math.sin(u*Math.PI)*length*curvature];
 const width=u=>Math.pow(Math.sin(Math.PI*u),.85)*length*.135;
 ctx.fillStyle=accentColor;ctx.globalAlpha=alpha*.34;
 ctx.beginPath();ctx.moveTo(0,0);
 for(let j=1;j<=20;j++){const u=j/20,p=spine(u);ctx.lineTo(p[0],p[1]-width(u)*(1+.12*Math.sin(u*25)));}
 for(let j=19;j>=0;j--){const u=j/20,p=spine(u);ctx.lineTo(p[0],p[1]+width(u)*.8);}
 ctx.closePath();ctx.fill();
 ctx.lineCap='round';
 for(let side=-1;side<=1;side+=2)for(let j=1;j<=9;j++){
 const u=.12+j*.076,a=spine(u-.065),b=spine(u+.045);
 ctx.globalAlpha=alpha*(j%3===0?.78:.57);ctx.strokeStyle=j%3===0?coreColor:accentColor;ctx.lineWidth=.65+(1-u)*.8;
 ctx.beginPath();ctx.moveTo(...a);ctx.quadraticCurveTo(length*u,b[1]+side*width(u)*.55,b[0],b[1]+side*width(u)*(side===1?.82:1.1));ctx.stroke();
 }
 ctx.strokeStyle=coreColor;ctx.globalAlpha=alpha*.75;ctx.lineWidth=1.35;
 ctx.beginPath();ctx.moveTo(-length*.13,0);for(let j=0;j<=22;j++)ctx.lineTo(...spine(j/22));ctx.stroke();
 // Separate pale strokes leave visible gaps rather than a solid neon shaft.
 for(let j=0;j<6;j++){ctx.strokeStyle=j%2?'#f6d174':'#fff0b7';ctx.globalAlpha=alpha*.95;ctx.lineWidth=.7;ctx.beginPath();ctx.moveTo(...spine(.06+j*.15));ctx.lineTo(...spine(.13+j*.15));ctx.stroke();}
 const tip=spine(.94);ctx.fillStyle=accentColor;ctx.globalAlpha=alpha;ctx.beginPath();ctx.arc(tip[0],tip[1],.9,0,Math.PI*2);ctx.fill();ctx.restore();
}
function shatteredPlumes(ctx,origin,age,count,dir,alpha,large=false){
 const duration=large?610:400;if(age<0||age>duration)return;
 const p=age/duration,appear=ease(age/55),fade=(1-ease((p-.32)/.68))*alpha;
 for(let i=0;i<count;i++){
 const a=i*2.399+(i%3)*.13,r=(large?34:17)+Math.pow(p,.72)*(large?58+(i%5)*13:24+(i%4)*9);
 const x=origin[0]+dir*Math.cos(a)*r,y=origin[1]+Math.sin(a)*r*.78+p*p*24;
 const angle=Math.atan2(Math.sin(a),dir*Math.cos(a))+.18*Math.sin(i+p*3);
 const length=(large?23+(i%4)*6:14+(i%3)*4)*appear*(1-p*.36);
 drawCalligraphicFeather(ctx,x,y,length,angle,(i%2?1:-1)*(.12+(i%3)*.035),'#5a3924',i%3===0?'#c75d2e':'#dda23a',fade*(.7+(i%3)*.1));
 // Gold dust takes over as the plume breaks up.
 if(p>.35){ctx.save();ctx.globalAlpha=alpha*(1-p)*.75;ctx.fillStyle='#d6a354';for(let j=0;j<3;j++){ctx.beginPath();ctx.arc(x-dir*Math.cos(a)*(j+1)*5,y-Math.sin(a)*(j+1)*5,1-j*.2,0,Math.PI*2);ctx.fill();}ctx.restore();}
 }
}
export function holyEffects(ctx,event,time,sampleAt,target,dir,impactAge,hit){
 const index=names.indexOf(event.move);if(index<0||time<360||time>1680)return;
 const fade=1-ease((time-1190)/450),red='#b74730',gold='#d6a354',white='#fff3c4';
 const line=(pts,color,width,alpha)=>{ctx.globalAlpha=fade*alpha;ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke()};
 const spark=(origin,age,count,spread=80)=>{if(age<0||age>430)return;const p=age/430;for(let i=0;i<count;i++){const a=i*2.399,r=(12+(i%7)*spread/7)*p;const x=origin[0]+Math.cos(a)*r,y=origin[1]+Math.sin(a)*r+p*p*20;line([[x-Math.cos(a)*(3+6*(1-p)),y-Math.sin(a)*5],[x,y]],i%3?gold:white,i%4?1:2.2,(1-p)*.85)}};
 ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
 // Both trails are sampled from the two actual held tokens, including rolls and turns.
 if(time>570)for(const rear of [false,true]){for(let j=1;j<20;j++){const at=time-j*9;if(at<560||at>1120)continue;const a=sampleAt(at),b=sampleAt(at+9);const tip=rear?'rearTip':'tip';line([a[tip],b[tip]],red,(1-j/21)*(index>=6?11:6),.45*(1-j/21));line([a[tip],b[tip]],gold,(1-j/21)*2,.85*(1-j/21));}}
 const now=sampleAt(time);
 if(index===0||index===3||index===6||index===7){const count=index===7?5:3;for(let j=count;j>=1;j--){const at=time-j*(index===7?44:32);if(at<480||at>1040)continue;const sample=sampleAt(at),frame=sample.frame;
 const around=index===7&&time>730,ghostDir=around?(j%2?dir:-dir):dir*(frame.pose.facing||1);
 const ghostX=around?target[0]-ghostDir*(82+j*5):frame.x;
 const ghostLift=frame.lift-(around?(j%3)*9:0);
 ctx.save();ctx.globalAlpha=fade;
 drawCurvedFigure(ctx,ghostX,ghostDir,frame.pose,at,'tokens',(.22-j*.025)*(index===7?1.35:1),ghostLift,false,'short_shenghuoling');
 ctx.restore();
 if(around){const hand=frame.pose.points[6],angle=frame.pose.sword;
 const tip=[ghostX+ghostDir*(hand[0]+Math.cos(angle)*43),324+ghostLift+hand[1]+Math.sin(angle)*43];
 line([[tip[0]-ghostDir*17,tip[1]-10],tip],red,5,.18);line([[tip[0]-ghostDir*17,tip[1]-10],tip],gold,1,.35);
 drawCalligraphicFeather(ctx,tip[0]-ghostDir*20,tip[1],24,Math.atan2(-.3,-ghostDir),j%2?.15:-.15,'#64462c','#d7aa51',fade*.36);}}}
 if(index===1){const clash=sampleAt(610),origin=[(clash.tip[0]+clash.rearTip[0])/2,(clash.tip[1]+clash.rearTip[1])/2];spark(origin,time-610,45,105);shatteredPlumes(ctx,origin,time-610,6,dir,fade);}
 if(index===2&&time>770&&time<1160){const p=(time-770)/390;const pts=[];for(let i=0;i<=36;i++){const a=i/36*Math.PI*1.65+p*2;pts.push([now.tip[0]+Math.cos(a)*18,now.tip[1]+Math.sin(a)*10])}line(pts,gold,2,.8);if(hit)spark(target,impactAge,18,35);}
 if(index===4||index===7){for(const rear of [false,true]){const pts=[];for(let j=0;j<24;j++){const at=time-j*9;if(at<585||at>1020)continue;pts.push(sampleAt(at)[rear?'rearTip':'tip'])}if(pts.length>1){line(pts,red,15,.09);line(pts,gold,1.4,.8)}}}
 if(index===5&&time>500&&time<1190){const root=now.root;for(let j=0;j<18;j++){const a=j*2.399,p=clamp((time-500-j*14)/350);if(p<=0||p>=1)continue;const x=root[0]-dir*(10+p*70),y=327-Math.sin(p*Math.PI)*(4+j%5*2);line([[x-dir*5,y],[x,y+2]],'#8a8571',1.3,(1-p)*.5)}}
 if(index>=6){for(let j=0;j<24;j++){const at=time-j*10;if(at<570||at>1100)continue;const p=j/24,tip=sampleAt(at)[j%2?'tip':'rearTip'];line([[tip[0]-dir*(4+p*18),tip[1]+p*13],[tip[0],tip[1]]],j%3?red:gold,1+(1-p)*2,(1-p)*.6)}}
 if(index===4&&time>625&&time<1170){
 for(let j=0;j<3;j++){
 const at=Math.min(time,1015)-j*48,which=j%2?'rearTip':'tip';
 const tip=sampleAt(at)[which],past=sampleAt(at-24)[which];
 const angle=Math.atan2(tip[1]-past[1],tip[0]-past[0])+Math.PI;
 const alpha=fade*ease((time-625)/80)*(1-ease((time-1020)/150))*(.84-j*.15);
 drawCalligraphicFeather(ctx,tip[0]+Math.cos(angle)*9,tip[1]+Math.sin(angle)*9,38-j*6,angle,(j%2?1:-1)*.2,'#62392c',j===1?'#c66530':'#dfa936',alpha);
 }
 }
  if(index===7&&hit){
 shatteredPlumes(ctx,target,impactAge,18,dir,fade,true);
 shatteredPlumes(ctx,[target[0],target[1]-6],impactAge-95,12,-dir,fade*.8);
 if(impactAge>70&&impactAge<630){
 const p=(impactAge-70)/560;
 ctx.save();ctx.fillStyle='#d7ae58';ctx.globalAlpha=fade*(1-p)*.7;
 for(let j=0;j<38;j++){const a=j*2.399,r=24+p*(62+j%7*9);ctx.beginPath();ctx.arc(target[0]+Math.cos(a)*r,target[1]+Math.sin(a)*r*.8-p*22,.6+j%3*.4,0,Math.PI*2);ctx.fill();}
 ctx.restore();
 }
 }
 if(hit&&impactAge>=0){spark(target,impactAge,index===7?60:index===1?42:28,index===7?120:75);if(index===7){const p=clamp(impactAge/360);for(let j=0;j<3;j++){ctx.globalAlpha=fade*(1-p)*.6;ctx.strokeStyle=j%2?gold:red;ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(target[0],target[1],12+p*(62+j*12),18+p*(85+j*9),j*.5,0,Math.PI*2);ctx.stroke()}}}
 ctx.restore();
}



// Authored contact and recorded contact may differ; keep the conversion reversible.
export function holyTime(local, contact = 950) {
 return local <= contact ? local * 950 / Math.max(1, contact) : 950 + local - contact;
}
export function holyReplayTime(local, contact = 950) {
 return local <= 950 ? local * Math.max(1, contact) / 950 : contact + local - 950;
}
export function holySample(frame, dir) {
 const world = point => {
  const hip=frame.pose.points[2],roll=frame.pose.roll||0,dx=point[0]-hip[0],dy=point[1]-hip[1];
  return [frame.x+dir*(frame.pose.facing||1)*(hip[0]+dx*Math.cos(roll)-dy*Math.sin(roll)),
   324+frame.lift+hip[1]+dx*Math.sin(roll)+dy*Math.cos(roll)];
 };
 const tip=rear=>{const angle=rear?-frame.pose.sword-.8:frame.pose.sword,hand=frame.pose.points[rear?4:6];
  return world([hand[0]+Math.cos(angle)*43,hand[1]+Math.sin(angle)*43]);};
 return {tip:tip(false),rearTip:tip(true),root:[frame.x,324+frame.lift],frame};
}