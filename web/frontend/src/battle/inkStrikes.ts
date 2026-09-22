import { unit, ease, type impactFor } from './choreography';
import type { Technique, Weapon } from './martialVisuals';

type Point=[number,number];
type Impact=ReturnType<typeof impactFor>;
const ink=(t:Technique)=>t.color || (t.flourish==='crimson'?'#873a30':t.flourish==='phantom'?'#3c5558':'#303d38');

function stroke(ctx:CanvasRenderingContext2D, a:Point,b:Point,color:string,width:number) {
  ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();
}

// Tapered filled ribbons read as brush strokes, rather than uniform wire arcs.
function ribbon(ctx:CanvasRenderingContext2D,x:number,y:number,r:number,rotation:number,progress:number,thickness:number,color:string) {
  ctx.save();ctx.translate(x,y);ctx.rotate(rotation);ctx.scale(1,.64);
  const start=-2.45,end=start+3.35*ease(progress);
  ctx.beginPath();
  for(let i=0;i<=28;i++) {
    const f=i/28,a=start+(end-start)*f;
    const radius=r+Math.sin(f*Math.PI)*thickness;
    const px=Math.cos(a)*radius,py=Math.sin(a)*radius;
    if(i===0) ctx.moveTo(px,py);else ctx.lineTo(px,py);
  }
  for(let i=28;i>=0;i--) {
    const f=i/28,a=start+(end-start)*f, radius=r-Math.sin(f*Math.PI)*thickness*.32;
    ctx.lineTo(Math.cos(a)*radius,Math.sin(a)*radius);
  }
  ctx.closePath();ctx.fillStyle=color;ctx.fill();
  ctx.strokeStyle='rgba(250,248,233,.72)';ctx.lineWidth=1.3;
  ctx.beginPath();ctx.arc(0,0,r,start,end);ctx.stroke();ctx.restore();
}

function wavefront(ctx:CanvasRenderingContext2D,r:number,width:number,color:string,rotation=0) {
  ctx.save();ctx.rotate(rotation);ctx.fillStyle=color;
  ctx.beginPath();ctx.moveTo(-r*.3,-r);
  ctx.bezierCurveTo(r*.75+width,-r*.5,r*.75+width,r*.5,-r*.3,r);
  ctx.bezierCurveTo(r*.75-width,r*.5,r*.75-width,-r*.5,-r*.3,-r);ctx.fill();
  ctx.strokeStyle='rgba(250,248,233,.8)';ctx.lineWidth=1;
  ctx.beginPath();ctx.moveTo(-r*.3,-r);ctx.bezierCurveTo(r*.75,-r*.5,r*.75,r*.5,-r*.3,r);ctx.stroke();
  ctx.restore();
}

export function drawPreparation(ctx:CanvasRenderingContext2D,t:Technique,x:number,dir:number,local:number,ranged:boolean) {
  if(local<140 || local>950) return;
  const phase=unit((local-140)/610),fade=Math.sin(phase*Math.PI);
  ctx.save();ctx.globalAlpha=fade*(t.weight>=1.5?.55:.22);
  ctx.strokeStyle=ink(t);ctx.lineWidth=1;
  for(let i=0;i<7;i++) {
    const angle=i*2.399, radius=80-phase*47;
    const px=x+Math.cos(angle)*radius,py=250+Math.sin(angle)*radius*.5;
    stroke(ctx,[px,py],[px+Math.cos(angle)*12,py+Math.sin(angle)*6],ink(t),1+i%2);
  }
  if(t.weight>=1.5) {
    ctx.beginPath();ctx.ellipse(x,327,40+phase*30,5+phase*3,0,0,Math.PI*2);ctx.stroke();
    if(ranged) ribbon(ctx,x+dir*12,244,30+phase*25,-phase*2,phase,4,ink(t));
  }
  ctx.restore();
}

export function drawTechnique(ctx:CanvasRenderingContext2D,t:Technique,weapon:Weapon,
  origin:Point,target:Point,dir:number,age:number,force=0) {
  if(age<80 || age>830) return;
  const ranged=weapon==='needles'||weapon==='zither';
  const start=t.motion==='flurry'?220:270;
  if(!ranged && age<start) return;
  const p=unit((age-start)/(400-start)),fade=unit((830-age)/270);
  const color=ink(t),weight=t.weight*(1+force*.3);
  ctx.save();ctx.lineCap='round';ctx.globalAlpha=fade;
  if(weapon==='needles') {
    const rain=t.pattern==='rain',focus=t.pattern==='focus';
    const count=focus?1:Math.round(weight*(rain?15:8));
    for(let i=0;i<count;i++) {
      const lag=(i%5)*12;
      const f=unit((age-110-lag)/(290-lag));
      if(f>=1 && age>560) continue;
      const spread=(i-(count-1)/2)*(rain?5:9);
      const swirl=t.pattern==='spiral'?Math.sin(f*Math.PI*3+i)*22*Math.sin(f*Math.PI):0;
      const px=origin[0]+(target[0]-origin[0])*f;
      const py=origin[1]+(target[1]-origin[1])*f+spread*Math.sin(Math.PI*f)-
        (rain?100*Math.sin(f*Math.PI):0)+swirl;
      const angle=Math.atan2(target[1]-py,target[0]-px || dir);
      const len=focus?55:19;
      stroke(ctx,[px-Math.cos(angle)*len,py-Math.sin(angle)*len],[px,py],color,focus?3:1.7);
      stroke(ctx,[px-Math.cos(angle)*(len+30),py-Math.sin(angle)*(len+30)],[px-Math.cos(angle)*len,py-Math.sin(angle)*len],'rgba(55,75,68,.24)',1);
    }
    if(age>=400) {
      ctx.globalAlpha=fade*unit((630-age)/230)*.55;
      for(let i=0;i<Math.min(count,18);i++) {
        const drift=(age-400)/8;
        const x=target[0]+dir*drift*(.5+i%3),y=target[1]+(i-count/2)*3+drift*drift*.03;
        stroke(ctx,[x-dir*12,y-5],[x,y],color,1.2);
      }
    }
  } else if(weapon==='zither') {
    const big=t.pattern==='crescendo';
    const count=big?5:t.pattern==='fan'?6:3;
    for(let i=0;i<count;i++) {
      const f=unit((age-90-i*28)/(310-i*28));
      const x=origin[0]+(target[0]-origin[0])*f;
      const y=target[1]+(t.pattern==='fan'?(i-2.5)*18*Math.sin(f*Math.PI):0);
      ctx.save();ctx.translate(x,y);ctx.scale(dir,1);
      const r=(big?75:32)+i*7;
      const rotate=t.pattern==='cross'?(i%2?-.65:.65):t.pattern==='spiral'?f*2:0;
      wavefront(ctx,r,(big?5:2)*weight,color,rotate);
      ctx.restore();
    }
  } else if(t.trail==='dust' && weapon==='unarmed') {
    ctx.save();ctx.translate(origin[0],318);ctx.scale(dir,1);
    ribbon(ctx,20,0,64,0,p,6*weight,color);
    for(let i=0;i<12;i++) {
      const spread=p*(12+i*7);
      stroke(ctx,[spread,-2],[spread+8,-3-Math.sin(i)*p*11],color,1.2);
    }
    ctx.restore();
  } else if(t.trail==='wave') {
    const x=origin[0]+(target[0]-origin[0])*p;
    ctx.save();ctx.translate(x,target[1]);ctx.scale(dir,1);
    for(let i=0;i<3;i++) {ctx.translate(-12,0);wavefront(ctx,28+i*9,3*weight*p,color);}
    ctx.restore();
  } else {
    const x=origin[0]+(target[0]-origin[0])*.75*p;
    ctx.save();ctx.translate(x,origin[1]+(target[1]-origin[1])*p);ctx.scale(dir,1);
    const point=t.trail==='point';
    if(point) {
      const count=t.pattern==='fan'?7:t.motion==='flurry'?4:1;
      for(let i=0;i<count;i++) {
        const offset=(i-(count-1)/2)*15;
        const reach=weapon==='spear'?185:weapon==='brush'?82:133;
        ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(52*p,offset);
        ctx.quadraticCurveTo(-reach*.35,offset-5*weight,-reach,offset-2);
        ctx.quadraticCurveTo(-reach*.2,offset+9*weight,52*p,offset);ctx.fill();
        stroke(ctx,[-reach*.7,offset],[52*p,offset],'rgba(248,247,236,.8)',1.2);
      }
    } else {
      const count=t.motion==='flurry'?4:t.pattern==='cross'?2:1;
      for(let i=0;i<count;i++) {
        const q=unit((age-135-i*40)/(265-i*40));
        const r=(weapon==='spear'?114:weapon==='brush'?57:86)+i*9;
        const rotation=t.motion==='cleave'?-1.1:t.motion==='rise'?2.8:t.motion==='sweep'?0:
          t.pattern==='wheel'?q*2:t.pattern==='fall'?-1.2+(i%2)*.6:t.pattern==='cross'?(i%2?1.5:-.6):-.25+i*.45;
        ribbon(ctx,-22,t.motion==='sweep'?54:0,r,rotation,q,(weapon==='blade'?11:7)*weight,color);
      }
    }
    if(t.trail==='vortex' || t.pattern==='spiral') {
      for(let i=0;i<3;i++) ribbon(ctx,-10,0,30+i*20,age/180+i*2,p,3,color);
    }
    ctx.restore();
  }
  if(t.flourish || t.trail==='dust' || t.weight>=1.5) {
    ctx.globalAlpha=fade*.6;
    for(let i=0;i<14;i++) {
      const a=i*2.399,r=18+p*60;
      const x=target[0]+Math.cos(a)*r+dir*p*20;
      const y=(t.trail==='dust'?319:target[1])+Math.sin(a)*r*.7;
      ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(x,y,t.flourish==='plum'?4:2,1.3,a+p,0,Math.PI*2);ctx.fill();
    }
  }
  ctx.restore();
}

export function drawImpact(ctx:CanvasRenderingContext2D,x:number,y:number,dir:number,age:number,impact:Impact,seed:number) {
  if(!impact.hit || age<0 || age>650) return;
  const p=unit(age/650),burst=ease(age/150),fade=Math.pow(1-p,1.5);
  ctx.save();ctx.translate(x,y);ctx.globalAlpha=fade;
  const force=impact.force,color=impact.heavy?'#813c30':'#35453d';
  const count=Math.round(9+force*19);
  for(let i=0;i<count;i++) {
    const a=i*2.399+seed,r=(14+burst*(34+force*70))*(.45+(i%5)/7);
    const px=Math.cos(a)*r,py=Math.sin(a)*r*.7+p*p*35;
    ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(px,py,1.4+(i%3)*1.2,1+i%2,a,0,Math.PI*2);ctx.fill();
    if(i%3===0) stroke(ctx,[px*.5,py*.5],[px,py],color,1.2);
  }
  if(impact.heavy) {
    ctx.save();ctx.scale(dir,1);
    ribbon(ctx,-12,0,25+burst*64,1.8,1,8*(1-p),color);
    ctx.restore();
    ctx.strokeStyle='rgba(56,63,51,.4)';ctx.lineWidth=1.5;
    ctx.beginPath();ctx.ellipse(0,324-y,25+burst*95,4+burst*10,0,0,Math.PI*2);ctx.stroke();
    for(let i=0;i<6;i++) stroke(ctx,[(i-3)*12,324-y],[(i-3)*(15+burst*13),324-y-burst*(6+i%3*7)],color,1);
  }
  ctx.restore();
}

// Cosmetic accents only. The caller supplies the real contact outcome; a snowy
// strike does not imply freezing, and a missed thrust cannot spawn a hit burst.
export function drawSampleAccent(ctx:CanvasRenderingContext2D,kind:'sword'|'spear'|'kick',
  tip:Point,target:Point,dir:number,age:number,impact:Impact) {
  if(age < -150 || age > 460) return;
  const charge=ease((age+150)/150),fade=1-ease(Math.max(0,age)/460);
  const snow=kind==='sword',power=1+impact.force*.5;
  const length=(kind==='spear'?180:kind==='sword'?145:75)*charge;
  ctx.save();ctx.translate(...tip);ctx.scale(dir,1);
  ctx.globalAlpha=fade*.7;
  ctx.fillStyle=snow?'rgba(116,196,224,.48)':'rgba(71,91,84,.3)';
  ctx.beginPath();ctx.moveTo(16*charge,0);
  ctx.bezierCurveTo(-length*.25,-13*power,-length*.65,-8*power,-length,1);
  ctx.bezierCurveTo(-length*.55,11*power,-length*.2,7*power,16*charge,0);ctx.fill();
  ctx.shadowColor=snow?'#b8edff':'#e4eadc';ctx.shadowBlur=snow?10:3;
  stroke(ctx,[-length*.8,1],[14*charge,0],snow?'#f1fcff':'#f0f0df',2.5*power);
  ctx.shadowBlur=0;
  if(kind!=='sword') {
    for(let i=0;i<3;i++) {
      ctx.globalAlpha=fade*(.38-i*.08);
      ctx.beginPath();ctx.strokeStyle='#70867d';ctx.lineWidth=2-i*.4;
      ctx.ellipse(-i*14,0,8+i*4,(18+i*9)*charge,0,-1.15,1.15);ctx.stroke();
    }
  }
  if(snow) {
    for(let i=0;i<24;i++) {
      const seed=(i*.61803398875)%1;
      const drift=Math.max(0,age)*(.018+(i%4)*.009);
      const x=-length*seed+drift*(i%2?1:-1);
      const y=Math.sin(i*2.399)*(12+seed*30)+Math.sin(age/130+i)*8+drift*.45;
      const radius=2.2+(i%4)*1.1;
      ctx.globalAlpha=fade*(.4+(i%3)*.2)*charge;
      ctx.strokeStyle=i%3?'#eefbff':'#70b7d0';ctx.fillStyle='#eefbff';ctx.lineWidth=1;
      if(i%3===0) {
        ctx.save();ctx.translate(x,y);ctx.rotate(i+age/650);
        for(let ray=0;ray<3;ray++) {
          const a=ray*Math.PI/3;
          stroke(ctx,[-Math.cos(a)*radius,-Math.sin(a)*radius],[Math.cos(a)*radius,Math.sin(a)*radius],i%2?'#effcff':'#70b7d0',1);
        }
        ctx.restore();
      } else {ctx.beginPath();ctx.arc(x,y,radius*.5,0,Math.PI*2);ctx.fill();}
    }
  }
  ctx.restore();
  if(!impact.hit || age<0) return;
  const burst=ease(age/200),hitFade=1-ease(age/400);
  ctx.save();ctx.translate(...target);ctx.scale(dir,1);ctx.globalAlpha=hitFade*.65;
  ctx.strokeStyle=snow?'#98d9ec':'#72877d';ctx.lineWidth=2;
  ctx.beginPath();ctx.ellipse(5+burst*16,0,8+burst*18,(16+burst*35)*power,0,-1.25,1.25);ctx.stroke();
  for(let i=0;i<(snow?18:9);i++) {
    const a=(i*.61803398875%1)*Math.PI*2,r=(10+burst*(35+i%5*9))*power;
    const x=Math.cos(a)*r,y=Math.sin(a)*r*.7+age*age*.00015;
    const size=(snow?2.5:1.5)+i%3;
    ctx.fillStyle=snow?(i%3?'#e8faff':'#7ebfd4'):'#657b70';
    ctx.beginPath();ctx.moveTo(x,y-size);ctx.lineTo(x+size*.55,y);ctx.lineTo(x,y+size);ctx.lineTo(x-size*.55,y);ctx.closePath();ctx.fill();
  }
  ctx.restore();
}
