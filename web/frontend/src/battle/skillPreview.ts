import type { BattleEvent, Side } from './replay';

export type Skill = {
  id: string; name: string;
  passives?: { type: string; max_stacks?: number }[];
  special_effect_data?: { type: string; max_stacks?: number } | { type: string; max_stacks?: number }[] | null;
};
type Effect = { type: string; max_stacks?: number };

function effectFor(skill: Skill | undefined, category: 'neigong' | 'qinggong'): Effect | undefined {
  if (category === 'neigong') return skill?.passives?.[0];
  const effect = skill?.special_effect_data;
  return Array.isArray(effect) ? effect[0] : effect || undefined;
}

export function skillStages(skill: Skill | undefined, category: 'neigong' | 'qinggong'): { value: string; label: string }[] {
  if (!skill) return [];
  const effect = effectFor(skill, category);
  if (!effect) return [{ value: 'full', label: category === 'qinggong' ? '移动轨迹' : '护体效果' }];
  if (effect.type === 'stacking_defense' || effect.type === 'action_spd_stack') {
    const count = Math.max(1, effect.max_stacks || 1);
    return [{ value: 'full', label: '完整叠层过程' }, ...Array.from({ length: count }, (_, i) => ({ value: String(i + 1), label: `第 ${i + 1} 层` }))];
  }
  if (effect.type === 'damage_defer')
    return [{ value: 'full', label: '触发, 持续与发作' }, { value: 'trigger', label: '触发' }, { value: 'sustain', label: '持续状态' }, { value: 'release', label: '延迟伤害发作' }];
  if (effect.type === 'crisis_defense')
    return [{ value: 'full', label: '触发及持续状态' }, { value: 'trigger', label: '触发' }, { value: 'sustain', label: '持续状态' }];
  return [{ value: 'full', label: '完整过程' }, { value: 'trigger', label: '触发' }];
}

export function previewCount(skill: Skill | undefined, category: 'neigong' | 'qinggong', stage: string): number {
  const effect = effectFor(skill, category);
  return stage === 'full' && (effect?.type === 'stacking_defense' || effect?.type === 'action_spd_stack') ? Math.max(1, effect.max_stacks || 1) : 1;
}

export function previewSkillEvents(skill: Skill | undefined, category: 'neigong' | 'qinggong', stage: string, side: Side, rounds: number): BattleEvent[] {
  if (!skill) return [];
  const effect = effectFor(skill, category), type = effect?.type;
  if (!effect && category === 'qinggong') return [];
  const target: Side = side === 'a' ? 'b' : 'a';
  const sourceSkill = { category, id: skill.id, name: skill.name };
  const events: BattleEvent[] = [];
  const selected = Number(stage);
  const stacks = type === 'stacking_defense' || type === 'action_spd_stack';
  if (type === 'action_spd_stack' && selected > 1)
    for (let i = 1; i < selected; i++) events.push({ type: 'passive_trigger', time: -3000 + i, actor: side, target: side, effect: type, sourceSkill });
  for (let i = 0; i < rounds; i++) {
    if (!stacks && i > 0) continue;
    if (stacks && stage !== 'full' && i > 0) continue;
    const layer = stacks ? (selected || Math.min(i + 1, effect?.max_stacks || 1)) : 1;
    if (stacks && stage === 'full' && i >= (effect?.max_stacks || 1)) continue;
    const time = i * 2500 + 600;
    const base = { time, action: i + 1, actor: side, target: side, sourceSkill };
    if (category === 'qinggong') {
      if (!type) continue;
      events.push({ ...base, type: 'passive_trigger', effect: type, status: type === 'dodge_damage_boost' ? 'next_attack_bonus' : type === 'action_spd_stack' ? 'action_spd_stack' : undefined, stacks: layer });
    } else if (type === 'stacking_defense') {
      events.push({ ...base, type: 'status_apply', status: type, stacks: layer, duration: 9999 });
    } else if (type === 'crisis_defense' || type === 'damage_defer') {
      events.push({ ...base, time: stage === 'sustain' || stage === 'release' ? -2000 : time, type: 'status_apply', status: type === 'damage_defer' ? 'deferred_damage' : type, effect: type, duration: 9999 });
      if (type === 'damage_defer' && (stage === 'full' || stage === 'release'))
        events.push({ ...base, time: time + 1200, type: 'damage', cause: 'deferred_damage', amount: 60, hpAfter: 840, maxHp: 1000 });
    } else if (type === 'thorns' || type === 'part_counter') {
      events.push({ ...base, actor: side, target, fromSide: side, type: 'damage', cause: type, amount: 40, hpAfter: 960, maxHp: 1000 });
    } else if (type === 'regeneration' || type === 'vampirism' || type === 'burst_heal' || type === 'fatal_block') {
      events.push({ ...base, type: 'heal', cause: type, amount: 50, hpAfter: 900, maxHp: 1000 });
    } else {
      events.push({ ...base, type: 'guard', multiplier: .8 });
    }
  }
  return events;
}
