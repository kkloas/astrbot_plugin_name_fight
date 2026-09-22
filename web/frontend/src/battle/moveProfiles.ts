import type { BattleEvent } from './replay';

export type MoveStyle = 'thrust'|'cross'|'rise'|'cleave'|'sweep'|'spin'|'flurry'|'leap'|'draw'|'palm'|'shock'|'kick'|'hook'|'coil'|'fan'|'needle'|'rain'|'pluck'|'strum'|'crescendo';
export type MoveTheme = 'snow'|'petal'|'cloud'|'gold'|'leaf'|'wind'|'ink'|'vermilion'|'jade'|'silver'|'mist'|'sound';
export type MoveProfile = {style:MoveStyle;theme:MoveTheme;variation:number;anticipation:number;amplitude:number};
const p=(style:MoveStyle,theme:MoveTheme,variation=0,anticipation=680,amplitude=1):MoveProfile=>({style,theme,variation,anticipation,amplitude});

// Explicit art + move identity, including names shared by different schools.
// Variation selects an authored trajectory variant, never a combat RNG result.
export const moveProfiles:Record<string,Record<string,MoveProfile>>={
  // Rendering metadata; newMartialMotion owns the full sixteen named timelines.
  sword_danyu:{
    '羽起青萍':p('rise','vermilion',0,700,.9),'穿林一线':p('thrust','vermilion',0,770),
    '回翎拂袖':p('spin','vermilion',0,650,.95),'掠水惊鸿':p('rise','vermilion',1,700),
    '双燕分波':p('flurry','vermilion',1,620),'凌空折羽':p('leap','vermilion',0,660,1.1),
    '千翎竞发':p('flurry','vermilion',2,580,1.3),'丹凤归云':p('leap','vermilion',0,620,1.45),
  },
  blade_jingchao:{
    '横江断流':p('sweep','ink',0,700),'拨浪开礁':p('cleave','ink',0,760,.9),
    '逆潮扬锋':p('rise','silver',1,710),'卷沙回刃':p('spin','ink',1,650,.95),
    '踏浪连环':p('flurry','silver',1,600,1.1),'悬瀑落刃':p('leap','ink',1,700,1.2),
    '千涛叠岸':p('flurry','ink',0,650,1.4),'一线分海':p('cleave','silver',2,800,1.5),
  },
  palm_crushing_wave:{'裂潮击':p('palm','jade',0,720),'断岳震':p('shock','ink',1,780,1.25)},
  sword_falling_plum:{'寒枝点雪':p('thrust','snow'),'回风斩':p('spin','petal',0,650)},
  leg_shadow_whirl:{'扫叶势':p('sweep','leaf',0,710),'穿云踢':p('kick','wind',1,680,1.15)},
  sword_huashan:{
    '白云出岫':p('thrust','cloud',0,700,.9),'有凤来仪':p('leap','gold',0,620,1.1),
    '天绅倒悬':p('rise','silver',1,730,1.15),'白虹贯日':p('thrust','gold',2,790,1.25),
    '苍松迎客':p('cross','jade',0,720),'金雁横空':p('leap','gold',1,660,1.2),
    '无边落木':p('flurry','leaf',0,580,1.2),'青山隐隐':p('draw','mist',0,810),
  },
  short_panguanbi:{
    '铁画银钩':p('hook','silver',0,700,.85),'朱笔勾魂':p('thrust','vermilion',0,750,.85),
    '画地为牢':p('spin','ink',1,630,.9),'笔走龙蛇':p('flurry','vermilion',1,570,.9),
    '生死立判':p('thrust','ink',2,820),'阎罗点卯':p('thrust','vermilion',1,720,.75),
    '铁案如山':p('cleave','ink',0,770),'一笔勾销':p('hook','vermilion',1,810,1.2),
  },
  blade_chengyun:{
    '拨云见日':p('rise','gold',0,700,1.2),'云出无心':p('spin','cloud',0,660,1.1),
    '平步青云':p('leap','cloud',0,620,1.2),'行云流水':p('flurry','jade',1,580,1.15),
    '云遮雾绕':p('coil','mist',0,640),'破云见空':p('cleave','cloud',1,810,1.35),
    '风起云涌':p('sweep','cloud',1,720,1.3),'乘云裂天':p('cleave','silver',2,840,1.5),
  },
  staff_yuejiaqiang:{
    '毒蛇吐信':p('thrust','jade',0,770),'拨草寻蛇':p('sweep','leaf',0,700,1.1),
    '泰山压顶':p('cleave','ink',1,790,1.25),'铁牛耕地':p('thrust','ink',1,740,1.2),
    '乌龙绞柱':p('spin','jade',1,610,1.2),'蛟龙出水':p('thrust','jade',2,800,1.3),
    '漫天梨花':p('flurry','petal',2,570,1.15),'绝招·回马枪':p('draw','silver',2,800,1.3),
  },
  sword_ittoryu:{
    '切落':p('cleave','silver',0,740,1.1),'袈裟斩':p('cross','silver',0,730),
    '逆袈裟':p('rise','silver',1,690),'刺突':p('thrust','silver',0,770),
    '胴拂':p('sweep','wind',1,710),'小手击':p('hook','silver',2,740,.8),
    '燕飞':p('leap','wind',1,650),'绝技·一之太刀':p('draw','silver',2,850,1.5),
  },
  sword_xiaoyaowuxiang:{
    '北冥鲲吸':p('coil','jade',1,660),'凌波微步':p('spin','mist',2,670),
    '天山六阳':p('thrust','gold',2,730,1.2),'无相幻境':p('flurry','mist',2,590,1.1),
    '白虹贯日':p('thrust','silver',1,800,1.1),'沧海一粟':p('thrust','jade',0,830,.8),
    '生死符剑':p('hook','mist',1,800),'绝技·逍遥游':p('leap','mist',2,630,1.4),
  },
  hidden_baoyulihua:{
    '散花':p('fan','silver',0,600),'追影':p('needle','wind',1,650,.8),
    '透骨':p('needle','silver',0,780),'见血':p('needle','vermilion',2,720),
    '夺目':p('needle','silver',2,750,.8),'蚀骨':p('needle','jade',1,740),
    '漫天花雨':p('rain','petal',0,540,1.2),'绝技·暴雨梨花':p('rain','silver',2,580,1.5),
  },
  zither_duanzhi:{
    '拨弦':p('pluck','sound',0,720,.8),'裂帛':p('strum','silver',0,740),
    '魔音入脑':p('pluck','mist',1,660),'乱心':p('strum','sound',1,620),
    '摄魂':p('pluck','jade',2,800),'断肠':p('strum','vermilion',2,760,1.1),
    '十面埋伏':p('crescendo','sound',1,560,1.25),'绝技·广陵绝响':p('crescendo','silver',2,830,1.5),
  },
};

export const themeColors:Record<MoveTheme,string>={snow:'#90cfe5',petal:'#aaa9bb',cloud:'#91a8ac',gold:'#b29a52',leaf:'#73835a',wind:'#90afb0',ink:'#344840',vermilion:'#a64c44',jade:'#568b85',silver:'#94b5c7',mist:'#819ba9',sound:'#66a9b6'};
export function profileFor(event?:BattleEvent) {
  return moveProfiles[event?.martialArtId || '']?.[event?.move || ''];
}
