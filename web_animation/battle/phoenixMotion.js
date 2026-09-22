import { twoBone } from './sampleMotion.js';
import { drawCalligraphicFeather as feather } from './holyMotion.js';
export const names=['凤点头','穿林打叶','鸟鸣涧','百鸟入林','有凤来仪','乱花迷眼','凤翔九天','绝技·百鸟朝凤'];
export const notes=['短促三点 / 枪尖吐火 / 赤羽轻落','侧掠挑叶 / 折线火痕 / 穿隙急刺','交步回枪 / 螺旋火丝 / 蓄弹突进','虚枪分散 / 羽群穿林 / 一枪归实','凌空折枪 / 斜插出画 / 羽焰消散','腕转枪花 / 朱羽纷飞 / 迷眼回刺','蓄步飞枪 / 横贯出画 / 闪回原位','前刺起势 / 升空悬停 / 火凤垂落'];
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)},mix=(a,b,t)=>a+(b-a)*t;
const k=(t,x,h,lean,g,angle,lift=0)=>({t,x,h,lean,g,angle,lift});
const idle=t=>k(t,0,74,-6,[34,-105],-.28);
export function phoenixMotion(event,time,travel){
 const i=names.indexOf(event.move);if(i<0)return;
 const n=Math.max(0,travel+12);let keys;
 switch(i){
 case 0:keys=[idle(0),k(420,n*.22,68,-12,[24,-108],-.16),k(640,n*.65,66,16,[67,-111],-.12),k(720,n*.5,69,2,[36,-104],-.06),k(810,n*.85,65,21,[71,-105],-.1),k(875,n*.73,67,4,[35,-108],-.2),k(950,n,62,27,[76,-112],-.12),k(1120,n,64,20,[65,-111],-.16),idle(1700)];break;
 case 1:keys=[idle(0),k(410,0,58,-22,[-4,-102],-.72),k(660,n*.42,58,9,[48,-78],.34),k(790,n*.68,66,18,[55,-129],-.65),k(875,n*.81,63,-5,[29,-102],.17),k(950,n,61,27,[74,-111],-.1),k(1180,n,64,17,[62,-121],-.3),idle(1710)];break;
 case 2:keys=[idle(0),k(410,-12,78,-14,[18,-108],-.36),k(665,n*.48,79,-20,[5,-99],.06),k(820,n*.6,54,-13,[14,-83],.23),k(950,n,59,32,[76,-110],-.14),k(1160,n,62,20,[58,-113],-.22),idle(1700)];break;
 case 3:keys=[idle(0),k(450,n*.12,63,-12,[23,-110],-.25),k(640,n*.5,62,12,[55,-118],-.4),k(745,n*.67,65,8,[48,-90],.2),k(835,n*.79,61,19,[66,-128],-.28),k(890,n*.76,62,-8,[30,-98],.09),k(950,n,59,31,[77,-107],-.12),k(1130,n,63,15,[60,-110],-.2),idle(1700)];break;
 case 4:keys=[idle(0),k(420,-9,48,-12,[18,-98],-.55),k(640,n*.38,72,-12,[22,-113],-.5,-92),k(760,n*.63,68,9,[51,-108],.68,-100),k(950,n+37,64,30,[72,-119],.72,-64),k(1200,n+285,64,30,[72,-119],.72,155),k(1340,n+430,64,30,[72,-119],.72,285),k(1400,n+430,64,30,[72,-119],.72,285),idle(1401),idle(1700)];break;
 case 5:keys=[idle(0),k(420,n*.25,67,-4,[25,-108],-.25),k(640,n*.55,68,12,[52,-125],-.6),k(735,n*.61,60,7,[49,-88],.3),k(810,n*.7,69,16,[55,-126],-.48),k(880,n*.74,61,3,[38,-91],.22),k(950,n,62,25,[76,-112],-.12),k(1190,n*.84,68,0,[40,-113],-.35),idle(1700)];break;
 case 6:keys=[idle(0),k(430,-20,48,-23,[8,-83],.15),k(650,n*.2,57,8,[43,-111],-.08,-14),k(820,n*.66,59,29,[74,-117],-.04,-22),k(950,n+13,59,33,[78,-118],-.04,-22),k(1260,(travel+210)*1.6+150,59,33,[78,-118],-.04,-22),k(1400,(travel+210)*1.6+150,59,33,[78,-118],-.04,-22),idle(1401),idle(1700)];break;
 case 7:keys=[idle(0),k(380,-18,50,-25,[2,-95],.04),k(650,n*.6,58,16,[56,-115],-.14,-12),k(780,n+18,59,32,[78,-119],-.08,-16),k(870,n+25,61,22,[56,-115],-.7,-40),k(1050,travel+195,72,0,[0,-112],-1.55,-265),k(1150,travel+210,73,0,[0,-103],1.57,-285),k(1250,travel+210,73,0,[0,-103],1.57,-275),k(1400,travel+210,49,12,[0,-100],Math.PI/2,-35),k(1770,travel+210,49,12,[0,-100],Math.PI/2,-35),k(1890,travel+210,49,12,[0,-100],Math.PI/2,-35),idle(1891),idle(2120)];break;
 }
 let a=keys[0],b=a,u=0;for(let j=1;j<keys.length;j++){a=keys[j-1];b=keys[j];u=ease((time-a.t)/(b.t-a.t));if(time<=b.t)break;}
 const v={};for(const key of ['x','h','lean','angle','lift'])v[key]=mix(a[key],b[key],u);
 const hip=[0,-v.h],neck=[v.lean,-v.h-Math.sqrt(2704-v.lean*v.lean)],shoulders=[[neck[0]-10,neck[1]+6],[neck[0]+10,neck[1]+6]];
 const grip=a.g.map((x,j)=>mix(x,b.g[j],u));
 for(let j=0;j<20;j++)for(const [root,off]of [[shoulders[1],0],[shoulders[0],60]]){const dx=grip[0]-off*Math.cos(v.angle)-root[0],dy=grip[1]-off*Math.sin(v.angle)-root[1],d=Math.hypot(dx,dy);if(d>77){grip[0]-=dx*(1-77/d);grip[1]-=dy*(1-77/d);}}
 const rear=[grip[0]-60*Math.cos(v.angle),grip[1]-60*Math.sin(v.angle)];
 const [be,bh]=twoBone(shoulders[0],rear,40,-1),[fe,fh]=twoBone(shoulders[1],grip,40,1);
 const active=ease((time-400)/300)*(1-ease((time-1200)/500)),stride=35+19*active;
 const cross=i===2?Math.sin(clamp((time-380)/550)*Math.PI)*28:0;
 const feet=v.lift<-8?[[-28,-29],[37,-24]]:[[-stride+cross,0],[stride-cross,0]];
 const [bk,bf]=twoBone(hip,feet[0],48,-1),[fk,ff]=twoBone(hip,feet[1],48,-1);
 let opacity=1;
 if(i===4||i===6)opacity=time<1401?1-ease((time-1260)/100):ease((time-1440)/180);
 if(i===7)opacity=time<1891?1-ease((time-1770)/120):ease((time-1920)/200);
 return {x:v.x,lift:v.lift,opacity,blink:0,pose:{points:[[neck[0],neck[1]-21],neck,hip,be,bh,fe,fh,bk,bf,fk,ff],shoulders,sword:v.angle,lean:0}};
}
// Layered, directional bird silhouette: crest, curved neck, tapered flight feathers and ribbon tails.
function phoenix(ctx,x,y,scale,dir,alpha,t,tilt=0){
 ctx.save();ctx.translate(x,y);ctx.scale(dir*scale,scale);ctx.rotate(tilt);ctx.lineCap='round';ctx.lineJoin='round';
 const stroke=(pts,c,w,a)=>{ctx.globalAlpha=alpha*a;ctx.strokeStyle=c;ctx.lineWidth=w;ctx.beginPath();ctx.moveTo(...pts[0]);ctx.bezierCurveTo(...pts[1],...pts[2],...pts[3]);ctx.stroke()};
 for(let j=0;j<9;j++){const wave=Math.sin(t*.006+j*.7)*13;const pts=[[-15,7],[-100,30+j*5+wave],[-135,-60+j*16],[-220-j*8,30+j*7+wave]];stroke(pts,'#d94720',7-j*.48,.23);stroke(pts,j%2?'#f4bd4e':'#df3823',1.6,.72);feather(ctx,-170-j*8,20+j*8+wave,55+j*2,Math.PI-.2,.13,'#b83220','#ed9236',alpha*.5);}
 for(const side of [-1,1]){
 const flap=Math.sin(t*.006)*12;
 ctx.globalAlpha=alpha*.17;ctx.fillStyle='#cb3422';ctx.beginPath();ctx.moveTo(-16,9);ctx.bezierCurveTo(-25,side*65, -90,side*(116+flap),-150,side*101);ctx.bezierCurveTo(-100,side*67,-63,side*25,-16,9);ctx.fill();
 stroke([[-16,9],[-25,side*53],[-74,side*(96+flap)],[-137,side*101]],'#f3a134',3,.72);
 for(let j=0;j<12;j++){const q=j/11;const bx=-18-q*82,by=side*(22+q*58),ang=side*(1.25+q*.93);feather(ctx,bx,by,62+q*39,ang,.12*side,'#ae2c20',j%3?'#e65a27':'#ffd376',alpha*(.62-q*.16));}
 }
 ctx.globalAlpha=alpha*.48;ctx.fillStyle='#d74724';ctx.beginPath();ctx.moveTo(-53,15);ctx.bezierCurveTo(-29,-7,-2,-7,9,-37);ctx.bezierCurveTo(13,-58,38,-62,47,-45);ctx.bezierCurveTo(21,-48,35,-19,5,7);ctx.bezierCurveTo(-17,28,-34,25,-53,15);ctx.fill();
 stroke([[-44,10],[-7,16],[26,-20],[20,-40]],'#ffd078',2.5,.92);
 stroke([[20,-40],[17,-59],[39,-63],[47,-45]],'#ffcc66',2,.9);
 ctx.globalAlpha=alpha*.9;ctx.fillStyle='#f9c15a';ctx.beginPath();ctx.moveTo(42,-48);ctx.lineTo(65,-43);ctx.lineTo(43,-39);ctx.closePath();ctx.fill();
 ctx.fillStyle='#6c2417';ctx.beginPath();ctx.arc(37,-48,2,0,Math.PI*2);ctx.fill();
 for(let j=0;j<3;j++)stroke([[24,-54],[13-j*4,-68],[29-j*7,-72],[17-j*8,-81-j*4]],'#f8b548',1.4,.8);
 ctx.restore();
}
export function phoenixEffects(ctx,event,time,sampleAt,target,dir,impactAge,hit){
 const i=names.indexOf(event.move);if(i<0||time<380||time>2240)return;
 const fade=1-ease((time-(i===7?1790:1260))/(i===7?420:400)),grow=ease((time-400)/260),now=sampleAt(time),tip=now.tip;
 const seed=n=>{const v=Math.sin(n*127.1+i*73.7)*43758.5;return v-Math.floor(v)};
 ctx.save();ctx.lineCap='round';
 const line=(a,b,c,w,alpha)=>{ctx.strokeStyle=c;ctx.lineWidth=w;ctx.globalAlpha=alpha;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()};
 // Live spear-tip samples make the fire ribbons follow each distinct action.
 for(let j=1;j<27;j++){const at=Math.min(time,i===7?1480:1320)-j*8;if(at<510||(i===7&&time>1480)||((i===4||i===6)&&time>1400))continue;const a=sampleAt(at).tip,b=sampleAt(at+8).tip,al=(1-j/28)*fade;
 line(a,b,'#d63d20',i===7?19:10,al*.13);line(a,b,'#ed7829',4,al*.58);line(a,b,'#ffd57b',1,al*.85);}
 for(let j=0;j<(i===7?65:30);j++){
 const age=(time-410-j*17);if(age<0)continue;const life=age%510,at=time-life;if(at>(i===7?1510:1330))continue;const s=sampleAt(at).tip,p=life/510;
 const x=s[0]-dir*p*(22+seed(j)*90),y=s[1]-p*(28+seed(j+90)*64)+Math.sin(p*5+j)*9;
 line([x,y],[x+dir*(2+4*(1-p)),y+3],'#e89532',1.4,(1-p)*fade*.8);
 if(j%4===0)feather(ctx,x,y,15+seed(j+33)*21,Math.PI*(dir===1?1:0)+Math.sin(j)*.5,.2,'#ac3024','#e84329',(1-p)*fade*.8);
 }
 if(i===2&&time<1200){for(let j=0;j<4;j++){ctx.globalAlpha=fade*.45;ctx.strokeStyle=j%2?'#ed6a25':'#efb953';ctx.lineWidth=1.3;ctx.beginPath();for(let s=0;s<=40;s++){const q=s/40,x=tip[0]-dir*q*135,y=tip[1]+Math.sin(q*12-time*.022+j*1.6)*q*17;s?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.stroke();}}
 if(i===3||i===7){const gather=i===7?ease((time-720)/230):0;for(let j=0;j<(i===7?28:15);j++){const spread=(j-(i===7?13.5:7))*7.5*(1-gather),length=55+seed(j)*70;const x=tip[0]-dir*(35+seed(j+40)*180)*(1-gather),y=tip[1]+spread;line([x-dir*length,y+12*(1-gather)],[x,y],'#c75529',1.4,fade*grow*.32);line([x-dir*9,y-3],[x,y],'#ffba55',1,fade*grow*.66);if(j%2===0)feather(ctx,x-dir*20,y,25,dir===1?-.15:Math.PI+.15,.15,'#9b3226','#e94b2c',fade*grow*.7);}}
 if(i===5){for(let j=0;j<25;j++){const a=j*2.399+time*.006,r=22+(j%6)*12;const x=tip[0]-dir*50+Math.cos(a)*r,y=tip[1]+Math.sin(a)*r*.65;feather(ctx,x,y,20+j%4*5,a+Math.PI/2,.16,'#ad2a24',j%4?'#e6432c':'#ffc45e',fade*grow*.8);}}
 if(i===4&&time<1390)phoenix(ctx,tip[0]-dir*38,tip[1]-35,.82,dir,grow*fade*.8,time,.72);
 if(i===6&&time<1400)phoenix(ctx,tip[0]-dir*42,tip[1]+20,.86,dir,grow*fade*.82,time,-.04);
 if(i===7&&time<1790){
 const descending=time>=1100,tilt=descending?Math.PI/2:time>830?-1.4:-.04;
 const x=descending?tip[0]-dir*36:tip[0]-dir*25,y=descending?tip[1]-52:tip[1]+18;
 phoenix(ctx,x,y,descending?1.08:.85,dir,grow*fade*.94*(1-ease((time-1410)/370)),time,tilt);
 if(time>=1180&&time<1500)for(let j=0;j<16;j++){const dx=(j-7.5)*7,top=tip[1]-200-seed(j)*90;line([tip[0]+dx,top],[tip[0]+dx*.35,tip[1]-15],'#ee8d30',j%3?1:3,fade*.3);}
 }
 if(hit&&impactAge>=0&&impactAge<(i===7?820:650)){const p=impactAge/(i===7?820:650),alpha=(1-p)*fade*ease(impactAge/65),count=i===7?78:i===4||i===6?24:12;
 for(let j=0;j<count;j++){const a=j*2.399,v=45+seed(j+11)*125,x=target[0]+Math.cos(a)*v*p*(i===7?1.7:1),y=i===7?329-Math.sin(Math.PI*p)*(50+seed(j+15)*130):target[1]+Math.sin(a)*v*p+p*p*50;
 feather(ctx,x,y,(i===7?26:16)+seed(j)*25,a+p*1.7,.16,'#9f2b21',j%3?'#e73f26':'#f4b74e',alpha*.9);
 line([x,y],[x-Math.cos(a)*9,y-Math.sin(a)*9],'#f5b54e',1,alpha*.65);}
 }
 ctx.restore();
}

export function phoenixTime(local,contact=950,move=names[0]){const beat=move===names[7]?1400:950;return local<=contact?local*beat/Math.max(1,contact):beat+local-contact;}
export function phoenixReplayTime(local,contact=950,move=names[0]){const beat=move===names[7]?1400:950;return local<=beat?local*Math.max(1,contact)/beat:contact+local-beat;}
