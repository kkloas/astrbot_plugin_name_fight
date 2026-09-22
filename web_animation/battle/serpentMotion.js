import {twoBone} from './sampleMotion.js';
export const names=['银蛇吐信','灵蛇缠腕','毒龙卷柱','鳞片倒割','狂蟒翻江','千丝万缕','嗜血蟒绞','绝技·白蟒索命'];
export const notes=['腕抖弹梢 / 银蛇吐信 / 毒珠飞溅','绕腕成环 / 沉肩回拽 / 蛇牙倒钩','贴地游走 / 螺旋攀升 / 蟒柱封步','三番送鞭 / 连抽倒割 / 飞鳞逆割','连续抡抽 / 延长鞭打 / 翻江白浪','高速连抽 / 细影交织 / 毒雨千丝','合围成圈 / 两段收紧 / 拧转回扯','腾空掷鞭 / 白蟒扑咬 / 锁身绞杀'];
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)},mix=(a,b,u)=>a+(b-a)*u;
const end=i=>i===4?2180:i>=3&&i<=6?1860:1340;
const beat=(i,t)=>{const period=i===3?280:i===4?310:180;return (1-Math.cos(clamp((t-600)/(end(i)-600))*(end(i)-600)/period*Math.PI*2))/2;};
const seed=n=>{const x=Math.sin(n*127.1)*43758.54;return x-Math.floor(x)};
export function serpentMotion(event,time,travel){
 const i=names.indexOf(event.move);if(i<0)return;
 const prep=ease((time-180)/320),go=ease((time-500)/450),back=ease((time-end(i))/340),active=prep*(1-back),strike=clamp((time-520)/430);
 const snap=Math.sin(strike*Math.PI),pull=ease((time-950)/260)*(1-back);
 let x=Math.max(0,travel-140)*go*(1-back),lift=0,lean=-18*prep+43*go-24*pull,h=68;
 let gx=24+50*go-44*pull,gy=-108,angle=-.12;
 if(i===0){gx+=Math.sin(strike*Math.PI*4)*14*snap;lean+=snap*4;}
 if(i===1){gy=-100+Math.sin(strike*Math.PI*2)*25;gx-=pull*25;lean-=pull*16;}
 if(i===2){h=47+20*go;gy=-55-60*go;angle=.65-1.2*go;lean=12*active;}
 if(i===3){const b=beat(i,time);gx=12+62*b;gy=-96-20*(1-b);lean=-22+49*b;x-=25*(1-b)*active;}
 if(i===4){const a=(time-600)/310*Math.PI*2;gx=24-Math.cos(a)*48*active;gy=-112+Math.sin(a)*43*active;lean=-Math.cos(a)*29*active;h=55;}
 if(i===5){const b=beat(i,time);gx=15+49*b;gy=-155+38*b;lean=-14+29*b;}
 if(i===6){const squeeze=ease((time-950)/230)*.5+ease((time-1270)/240)*.5,twist=Math.sin(clamp((time-1510)/350)*Math.PI);gx=55*go-55*squeeze;gy=-102+squeeze*18-twist*25;h=52;lean=22*go-47*squeeze;x-=twist*28;}
 if(i===7){lift=-92*Math.sin(Math.PI*clamp((time-400)/900));gx=25+48*go-22*pull;gy=-133+26*go;lean=24*go-18*pull;h=70;x+=45*go*(1-back);}
 lean*=1-back;h=mix(74,h,active);gx=mix(34,gx,active);gy=mix(-105,gy,active);lean=Math.max(-38,Math.min(38,lean));
 const hip=[0,-h],neck=[lean,-h-Math.sqrt(2704-lean*lean)],shoulders=[[neck[0]-10,neck[1]+6],[neck[0]+10,neck[1]+6]];
 const [fe,fh]=twoBone(shoulders[1],[gx,gy],40,1),[be,bh]=twoBone(shoulders[0],[-35-20*active,-90+25*active],40,-1);
 const stride=34+18*active,feet=lift<-8?[[-34,-25],[31,-32]]:[[-stride,0],[stride,0]];
 const [bk,bf]=twoBone(hip,feet[0],48,-1),[fk,ff]=twoBone(hip,feet[1],48,-1);
 const target=[travel+165-x,-95-lift],points=whipPath(i,time,fh,target,active);
 return {x,lift,opacity:1,blink:0,pose:{points:[[neck[0],neck[1]-21],neck,hip,be,bh,fe,fh,bk,bf,fk,ff],shoulders,sword:angle,lean:0,whip:points}};
}
function whipPath(i,time,hand,target,active){
 const launch=ease((time-470)/460),pull=ease((time-980)/270),recover=ease((time-end(i))/340),reach=launch*(1-recover)*(i>=3&&i<=5?.48+.52*beat(i,time):1);
 const tx=mix(hand[0]+110,target[0],reach),ty=mix(hand[1]+55,target[1],reach);
 const pts=[];
 for(let j=0;j<=90;j++){const u=j/90,s=Math.sin(Math.PI*u);let x=mix(hand[0],tx,u),y=mix(hand[1],ty,u);
 if(i===0){y+=Math.sin(u*10-time*.017)*s*22*(1-launch*.7);x-=Math.sin(u*Math.PI)*20*(1-launch);}
 if(i===1||i===6||i===7){const start=i===1?.66:.43;if(u>start){const v=(u-start)/(1-start),turns=i===1?1.25:i===6?2.7:3.2,r=(i===1?31:i===7?92:75)*(1-(i===6?(.28*ease((time-950)/230)+.36*ease((time-1270)/240)):pull*.45))*reach,a=v*Math.PI*2*turns-(i===6?ease((time-1510)/350)*Math.PI*1.7:time*.002);
 const f=ease(v/.18);x=mix(x,tx+Math.cos(a)*r,f);y=mix(y,ty+Math.sin(a)*r*.48+(i===1?0:(v-.5)*106),f);}else y-=s*45*active;}
 if(i===2){const a=u*Math.PI*7-time*.003;x+=Math.sin(a)*s*45*launch;y=mix(hand[1],-2,u)+Math.cos(a)*s*18-launch*u*125;}
 if(i===3){y+=s*Math.sin(u*8)*20; x-=pull*s*55;}
 if(i===4){y+=Math.sin(u*Math.PI*3-time*.012)*s*95*active;}
 if(i===5){y-=s*135*active;y+=Math.sin(u*34-time*.065)*s*13*active;}
 pts.push([x,y]);}
 for(let pass=0;pass<2;pass++){const old=pts.map(p=>[...p]);for(let j=1;j<pts.length-1;j++)pts[j]=old[j].map((v,k)=>(old[j-1][k]+2*v+old[j+1][k])/4);}
 return pts;
}
export function drawSerpentWhip(ctx,pts){
 ctx.save();ctx.lineJoin='round';ctx.lineCap='round';
 for(const [color,w]of [['#78847a',4.8],['#eceee0',2.9]]){ctx.strokeStyle=color;ctx.lineWidth=w;ctx.beginPath();pts.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke();}
 ctx.strokeStyle='#576f56';ctx.lineWidth=1;
 for(let j=5;j<pts.length-1;j+=5){const p=pts[j],q=pts[j+1],a=Math.atan2(q[1]-p[1],q[0]-p[0]);ctx.beginPath();ctx.moveTo(...p);ctx.lineTo(p[0]-Math.cos(a)*4-Math.sin(a)*5,p[1]-Math.sin(a)*4+Math.cos(a)*5);ctx.stroke();}
 ctx.restore();
}
export function serpentEffects(ctx,event,time,sampleAt,target,dir,impactAge,hit){
 const i=names.indexOf(event.move);if(i<0||time<390||time>2660)return;
 const fade=1-ease((time-end(i))/440),grow=ease((time-390)/230),alpha=fade*grow;
 const world=t=>{const f=sampleAt(t).frame;if(!f?.pose.whip)return [];return f.pose.whip.map(p=>[f.x+dir*p[0],324+f.lift+p[1]]);};
 const pts=world(time);if(pts.length<2)return;
 ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
 const path=(arr,color,w,a)=>{ctx.strokeStyle=color;ctx.lineWidth=w;ctx.globalAlpha=a;ctx.beginPath();arr.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke();};
 // The apparition shares the articulated whip path rather than floating beside it.
 path(pts,'#778f63',i===7?62:15,alpha*.12);path(pts,'#faffdf',i===7?38:9,alpha*.57);path(pts,'#99ac7c',1.2,alpha*.66);
 for(let j=7;j<pts.length-2;j+=3){const p=pts[j],q=pts[j+1],a=Math.atan2(q[1]-p[1],q[0]-p[0]),w=i===7?18:4;path([[p[0]-Math.sin(a)*w,p[1]+Math.cos(a)*w],[p[0]+Math.cos(a)*3,p[1]+Math.sin(a)*3],[p[0]+Math.sin(a)*w,p[1]-Math.cos(a)*w]],'#7b9268',.85,alpha*.6);}
 const tip=pts.at(-1),prev=pts.at(-3),ang=Math.atan2(tip[1]-prev[1],tip[0]-prev[0]);
 if(i>=3){
 ctx.save();ctx.translate(...tip);ctx.rotate(ang);ctx.globalAlpha=alpha*.35;ctx.fillStyle='#83a568';
 ctx.beginPath();ctx.ellipse(3,0,i===7?30:11,i===7?23:7,0,0,Math.PI*2);ctx.fill();ctx.restore();
 }
 if(i===4||i===5||i===7){const count=i===5?14:i===4?9:5;for(let j=1;j<=count;j++){const past=world(time-j*12);if(past.length<2)continue;const off=i===5?(j-count/2)*9:0;path(past.map((p,k)=>[p[0],p[1]+Math.sin(k/90*Math.PI)*off]),j%2?'#fffef0':'#90a782',i===5?1:2,alpha*(1-j/(count+1))*.46);}}
 if(i===2||i===6){for(let j=0;j<20;j++){const a=j*2.399+time*.002,r=(i===6?65:88)*(1-ease((time-940)/400)*.4);ctx.globalAlpha=alpha*.15;ctx.fillStyle='#719548';ctx.beginPath();ctx.ellipse(target[0]+Math.cos(a)*r,326+Math.sin(a)*r*.13,11,3,a,0,Math.PI*2);ctx.fill();}}
 // Venom and barbs are cosmetic particles, with hit bursts omitted on a dodge.
 for(let j=0;j<(i===4?65:35);j++){const age=time-520-j*21;if(age<0||age>650)continue;const p=age/650,source=world(520+j*21);if(!source.length)continue;const o=source.at(-1),x=o[0]-dir*p*(12+seed(j)*40),y=o[1]+p*p*75;ctx.globalAlpha=(1-p)*alpha*.6;ctx.fillStyle=j%2?'#749d36':'#a4b84c';ctx.beginPath();ctx.ellipse(x,y,1.5+seed(j+9)*2,2.5+p*3,-p,0,Math.PI*2);ctx.fill();}
 if(hit&&impactAge>=0&&impactAge<650){const p=impactAge/650;for(let j=0;j<(i===7?65:30);j++){const a=j*2.399,v=30+seed(j)*100,x=target[0]+Math.cos(a)*v*p,y=target[1]+Math.sin(a)*v*p+p*p*60;ctx.globalAlpha=(1-p)*.8;ctx.fillStyle=j%3?'#76913e':'#e9edcf';ctx.beginPath();ctx.ellipse(x,y,1+seed(j+44)*3,2+seed(j+4)*5,a,0,Math.PI*2);ctx.fill();if(j%4===0)path([[x-4,y+3],[x,y-5],[x+2,y+4]],'#78906c',1,(1-p)*.8);}}
 ctx.restore();
}

export const serpentTime=(t,c=950)=>t<=c?t*950/Math.max(1,c):950+(t-c)/.43;
export const serpentReplayTime=(t,c=950)=>t<=950?t*Math.max(1,c)/950:c+(t-950)*.43;
