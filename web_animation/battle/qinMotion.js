export const names=['拨弦','裂帛','魔音入脑','乱心','摄魂','断肠','十面埋伏','绝技·广陵绝响'];
export const notes=['单指勾弦 / 同心音浪','抬腕扫弦 / 交错音刃','捻指泛音 / 螺旋贯耳','双手错拨 / 逆向波纹','按弦牵引 / 青墨游丝','沉肩重拨 / 双重心震','轮指连奏 / 扇形叠浪','双手蓄势 / 一线绝响'];
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>{x=clamp(x);return x*x*(3-2*x)};
export function qinPose(pose,index,t){
 const p={...pose,points:pose.points.map(p=>[...p]),lean:0,sword:0};
 const prep=ease(t/540),fire=ease((t-570)/100),recover=ease((t-1120)/500);
 const energy=(prep-fire*.65)*(1-recover), sweep=fire*(1-recover);
 const multi=index===3||index===6?Math.sin(Math.max(0,t-570)/52)*(t>570&&t<1000?1:0):0;
 const wide=[12,32,8,24,16,27,35,43][index];
 p.points=[[energy*-8+sweep*5,-143+energy*6],[energy*-5,-121+energy*5],[-3,-67],[-25,-104],[-30,-85],[24,-109],[30,-86],[-20,-34],[-36,0],[20,-34],[36,0]];
 p.points[4]=[-30+(index===4?energy*20:multi*12),-85-energy*(index===7?27:8)];
 p.points[6]=[26-energy*18+sweep*wide+multi*15,-86-energy*(index===1||index===7?31:14)+sweep*(index===2?-9:3)];
 p.points[5]=[17+p.points[6][0]*.18,-109-energy*8];
 return p;
}
export function qinFX(ctx,index,t,sx,tx,hit){
 if(t<240||t>1840)return;
 const palettes=[['#4e8994','#c0aa66'],['#536e83','#c2dce3'],['#655c86','#a0b6d2'],['#6c6488','#66a6a8'],['#39786d','#a6c5a0'],['#91453f','#c79966'],['#467e8b','#b1c7bd'],['#597b90','#d4b571']];
 const [ink,gold]=palettes[index],sy=241,ty=index===2?190:231;
 const direction=Math.sign(tx-sx)||1,dist=Math.abs(tx-sx),age=t-950;
 const fade=1-ease((t-1190)/570),flight=clamp((t-650)/300);
 ctx.save();ctx.translate(sx,0);ctx.scale(direction,1);ctx.lineCap='round';ctx.lineJoin='round';
 const line=(pts,color=ink,width=1,alpha=1)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.globalAlpha=alpha*fade;ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke()};
 const ring=(x,y,rx,ry,color=ink,alpha=.5,width=1,rot=0)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.globalAlpha=alpha*fade;ctx.beginPath();ctx.ellipse(x,y,Math.max(.1,rx),Math.max(.1,ry),rot,0,Math.PI*2);ctx.stroke()};
 const dot=(x,y,r,color,alpha)=>{ctx.globalAlpha=alpha*fade;ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill()};
 const glow=(x,y,r,color,alpha)=>{ctx.globalAlpha=alpha*fade;const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,color);g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.fillRect(x-r,y-r,r*2,r*2)};
 const seed=n=>{const v=Math.sin(n*127.1+index*311.7)*43758.5453;return v-Math.floor(v)};
 // Original crescent silhouette, with translucent body and separate bright edge.
 const crescent=(x,y,r,rotation=0,a=.6,w=8,color=ink)=>{ctx.save();ctx.translate(x,y);ctx.rotate(rotation);ctx.globalAlpha=a*fade;ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(-r*.37,-r);ctx.bezierCurveTo(r*.8,-r*.48,r*.8,r*.48,-r*.37,r);ctx.bezierCurveTo(r*.44,r*.38,r*.44,-r*.38,-r*.37,-r);ctx.fill();ctx.strokeStyle=color;ctx.lineWidth=w*.23;ctx.beginPath();ctx.moveTo(-r*.37,-r);ctx.bezierCurveTo(r*.8,-r*.48,r*.8,r*.48,-r*.37,r);ctx.stroke();ctx.globalAlpha=a*.7*fade;ctx.strokeStyle='#eff0d9';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(-r*.32,-r*.92);ctx.bezierCurveTo(r*.71,-r*.44,r*.71,r*.44,-r*.32,r*.92);ctx.stroke();ctx.restore()};
 // Quiet inward dust becomes a sharp string vibration at release.
 const charge=ease((t-240)/380)*(1-ease((t-650)/130));
 if(charge>0){glow(-8,sy,65,gold,charge*.19);for(let j=0;j<27;j++){const a=j*2.399,r=(1-charge)*70+12+seed(j)*23;dot(-8+Math.cos(a)*r,sy+Math.sin(a)*r*.55,.7+seed(j+30)*1.6,j%3?ink:gold,charge*.65)}for(let j=0;j<3;j++)ring(-8,sy,20+j*15,5+j*4,gold,charge*.25);}
 if(t<650){ctx.restore();return;}
 const x=dist*flight,y=sy+(ty-sy)*flight;
 const vibration=(1-ease((t-700)/330));
 for(let j=0;j<7;j++){const pts=[];for(let k=0;k<=30;k++){const u=k/30;pts.push([-83+u*111,sy-6+j*2+Math.sin(u*Math.PI)*Math.sin(u*27+t*.09+j)*2.7*vibration])}line(pts,gold,.8,vibration*.85)}
 // Supporting broad waves preserve the volume of the original effects.
 const count=index===6?8:index===7?6:4;
 for(let j=0;j<count;j++){
 const start=650+j*(index===6?24:18),p=clamp((t-start)/(950-start));if(t<start)continue;
 const trailAge=Math.max(0,age),xx=dist*p-j*13-Math.min(32,trailAge*.04);
 const rr=(index===7?83:index===6?58:36)+j*(index===7?11:7);
 const rotation=index===1?(j%2?-.7:.65):index===2?-.2+p*1.5:index===3?(j%2?-1:1)*p*.65:0;
 crescent(xx,sy+(ty-sy)*p+(index===6?(j-count/2)*13*Math.sin(p*Math.PI):0),rr,rotation,(index===4?.18:.4)*(1-j/(count+3)),8);
 }
 // Air streaks and gold flecks follow the advancing front, never precede it.
 for(let j=0;j<44;j++){const u=seed(j+80),xx=x*u,spread=Math.sin(u*Math.PI)*(index===6?78:36);const yy=sy+(ty-sy)*u*flight+(seed(j+140)-.5)*spread*2;const a=(.2+seed(j+210)*.5)*(1-ease((t-1060)/400));line([[xx-8-seed(j+50)*23,yy],[xx,yy]],j%4?ink:gold,j%5?.7:1.6,a);if(j%3===0)dot(xx,yy,1+seed(j)*1.3,gold,a);}
 if(index===0){for(let j=0;j<5;j++)ring(x-j*27,y,14+j*7,35+j*12,j%2?ink:gold,.62-j*.08,1.5);glow(x,y,65,gold,.12);}
 if(index===1){for(let j=0;j<4;j++){const xx=x-j*24,rot=j%2?-.62:.62;crescent(xx,y,62+j*9,rot,.75,15,j%2?ink:gold);line([[xx-65,y+(j%2?1:-1)*48],[xx+17,y]],'#f1edcf',1.4,.7)}}
 if(index===2||index===3||index===4){const n=index===4?9:6;for(let j=0;j<n;j++){const pts=[];for(let k=0;k<=85;k++){const u=k/85,env=Math.sin(u*Math.PI),a=u*(index===3?25:17)+j*Math.PI*2/n+t*(j%2&&index===3?-.014:.012);pts.push([x*u,sy+(ty-sy)*flight*u+Math.sin(a)*env*(index===4?44:29)+Math.cos(a*.5)*env*10])}line(pts,j%3?ink:gold,j%3?1.4:2.2,.65);if(j<3)line(pts,ink,7,.055)}
 if(index===2&&age>=0&&hit){for(let j=0;j<4;j++)ring(dist,ty,24+j*9,10+j*5,j%2?gold:ink,.75,1.7,Math.sin(t*.007+j)*.8)}
 if(index===3&&age>=0&&hit){for(let j=0;j<3;j++){ring(dist,ty,30+j*16,18+j*7,j%2?gold:ink,.6,1.4,(j%2?1:-1)*(t*.006));}}
 if(index===4&&age>=0&&hit){for(let j=0;j<7;j++){const pts=[];for(let k=0;k<=50;k++){const u=k/50,a=u*8+j*.9+t*.006;pts.push([dist+Math.sin(a)*(22+u*20),175+u*128])}line(pts,j%2?ink:gold,1.2,.6)}for(let j=0;j<30;j++){const a=j*2.399+t*.001,r=18+seed(j)*45;dot(dist+Math.cos(a)*r,ty+Math.sin(a)*r*1.3,1.2,gold,.65)}}
 }
 if(index===5){for(let j=0;j<2;j++){ring(x-j*24,y,22+j*11,49+j*16,j?ink:gold,.65,2.5);const xx=x-j*24;line([[xx-68,y],[xx-32,y],[xx-20,y-14],[xx-8,y+22],[xx+2,y-35],[xx+14,y+8],[xx+32,y]],ink,3,.85)}if(age>=0&&hit){for(let beat=0;beat<2;beat++){const a=clamp((age-beat*130)/320);if(age<beat*130)continue;glow(dist,ty,48+a*22,ink,(1-a)*.32);ring(dist,ty,12+a*73,16+a*81,ink,(1-a)*.85,3-a*2);}}}
 if(index===6){for(let j=0;j<13;j++){const a=(j-6)*.12;const end=[x,sy+Math.sin(a)*Math.sin(flight*Math.PI)*130+(ty-sy)*flight];line([[end[0]-45,end[1]-Math.sin(a)*18],end],j%3?ink:gold,1.6,.7);dot(...end,1.4,gold,.8)}ring(x,y,35,126,ink,.32,2);}
 if(index===7){glow(x,y,100,gold,.2);line([[0,sy],[x,y]],ink,22,.07);line([[0,sy],[x,y]],gold,9,.45);line([[0,sy],[x,y]],'#f7f0d6',2.3,.95);crescent(x,y,122,0,.65,15);if(age>=0){const p=ease(age/180);const pts=Array.from({length:22},(_,j)=>[j/21*dist*p,329+(j===0?0:(seed(j+400)-.5)*13)]);line(pts,'#465146',2.4,.75);for(let j=2;j<19;j+=3){const q=pts[j];line([q,[q[0]-8,q[1]+12],[q[0]+4,q[1]+17]],ink,1,.5)}ring(dist,329,20+age*.26,4+age*.025,gold,.6*(1-clamp(age/600)),2)}}
 // Time-derived bursts remain identical while paused or seeking.
 if(age>=0&&hit){const p=clamp(age/640),burst=index===7?95:index===6?76:54;
 glow(dist,ty,55, gold,(1-clamp(age/220))*.38);
 for(let j=0;j<52;j++){const a=seed(j+600)*Math.PI*2,r=10+Math.pow(p,.7)*(burst+seed(j+650)*52),px=dist+Math.cos(a)*r,py=ty+Math.sin(a)*r*.8+p*p*25;const alpha=(1-p)*(.35+seed(j+700)*.55);if(j%3===0){dot(px,py,1+seed(j+750)*(index===5?3:1.7),index===5?ink:gold,alpha)}else{line([[px-Math.cos(a)*(4+seed(j)*11),py-Math.sin(a)*7],[px,py]],j%4?ink:gold,.65+seed(j)*1.1,alpha)}}
 for(let j=0;j<3;j++){const a=clamp((age-j*55)/460);if(age<j*55)continue;ring(dist,ty,8+a*(burst+20),12+a*burst, j%2?gold:ink,(1-a)*.5,1.6)}
 }
 ctx.restore();
}

// Map the authored contact to the recorded outcome without changing replay events.
export function qinTime(local, contact = 950) {
    return local <= contact ? local * 950 / Math.max(1, contact) : 950 + local - contact;
}
