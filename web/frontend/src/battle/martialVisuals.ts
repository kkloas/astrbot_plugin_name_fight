import type { BattleEvent, ReplayFighter } from './replay';

export type Weapon = 'sword' | 'katana' | 'blade' | 'spear' | 'brush' | 'unarmed' | 'needles' | 'zither';
export type Motion = 'thrust' | 'slash' | 'rise' | 'cleave' | 'sweep' | 'flurry' | 'leap' | 'draw' | 'palm' | 'kick' | 'throw' | 'pluck';
export type Trail = 'edge' | 'point' | 'wave' | 'dust' | 'needles' | 'sound' | 'vortex' | 'mist';
export type Pattern = 'direct' | 'cross' | 'wheel' | 'fall' | 'fan' | 'rain' | 'spiral' | 'focus' | 'crescendo';
export type Technique = { motion: Motion; trail: Trail; weight: number; flourish?: 'plum' | 'cloud' | 'crimson' | 'phantom'; feint?: boolean; pattern?: Pattern };
const v = (motion: Motion, trail: Trail, weight = 1, flourish?: Technique['flourish']): Technique => ({ motion, trail, weight, flourish });

// Explicit per-art keys avoid confusing the two different "白虹贯日" entries.
// Visual flourishes never imply that a probabilistic status actually triggered.
export const techniques: Record<string, Record<string, Technique>> = {
  palm_crushing_wave: {
    '裂潮击': v('palm','wave'), '断岳震': v('cleave','wave',1.4),
  },
  sword_falling_plum: {
    '寒枝点雪': v('thrust','point',.8,'plum'), '回风斩': v('slash','edge',1,'plum'),
  },
  leg_shadow_whirl: {
    '扫叶势': v('sweep','dust'), '穿云踢': v('kick','wave',1.2),
  },
  sword_huashan: {
    '白云出岫': v('thrust','point',.8,'cloud'), '有凤来仪': v('leap','edge'),
    '天绅倒悬': v('rise','edge'), '白虹贯日': v('thrust','point',1.5),
    '苍松迎客': v('slash','edge',.8), '金雁横空': v('leap','edge',1.1),
    '无边落木': v('flurry','edge',1.3), '青山隐隐': v('draw','mist',1.2),
  },
  short_panguanbi: {
    '铁画银钩': v('slash','edge',.7,'crimson'), '朱笔勾魂': v('thrust','point',.7,'crimson'),
    '画地为牢': v('sweep','dust',.8), '笔走龙蛇': v('flurry','edge',.8,'crimson'),
    '生死立判': v('thrust','point',1.2), '阎罗点卯': v('thrust','point',.6),
    '铁案如山': v('cleave','edge',1.3), '一笔勾销': v('draw','edge',1.3,'crimson'),
  },
  blade_chengyun: {
    '拨云见日': v('rise','edge',1,'cloud'), '云出无心': v('slash','edge',1,'cloud'),
    '平步青云': v('leap','edge',1.3), '行云流水': v('flurry','edge',1.2),
    '云遮雾绕': v('slash','mist',1,'cloud'), '破云见空': v('cleave','edge',1.5),
    '风起云涌': v('sweep','edge',1.4,'cloud'), '乘云裂天': v('draw','edge',1.7,'cloud'),
  },
  staff_yuejiaqiang: {
    '毒蛇吐信': v('thrust','point'), '拨草寻蛇': v('sweep','dust'),
    '泰山压顶': v('cleave','edge',1.4), '铁牛耕地': v('thrust','point',1.2),
    '乌龙绞柱': v('slash','vortex'), '蛟龙出水': v('rise','point',1.4),
    '漫天梨花': v('flurry','point',1.3), '绝招·回马枪': {...v('draw','point',1.7),feint:true},
  },
  sword_ittoryu: {
    '切落': v('cleave','edge',1.3), '袈裟斩': v('slash','edge',1.2),
    '逆袈裟': v('rise','edge'), '刺突': v('thrust','point'),
    '胴拂': v('sweep','edge',1.2), '小手击': v('slash','point',.8),
    '燕飞': v('leap','edge',1.2), '绝技·一之太刀': v('draw','edge',1.8),
  },
  sword_xiaoyaowuxiang: {
    '北冥鲲吸': v('slash','vortex',1,'phantom'), '凌波微步': v('slash','mist',1,'phantom'),
    '天山六阳': v('thrust','point',1.3,'crimson'), '无相幻境': v('flurry','mist',1.3,'phantom'),
    '白虹贯日': v('thrust','point',1.4,'phantom'), '沧海一粟': v('thrust','point',.7),
    '生死符剑': v('draw','mist',1), '绝技·逍遥游': v('leap','mist',1.6,'phantom'),
  },
  hidden_baoyulihua: {
    '散花': v('throw','needles',1), '追影': v('throw','needles',.6),
    '透骨': v('throw','needles',.3), '见血': v('throw','needles',.8),
    '夺目': v('throw','needles',.4), '蚀骨': v('throw','needles',.6,'phantom'),
    '漫天花雨': v('throw','needles',1.5), '绝技·暴雨梨花': v('throw','needles',2),
  },
  zither_duanzhi: {
    '拨弦': v('pluck','sound',.7), '裂帛': v('pluck','edge'),
    '魔音入脑': v('pluck','sound',1.1,'phantom'), '乱心': v('pluck','sound',1,'cloud'),
    '摄魂': v('pluck','sound',.8,'phantom'), '断肠': v('pluck','sound',1.2,'crimson'),
    '十面埋伏': v('pluck','sound',1.6), '绝技·广陵绝响': v('pluck','edge',1.9),
  },
};

export function weaponFor(fighter: ReplayFighter): Weapon {
  if (fighter.martialArt.id === 'sword_ittoryu') return 'katana';
  const weapons: Record<string, Weapon> = {
    sword:'sword', blade:'blade', staff:'spear', short_weapon:'brush',
    palm:'unarmed', leg:'unarmed', hidden_weapon:'needles', musical_instrument:'zither',
  };
  return weapons[fighter.martialArt.type || 'sword'] || 'unarmed';
}

const patterns: Record<string, Record<string, Pattern>> = {
  sword_huashan: {'有凤来仪':'wheel','天绅倒悬':'fall','金雁横空':'cross','无边落木':'fall','青山隐隐':'focus'},
  sword_falling_plum: {'回风斩':'wheel'},
  short_panguanbi: {'铁画银钩':'cross','画地为牢':'wheel','笔走龙蛇':'spiral','阎罗点卯':'focus','一笔勾销':'cross'},
  blade_chengyun: {'云出无心':'wheel','行云流水':'cross','云遮雾绕':'spiral','风起云涌':'wheel','乘云裂天':'fall'},
  staff_yuejiaqiang: {'乌龙绞柱':'spiral','蛟龙出水':'wheel','漫天梨花':'fan'},
  sword_ittoryu: {'袈裟斩':'fall','逆袈裟':'cross','燕飞':'wheel','绝技·一之太刀':'focus'},
  sword_xiaoyaowuxiang: {'北冥鲲吸':'spiral','凌波微步':'wheel','天山六阳':'fan','无相幻境':'cross','生死符剑':'focus','绝技·逍遥游':'spiral'},
  hidden_baoyulihua: {'散花':'fan','追影':'spiral','透骨':'focus','见血':'cross','夺目':'focus','蚀骨':'spiral','漫天花雨':'rain','绝技·暴雨梨花':'rain'},
  zither_duanzhi: {'拨弦':'direct','裂帛':'cross','魔音入脑':'spiral','乱心':'wheel','摄魂':'focus','断肠':'fall','十面埋伏':'fan','绝技·广陵绝响':'crescendo'},
};

export function techniqueFor(event: BattleEvent | undefined, fighter: ReplayFighter): Technique {
  const known = techniques[event?.martialArtId || fighter.martialArt.id || '']?.[event?.move || ''];
  if (known) return {...known,pattern:patterns[event?.martialArtId || fighter.martialArt.id || '']?.[event?.move || ''] || 'direct'};
  const type = event?.weaponType || fighter.martialArt.type;
  if (type === 'palm') return v('palm','wave');
  if (type === 'leg') return v('kick','wave');
  if (type === 'hidden_weapon') return v('throw','needles');
  if (type === 'musical_instrument') return v('pluck','sound');
  return v('thrust','point');
}

export const effectLabels: Record<string, string> = {
  regeneration:'回春', vampirism:'汲血', thorns:'反震', burst_heal:'生机爆发',
  crisis_defense:'罡气护体', battle_start_first_strike:'抢占先机', low_hp_extra_action:'绝境提气',
};
