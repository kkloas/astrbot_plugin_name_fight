import { unit, type impactFor } from './choreography';
import { themeColors, type MoveProfile } from './moveProfiles';

type Point=[number,number];
type Impact=ReturnType<typeof impactFor>;
const noise=(n:number)=>{const x=Math.sin(n*127.1)*43758.5453;return x-Math.floor(x);};

// All particles are sampled from absolute time. Seeking never reseeds an effect.
export function drawMoveTheme(ctx:CanvasRenderingContext2D,p:MoveProfile,tip:Point,target:Point,dir:number,age:number,impact:Impact) {
  if(age < -300 || age > 570) return;
  const life=unit((age+300)/870),fade=unit((age+300)/100)*(1-unit((age-170)/400));
  const strength=(.75+impact.force*.7)*p.amplitude;
  const color=themeColors[p.theme];
  ctx.save();ctx.globalAlpha=fade*.8;ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineCap='round';
  const curve=(x:number,y:number,w:number,h:number,width:number)=>{
    ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x-dir*w,y+h);
    ctx.quadraticCurveTo(x+dir*w*.55,y-h,x+dir*w,y);ctx.stroke();
  };
  const particleCount=Math.round((p.style==='rain'?38:18)*strength);
  if(p.theme==='petal'||p.theme==='leaf'||p.theme==='snow') {
    for(let i=0;i<particleCount;i++) {
      const n=noise(i+17*p.variation),progress=(life+n*.6)%1;
      const x=tip[0]+dir*((progress-.5)*175+Math.sin(i*2.1+life*7)*22);
      const y=tip[1]+(noise(i+72)-.5)*92+progress*50;
      ctx.save();ctx.translate(x,y);ctx.rotate(i+life*5);ctx.globalAlpha=fade*(.3+.6*n);
      if(p.theme==='snow') {
        ctx.lineWidth=1;for(let j=0;j<3;j++) {ctx.rotate(Math.PI/3);ctx.beginPath();ctx.moveTo(-3,0);ctx.lineTo(3,0);ctx.stroke();}
      } else {
        ctx.beginPath();ctx.moveTo(-5,0);ctx.quadraticCurveTo(0,-5,7,0);ctx.quadraticCurveTo(1,p.theme==='leaf'?2:6,-5,0);ctx.fill();
      }
      ctx.restore();
    }
  }
  if(p.theme==='cloud'||p.theme==='mist'||p.theme==='wind') {
    for(let i=0;i<6;i++) {
      const x=tip[0]-dir*(20+i*17+life*30),y=tip[1]+Math.sin(life*6+i)*24;
      ctx.globalAlpha=fade*(.16-i*.018);curve(x,y,48+life*32,13+i*3,8-i);
      ctx.globalAlpha=fade*.32;curve(x,y,48+life*32,13+i*3,1);
    }
  }
  if(p.theme==='jade'||p.style==='coil') {
    // Inward curls suggest drawing breath, not a life-steal tether.
    for(let i=0;i<4;i++) {
      const radius=(p.style==='coil'?1-life*.55:.5+life*.5)*(28+i*13);
      const x=tip[0]-dir*i*13;
      ctx.lineWidth=2;ctx.globalAlpha=fade*(.6-i*.1);ctx.beginPath();
      ctx.ellipse(x,tip[1],radius*.6,radius,dir*life,life*5+i,life*5+i+Math.PI*1.3);ctx.stroke();
    }
  }
  if(p.theme==='ink'||p.theme==='vermilion'||p.style==='hook') {
    ctx.globalAlpha=fade*.7;
    curve(tip[0],tip[1],30+25*p.amplitude,22+p.variation*6,4);
    ctx.fillStyle=p.style==='hook'?'#9f433c':color;
    for(let i=0;i<12;i++) {
      ctx.beginPath();ctx.ellipse(tip[0]+dir*(noise(i+9)-.7)*95,tip[1]+(noise(i+38)-.5)*60,1+noise(i)*3,1+noise(i+4)*2,i,0,Math.PI*2);ctx.fill();
    }
  }
  if(p.theme==='gold'||p.theme==='silver') {
    ctx.globalAlpha=fade*.65;
    const length=(p.style==='draw'?145:95)*strength;
    ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(tip[0]-dir*length,tip[1]+3);ctx.lineTo(tip[0]+dir*22,tip[1]);ctx.stroke();
    ctx.strokeStyle='#f7f8ef';ctx.lineWidth=1.6;ctx.stroke();ctx.strokeStyle=color;
    for(let i=0;i<10;i++) {const x=tip[0]-dir*noise(i+4)*length,y=tip[1]+(noise(i+33)-.5)*50;curve(x,y,5+life*9,2,1);}
  }
  if(p.theme==='sound') {
    const phase=unit((age+280)/380),count=p.style==='crescendo'?6:3;
    for(let i=0;i<count;i++) {
      const progress=unit(phase-i*.095),x=tip[0]+(target[0]-tip[0])*progress;
      const radius=(25+i*5)*strength;
      ctx.globalAlpha=fade*(1-i/(count+1))*.75;ctx.lineWidth=i===0?4:1.5;
      ctx.beginPath();ctx.moveTo(x-dir*10,tip[1]-radius);
      ctx.quadraticCurveTo(x+dir*radius*.95,tip[1],x-dir*10,tip[1]+radius);ctx.stroke();
    }
  }
  if((p.style==='palm'||p.style==='shock') && age>-100) {
    ctx.globalAlpha=fade*.6;
    for(let i=0;i<3;i++) {const radius=(25+life*65+i*12)*strength;ctx.lineWidth=3-i*.7;ctx.beginPath();ctx.ellipse(tip[0]+dir*20,tip[1],radius*.35,radius,0,-1.3,1.3);ctx.stroke();}
  }
  // Decorative motion can play on misses. A contact burst requires actual damage.
  if(impact.hit && age>=0 && age<310) {
    const progress=age/310;ctx.globalAlpha=(1-progress)*.75;ctx.strokeStyle=color;
    for(let i=0;i<Math.round(10+impact.force*14);i++) {
      const angle=i*2.399,reach=(18+noise(i+11)*36)*strength*progress;
      ctx.lineWidth=1+noise(i)*2;ctx.beginPath();ctx.moveTo(target[0]+Math.cos(angle)*reach*.4,target[1]+Math.sin(angle)*reach*.4);
      ctx.lineTo(target[0]+Math.cos(angle)*reach,target[1]+Math.sin(angle)*reach);ctx.stroke();
    }
  }
  ctx.restore();
}
