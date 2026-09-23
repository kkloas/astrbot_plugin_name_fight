import {twoBone} from './sampleMotion.js';
export const names=['损心诀','伤肺诀','摧肝肠诀','藏离诀','精失诀','意恍惚诀','气浮躁诀','绝技·七者皆伤'];
export const colors=['#286775','#9bafa5','#b58927','#547f58','#c65d30','#80529d','#399aa4'];
export const notes=['阴水先行 / 吞吐三拳 / 水纹暗涌','拔身进步 / 四拳交错 / 银白爆风','避锋转腰 / 反手钻拳 / 金风螺旋','绕背潜身 / 一推一送 / 延迟暗劲','拳骨凝光 / 双拳破罡 / 再进寸劲','上下虚晃 / 紫影换线 / 斜切灵台','交步压进 / 八拳骤雨 / 双拳终击','七色分流 / 拧合实拳 / 七层内震'];
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)},mix=(a,b,u)=>a+(b-a)*u;
export const beats=[[1020,1390,1800],[900,1190,1500,1800],[1100,1430,1800],[1310,1800],[1240,1800],[880,1110,1340,1570,1800],[820,960,1100,1240,1380,1520,1660,1800],[800,935,1070,1205,1340,1475,1610,1800]];
const pulse=(t,c,w=100)=>t<c?ease((t-c+w)/w):1-ease((t-c)/(w*1.35));
function strengths(i,t){let front=0,rear=0;beats[i].forEach((b,j)=>{const v=pulse(t,b,i===6||i===7?65:i===0?135:105);if(i===4||(i===6&&j===7)){front=Math.max(front,v);rear=Math.max(rear,v);}else if(j%2)rear=Math.max(rear,v);else front=Math.max(front,v);});return [front,rear];}
export function qishangMotion(event,time,travel){
 const i=names.indexOf(event.move);if(i<0)return;
 const prep=ease((time-120)/390),advance=ease((time-460)/540),recover=ease((time-2410)/360),active=prep*(1-recover),[f,r]=strengths(i,time);
 const final=pulse(time,1800,110),contact=travel+12;
 let x=contact*advance*(1-recover),h=68,lean=-15*prep+30*advance+8*f-7*r,lift=0,front=[32+44*f,-105-8*f],rear=[-9+77*r,-100+5*r],facing=1,opacity=1;
 if(i===0){x-=12*(1-f)*active;lean=7*active+15*f;front=[27+47*f,-104];rear=[-14+67*r,-109];}
 if(i===1){h=74;lift=-8*Math.max(f,r);front=[29+45*f,-124];rear=[-8+79*r,-87];lean=10*active+18*f;}
 if(i===2){const turn=ease((time-600)/370);h=60;lean=-28*active+48*turn;front=[24+49*f,-103+14*f];rear=[-34+106*r,-121+28*r];x-=Math.sin(clamp((time-500)/1000)*Math.PI)*23;}
 if(i===3){const bypass=ease((time-590)/320);x=(travel+180)*bypass;facing=time>=750&&time<2500?-1:1;opacity=time<740?1-ease((time-560)/150):time<940?ease((time-770)/170):1;h=56;lean=10+12*f;front=[27+48*f,-103];rear=[-6+65*r,-91];if(time>2380){opacity=1-ease((time-2380)/110);if(time>=2500){x=0;opacity=ease((time-2550)/220);}}}
 if(i===4){h=52;lean=-23*active+53*Math.max(f,r);front=[14+62*f,-88];rear=[4+66*r,-104];x-=25*(1-Math.max(f,r))*active;}
 if(i===5){const sw=Math.sin((time-600)*.013);h=65+sw*7*active;lean=sw*22*active+final*18;front=[25+51*f,-108-27*sw*f];rear=[-15+91*r,-100+24*sw*r];x+=sw*13*active;}
 if(i===6){h=59;lean=13*active+15*(f-r);front=[30+47*f,-101-9*f];rear=[-5+80*r,-111+14*r];x-=30*(1-ease((time-700)/1050))*active;}
 if(i===7){h=58;lean=-20*active+39*advance+12*final;front=[24+54*Math.max(f,final),-105];rear=[-15+82*r,-116];x-=22*(1-final)*active;}
 h=mix(74,h,active);lean=Math.max(-36,Math.min(36,lean*(1-recover)));front=front.map((v,j)=>mix(j===0?35:-100,v,active));rear=rear.map((v,j)=>mix(j===0?-25:-98,v,active));
 const hip=[0,-h],neck=[lean,-h-Math.sqrt(2704-lean*lean)],shoulders=[[neck[0]-10,neck[1]+6],[neck[0]+10,neck[1]+6]];
 const [be,bh]=twoBone(shoulders[0],rear,40,-1),[fe,fh]=twoBone(shoulders[1],front,40,1),stride=33+19*active;
 const [bk,bf]=twoBone(hip,[-stride,-Math.max(0,Math.sin(time*.012))*5*active],48,-1),[fk,ff]=twoBone(hip,[stride,0],48,-1);
 return {x,lift,opacity,blink:0,pose:{points:[[neck[0],neck[1]-21],neck,hip,be,bh,fe,fh,bk,bf,fk,ff],shoulders,sword:0,lean:0,facing}};
}
function fist(ctx,x,y,angle,size,color,alpha){
 ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.scale(size,size);ctx.globalAlpha=alpha;ctx.fillStyle=color;
 ctx.beginPath();ctx.moveTo(-19,-5);ctx.lineTo(-7,-6);ctx.lineTo(-4,-10);ctx.lineTo(7,-10);ctx.lineTo(12,-6);ctx.lineTo(12,3);ctx.lineTo(6,9);ctx.lineTo(-7,7);ctx.lineTo(-19,5);ctx.closePath();ctx.fill();
 ctx.strokeStyle='#eee7d2';ctx.lineWidth=.8;ctx.globalAlpha=alpha*.7;for(let j=0;j<3;j++){ctx.beginPath();ctx.moveTo(-1+j*4,-8);ctx.lineTo(j*4,-2);ctx.stroke();}ctx.restore();
}
// Same roll, lean and facing transforms as drawCurvedFigure, sampled this frame.
export function qishangBody(frame,dir){
 const pose=frame.pose,hip=pose.points[2],roll=pose.roll||0,lean=pose.lean||0;
 const world=p=>{const dx=p[0]-hip[0],dy=p[1]-hip[1],rx=hip[0]+dx*Math.cos(roll)-dy*Math.sin(roll),ry=hip[1]+dx*Math.sin(roll)+dy*Math.cos(roll);return [frame.x+dir*(pose.facing||1)*(rx*Math.cos(lean)-ry*Math.sin(lean)),324+frame.lift+rx*Math.sin(lean)+ry*Math.cos(lean)];};
 const neck=world(pose.points[1]),waist=world(hip),len=Math.hypot(waist[0]-neck[0],waist[1]-neck[1])||1,down=[(waist[0]-neck[0])/len,(waist[1]-neck[1])/len];
 return {center:[mix(neck[0],waist[0],.48),mix(neck[1],waist[1],.48)],down,right:[down[1],-down[0]]};
}
export const qishangTime=(t,c=950)=>t<=c?t*1800/Math.max(1,c):1800+(t-c)/.68;
export const qishangReplayTime=(t,c=950)=>t<=1800?t*Math.max(1,c)/1800:c+(t-1800)*.68;
export function qishangEffects(ctx,event,time,sampleAt,target,dir,impactAge,hit,receiver){
 const i=names.indexOf(event.move);if(i<0||time<470||time>2830)return;
 const seed=n=>{const x=Math.sin(n*127.1+i*19.7)*43758.54;return x-Math.floor(x)},fade=1-ease((time-2310)/450),grow=ease((time-470)/250),color=colors[i]||colors[0];
 const hands=t=>{const frame=sampleAt(t).frame,d=dir*(frame.pose.facing||1);return {front:[frame.x+d*frame.pose.points[6][0],324+frame.lift+frame.pose.points[6][1]],rear:[frame.x+d*frame.pose.points[4][0],324+frame.lift+frame.pose.points[4][1]],frame,d};};
 const now=hands(time),origin=now.front,d=now.d;
 const line=(pts,c,w,a)=>{ctx.globalAlpha=clamp(a);ctx.strokeStyle=c;ctx.lineWidth=w;ctx.beginPath();pts.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke();};
 const stream=(from,to,kind,c,alpha,phase,width=1)=>{
  for(let j=0;j<(kind===6?13:kind===1?9:7);j++){const pts=[],offset=(j-3)*4;
   for(let k=0;k<=32;k++){const q=k/32,s=Math.sin(q*Math.PI),x=mix(from[0],to[0],q);let y=mix(from[1],to[1],q)+offset*s;
    if(kind===0)y+=Math.sin(q*13+phase*7+j*.65)*s*(8+j*1.3);
    else if(kind===2)y+=Math.sin(q*25-phase*12+j*.7)*s*(12+j*1.4);
    else if(kind===3)y+=Math.sin(q*7+j+phase)*s*15;
    else if(kind===5)y+=Math.sin(q*9+phase*10+j*.7)*s*(20+j*2);
    else if(kind===6)y+=Math.sin(j*2.4)*s*25;
    else y+=Math.sin(j*2.3)*s*11;
    pts.push([x,y]);}
   if(j%3===0){
    line(pts,c,width*9,alpha*.09);
    for(let n=1;n<pts.length;n++)line([pts[n-1],pts[n]],c,width*(1+Math.sin(n/32*Math.PI)*3.8),alpha*.3);
    line(pts.slice(9,22),'#313e38',width*.75,alpha*.26);
   }
   line(pts,c,width*(j%3===0?2.3:1),alpha*(j%3===0?.8:.42));
  }
 };
 ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
 // Every afterimage follows an authored extension and retraction beat.
 for(let j=0;j<beats[i].length;j++){
  const b=beats[i][j],age=time-b;if(age < -180||age>320)continue;
  const p=clamp((age+180)/300),a=(1-ease(Math.max(0,age)/320))*grow*fade,c=i===7?colors[j%7]:color;
  const at=hands(Math.max(0,b-115)),from=j%2?at.rear:at.front,goal=[target[0]-dir*8,target[1]+(i===5?Math.sin(j*2.4)*39:i===1?(j%2?-22:16):i===6?(j%3-1)*15:0)];
  const tip=[mix(from[0],goal[0],ease(p)),mix(from[1],goal[1],ease(p))],kind=i===7?j%7:i;
  stream(from,tip,kind,c,a*.75,p,kind===4?2:1);
  for(let n=0;n<3;n++){const q=Math.max(0,p-n*.13),x=mix(from[0],goal[0],ease(q)),y=mix(from[1],goal[1],ease(q));fist(ctx,x,y,Math.atan2(goal[1]-from[1],goal[0]-from[0]),1.22-n*.16,c,a*(.58-n*.14));}
 }
 // Yin water precedes the first soft strike; recoil trails remain translucent.
 if(i===0&&time<1810){const early=ease((time-500)/420);stream(origin,[mix(origin[0],target[0],early),target[1]],0,color,grow*fade*.5,time*.002);}
 if(i===2&&time>700&&time<2020){for(let j=0;j<3;j++){const pts=[];for(let n=0;n<=60;n++){const a=n/60*Math.PI*4+time*.008+j*2.1,r=6+n*.4;pts.push([target[0]-d*38+Math.cos(a)*r*.7,target[1]+Math.sin(a)*r]);}line(pts,color,1.3,fade*.25);}}
 if(i===3&&time>860&&time<2100){stream(now.rear,[target[0],target[1]+10],3,color,fade*.35,time*.001);}
 if(i===4){const charge=(1-ease((time-1780)/100))*grow;for(const hand of [now.front,now.rear]){ctx.globalAlpha=charge*.22;ctx.fillStyle=color;ctx.beginPath();ctx.arc(...hand,13+Math.sin(time*.025)*2,0,Math.PI*2);ctx.fill();}}
 if(i===5){for(let j=0;j<6;j++){const a=j*1.1+time*.004,r=30+j*4;fist(ctx,target[0]-dir*(45+Math.cos(a)*r),target[1]+Math.sin(a)*r,-Math.sin(a)*.3,1.1,color,grow*fade*.14);}}
 // Seven strands stay distinct until the final convergence at the real fist.
 if(i===7&&time>760&&time<2090){const converge=ease((time-1480)/320);for(let j=0;j<7;j++){
  const a=j*Math.PI*2/7+time*.002,from=[now.frame.x-dir*(100+Math.cos(a)*80),195+Math.sin(a)*116],end=[origin[0]+d*14,origin[1]];
  stream(from,end,j,colors[j],fade*(.3+.4*converge),time*.002+j,1.3);
  const px=mix(from[0],end[0],converge),py=mix(from[1],end[1],converge);fist(ctx,px,py,0,.85,colors[j],fade*.52*(1-converge));
 }}
 // Internal forces stay in the victim's torso coordinate system as they recoil.
 if(hit&&receiver&&impactAge>=0&&impactAge<830){
  const body=qishangBody(receiver,-dir);ctx.save();ctx.transform(...body.right,...body.down,...body.center);
  const count=i===7?7:3;for(let j=0;j<count;j++){const age=impactAge-j*(i===7?77:95);if(age<0||age>440)continue;const p=age/440,kind=i===7?j:i,c=colors[kind],a=(1-p)*.85,spread=ease(p*5);
   ctx.save();ctx.beginPath();ctx.ellipse(0,0,23,35,0,0,Math.PI*2);ctx.clip();
   for(let n=0;n<7;n++){
    const pts=[];for(let k=0;k<=32;k++){const u=k/32;let x=0,y=0;
     if(kind===0){y=(u-.5)*63;x=(n-3)*4+Math.sin(u*12-age*.012+n)*3*spread;}
     if(kind===1){const side=n%2?1:-1;x=side*Math.sin(u*Math.PI)*20*spread;y=(n-3)*7+u*13;}
     if(kind===2){const angle=u*Math.PI*4+n*.9+age*.012,r=(3+u*19)*spread;x=Math.cos(angle)*r;y=Math.sin(angle)*r*1.3;}
     if(kind===3){y=(u-.5)*56;x=Math.sin(u*7+n*.7)*12*spread;if(k%5===0&&pts.length){line(pts,c,.9,a*.65);pts.length=0;}}
     if(kind===4){y=(u-.5)*65;x=(n-3)*4+Math.sin(Math.floor(u*8)*2.4+n)*5*spread;}
     if(kind===5){const angle=u*Math.PI*2+age*.009+n;x=Math.cos(angle)*(5+n*2.1)*spread;y=Math.sin(angle)*(8+n*3);}
     if(kind===6){y=(u-.5)*62;x=(n-3)*5+u*10*spread;if(k%9===0&&pts.length){line(pts,c,1.4,a);pts.length=0;}}
     pts.push([x,y]);
    }line(pts,c,kind===4?1.5:1,a);
   }ctx.restore();
   // Expanding water rings, pressure fans, vortices or fractured arcs per force.
   for(let ring=0;ring<3;ring++){const r=(8+ring*9+36*p),pts=[];for(let n=0;n<=42;n++){const t=n/42*Math.PI*(kind===1?1.35:1.8)+ring*.9+age*.004,rough=kind===4?Math.sin(n*2.4)*3:0;pts.push([Math.cos(t)*(r+rough),Math.sin(t)*(r*.64+rough)]);}line(pts,c,ring===0?1.6:.8,a*(kind===3?.18:.4));}
   for(let n=0;n<(i===7?16:30);n++){const angle=n*2.399+j*.7,r=(12+seed(n+j*40)*47)*p,x=Math.cos(angle)*r,y=Math.sin(angle)*r+p*p*15;
    if(kind===0||kind===3){ctx.globalAlpha=a*.65;ctx.fillStyle=c;ctx.beginPath();ctx.ellipse(x,y,1.2+seed(n)*1.4,2.5,angle,0,Math.PI*2);ctx.fill();}
    else if(kind===4){line([[x-2,y+3],[x+3,y],[x-1,y-3]],c,1.3,a*.8);}
    else line([[x,y],[x+Math.cos(angle)*6,y+Math.sin(angle)*6]],c,1,a*.7);
   }
  }ctx.restore();
 }
 ctx.restore();
}
