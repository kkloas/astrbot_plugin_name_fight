import { useEffect, useRef, useState } from 'react';
import { ApiError } from '../api';
import { BattleView } from '../battle/BattleView';
import { useBattlePlayback, type ReplayBattle, type ReplayFighter, type BossPresentation } from '../battle/replay';
import './boss.css';

type Fighter = ReplayFighter & { slotIndex?: number; starRating?: number };
type Phase = { boss_key?: string; name: string; label: string; description: string;
  stats: { hp: number; atk: number; def: number; spd: number; crt: number; eva: number };
  martial_art: { name: string; boss_summary?: string }; neigong: { name: string; boss_summary?: string }; qinggong: { name: string; boss_summary?: string } };
type RewardPreview = { points: number; items: { name: string; quantity: number }[] };
const rewardText = (reward: RewardPreview) => `${reward.points} 积分${reward.items.map(item => ` / ${item.name} ×${item.quantity}`).join('')}`;
type BossState = {
  rewardPreview?: { participation: RewardPreview; killed: RewardPreview[]; closed: RewardPreview[] }; activity: null | { boss_id: number; boss_name: string; status: string; phase1_payload: Phase; phase2_payload: Phase;
  phase2_current_hp: number; phase2_max_hp: number }; remainingAttempts: number | null; dailyLimit: number; teamSlots: number[];
  assets: Record<string, { portrait: string; label: string }>;
  rank: { user_id: string; display_name: string; total_damage: number }[] };
type BossResult = { requestId: string; bossId: number; boss_name: string; practice: boolean; phase1_cleared: boolean; entered_phase2: boolean;
  phase2_damage: number; creditedDamage: number; phase2_current_hp: number; phase2_max_hp: number; total_damage: number;
  remaining_attempts: number; daily_limit: number; is_killed: boolean; survivors: number;
  duels: (ReplayBattle & { index: number; phase: number; boss: BossPresentation })[];
  settlement?: { rewards: { points: number; items: { item_name: string; quantity: number }[] }[] } };
type Challenge = { requestId: string; bossId: number; slots: number[]; practice: boolean; phase: 'full' | 'phase1' | 'phase2' };

export function BossView({ initialBoss, fighters, request, identityKey, onRefreshGame, onNotice }: {
  initialBoss: BossState; fighters: Fighter[]; request: <T>(path: string, init?: RequestInit) => Promise<T>;
  identityKey: string; onRefreshGame: () => Promise<void>; onNotice: (message: string) => void;
}) {
  const [boss, setBoss] = useState(initialBoss);
  const [phase, setPhase] = useState<1 | 2>(1);
  const [slots, setSlots] = useState(initialBoss.teamSlots || [1, 2, 3]);
  const [practicePhase, setPracticePhase] = useState<Challenge['phase']>('full');
  const [result, setResult] = useState<BossResult | null>(null);
  const [duelIndex, setDuelIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [autoAdvance, setAutoAdvance] = useState(true);
  const storageKey = `nfight-boss-pending:${identityKey}`;
  const [pending, setPending] = useState<Challenge | null>(() => {
    try { return JSON.parse(sessionStorage.getItem(storageKey) || 'null'); } catch { return null; }
  });
  const inFlight = useRef(false);
  const replayGeneration = useRef(0);
  const duel = result?.duels[duelIndex] || null;
  const playback = useBattlePlayback(duel);
  const activity = boss.activity;

  useEffect(() => { setBoss(initialBoss); }, [initialBoss]);
  useEffect(() => {
    let active = true;
    const generation = replayGeneration.current;
    request<BossResult | null>('/api/world-boss/replay').then(value => {
      if (active && value && replayGeneration.current === generation) { setResult(value); setDuelIndex(0); }
    }).catch(err => { if (active) setError(String(err.message || err)); });
    const poll = () => {
      if (document.hidden) return;
      request<BossState>('/api/world-boss').then(value => { if (active) setBoss(value); }).catch(() => {});
    };
    const timer = window.setInterval(poll, 15000);
    return () => { active = false; window.clearInterval(timer); };
  }, [identityKey]);
  useEffect(() => {
    if (!autoAdvance || !result || !duel || playback.time < playback.duration || duelIndex + 1 >= result.duels.length) return;
    const timer = window.setTimeout(() => setDuelIndex(index => index + 1), 1200);
    return () => window.clearTimeout(timer);
  }, [autoAdvance, result, duel, duelIndex, playback.time, playback.duration]);

  function remember(value: Challenge | null) {
    setPending(value);
    try { if (value) sessionStorage.setItem(storageKey, JSON.stringify(value)); else sessionStorage.removeItem(storageKey); } catch { /* In-memory retries still retain the request ID. */ }
  }
  async function challenge(practice: boolean, retry?: Challenge) {
    if (inFlight.current || (!activity && !retry)) return;
    const payload = retry || { requestId: crypto.randomUUID(), bossId: activity!.boss_id, slots, practice, phase: practice ? practicePhase : 'full' as const };
    replayGeneration.current += 1;
    remember(payload); inFlight.current = true; setBusy(true); setError('');
    try {
      const value = await request<BossResult>('/api/world-boss/challenge', { method: 'POST', body: JSON.stringify(payload) });
      setResult(value); setDuelIndex(0); remember(null);
      onNotice(value.practice ? '演练完成, 未扣次数和贡献' : `挑战完成, 贡献 +${value.creditedDamage}`);
      request<BossState>('/api/world-boss').then(setBoss).catch(() => {});
      onRefreshGame().catch(() => {});
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      if (err instanceof ApiError && err.status >= 400 && err.status < 500) remember(null);
    } finally { inFlight.current = false; setBusy(false); }
  }
  const validTeam = new Set(slots).size === 3 && slots.every(slot => fighters.some(f => f.slotIndex === slot));
  const panel = activity?.[phase === 1 ? 'phase1_payload' : 'phase2_payload'];
  const asset = boss.assets?.[panel?.boss_key || `dragon_chief_phase${phase}`];
  const active = activity?.status === 'active';
  const hp = activity ? Math.max(0, Math.min(100, activity.phase2_current_hp / activity.phase2_max_hp * 100)) : 0;
  return <div className="world-boss-view">
    <header className="boss-heading"><div><span className="boss-eyebrow">群侠共讨 · 世界首领</span><h2>{activity?.boss_name || '山门未启'}</h2></div>
      <span className={`boss-status ${active ? 'active' : ''}`}>{active ? '正在讨伐' : activity ? '本期已结束' : '等待开启'}</span></header>
    {activity && panel ? <>
      <div className="boss-phase-tabs" role="tablist" aria-label="BOSS 阶段">
        <button role="tab" aria-selected={phase === 1} onClick={() => setPhase(1)}>壹 · 破阵前锋</button>
        <button role="tab" aria-selected={phase === 2} onClick={() => setPhase(2)}>贰 · 龙首真身</button>
      </div>
      <section className={`boss-dossier phase-${phase}`} aria-label="BOSS 情报">
        <div className="boss-portrait">{asset && <img src={asset.portrait} alt={panel.name} decoding="async" />}<span>{phase === 1 ? '先破其阵' : '群侠合击'}</span></div>
        <div className="boss-details"><span className="boss-eyebrow">{panel.label}</span><h3>{panel.name}</h3><p>{panel.description}</p>
          <dl className="boss-stat-grid">{([['气血', panel.stats.hp], ['攻击', panel.stats.atk], ['防御', panel.stats.def], ['速度', panel.stats.spd], ['暴击', `${panel.stats.crt}%`], ['闪避', `${panel.stats.eva}%`]] as const).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
          <div className="boss-techniques">{([['武学', panel.martial_art], ['内功', panel.neigong], ['轻功', panel.qinggong]] as const).map(([label, entry]) => <div key={label}><span>{label}</span><strong>{entry.name}</strong>{entry.boss_summary && <small>{entry.boss_summary}</small>}</div>)}</div>
        </div>
      </section>
      <section className="boss-shared-health"><div><strong>全群共享血量</strong><span>{activity.phase2_current_hp.toLocaleString()} / {activity.phase2_max_hp.toLocaleString()}</span></div>
        <div className="boss-health-track" role="progressbar" aria-label="全群 BOSS 血量" aria-valuenow={activity.phase2_current_hp} aria-valuemax={activity.phase2_max_hp} aria-valuemin={0}><i style={{ width: `${hp}%` }} /></div>
        <small>每次挑战先破前锋, 仅真身阶段伤害计入共享血量和贡献。共享血量每 15 秒刷新。</small>
      </section>
      <section className="boss-team-panel"><div className="boss-section-title"><h3>出战阵容</h3><span>今日剩余 {boss.remainingAttempts ?? 0} / {boss.dailyLimit} 次</span></div>
        <p>沿用 Bot 三人阵容, 可为本次挑战调整顺序。存活队员携剩余气血进入下一阶段。</p>
        <div className="boss-team-slots">{slots.map((slot, index) => <label key={index}><span>第 {index + 1} 阵</span><select aria-label={`第 ${index + 1} 阵角色`} value={slot} disabled={busy || Boolean(pending)} onChange={event => setSlots(values => values.map((value, i) => i === index ? Number(event.target.value) : value))}>
          {!fighters.some(f => f.slotIndex === slot) && <option value={slot}>请选择角色</option>}
          {fighters.map(fighter => <option key={fighter.name} value={fighter.slotIndex}>{fighter.name} · {fighter.martialArt.name}</option>)}
        </select></label>)}</div>
        {!validTeam && <p className="boss-error">需要三个不同的已有角色。可先在角色页面创建或调整阵容。</p>}
        <div className="boss-actions"><button className="boss-challenge" disabled={busy || Boolean(pending) || !validTeam || !active || (boss.remainingAttempts ?? 0) <= 0} onClick={() => challenge(false)}>{busy ? '正在交锋...' : '挑战世界 BOSS'}</button>
          <select aria-label="演练阶段" value={practicePhase} disabled={busy || Boolean(pending)} onChange={event => setPracticePhase(event.target.value as Challenge['phase'])}><option value="full">完整双阶段</option><option value="phase1">只练一阶段</option><option value="phase2">只练满血真身</option></select>
          <button disabled={busy || Boolean(pending) || !validTeam} onClick={() => challenge(true)}>免费演练</button></div>
        <small>演练不扣次数、不改变共享血量和贡献。重播也不会重复结算。</small>
      </section>
    </> : <p className="boss-empty">管理员开启世界 BOSS 后, 这里会显示两阶段情报、挑战入口和贡献榜。</p>}
    {error && <p role="alert" className="boss-error">{error}</p>}
    {pending && !busy && <div className="boss-retry"><p>上次挑战的返回结果尚未确认。恢复同一次挑战不会重复扣次。</p><button onClick={() => challenge(pending.practice, pending)}>恢复上次挑战</button></div>}
    {result && <section className="boss-replay"><div className="boss-section-title"><h3>{result.practice ? '演练回放' : '最近挑战回放'}</h3><span>{result.boss_name}</span></div>
      <p className="boss-replay-note">回放血量保留本次交锋快照, 不随全群最新血量跳动。</p>
      {duel && <><div className="boss-bout-heading"><strong>{duel.boss.label} · 第 {duelIndex + 1} / {result.duels.length} 阵</strong><span>{duel.attacker.name} vs {duel.defender.name}</span></div>
        <BattleView battle={duel} playback={playback} startBattle={async () => playback.replay()} showResult={false} />
        <div className="boss-bout-controls"><button disabled={duelIndex === 0} onClick={() => setDuelIndex(index => index - 1)}>上一阵</button><button disabled={duelIndex + 1 >= result.duels.length} onClick={() => setDuelIndex(index => index + 1)}>下一阵</button><label><input type="checkbox" checked={autoAdvance} onChange={event => setAutoAdvance(event.target.checked)} /> 自动接战</label></div></>}
      <div className="boss-result" aria-live="polite"><strong>{result.practice ? '演练结果' : result.is_killed ? '真身已破, 讨伐完成' : result.entered_phase2 ? '本次讨伐结束' : '止步前锋'}</strong>
        <span>二阶段伤害 {result.phase2_damage.toLocaleString()}</span>{!result.practice && <><span>本次入账 +{result.creditedDamage.toLocaleString()}</span><span>你的累计贡献 {result.total_damage.toLocaleString()}</span></>}
        <span>存活 {result.survivors} 人</span>
        {result.settlement?.rewards.map((reward, i) => <p key={i}>获得 {reward.points} 积分{reward.items.map(item => ` / ${item.item_name} ×${item.quantity}`).join('')}</p>)}
      </div>
    </section>}
    <div className="boss-bottom-grid"><section className="boss-ranking"><h3>本期贡献榜</h3>{boss.rank.length ? <ol>{boss.rank.map((entry, index) => <li key={entry.user_id}><b>{String(index + 1).padStart(2, '0')}</b><span>{entry.display_name}</span><strong>{entry.total_damage.toLocaleString()}</strong></li>)}</ol> : <p>静候群侠出手。</p>}</section>
      <section className="boss-rules"><h3>讨伐须知</h3><p>正式挑战每天最多 {boss.dailyLimit} 次。前锋每次重新迎战, 真身血量由全群共享。</p><p>击杀后, 所有有贡献的成员获得参与奖励, 前十名另有排行奖励。未击杀关闭时按贡献排行结算。</p><p>Bot 命令: /bossfight 动画挑战, /bossquick 快速战报, /bosssim 免费演练。</p>{boss.rewardPreview && <details className="boss-rewards"><summary>本期奖励明细</summary><p>击杀参与奖励: {rewardText(boss.rewardPreview.participation)}</p><table><thead><tr><th>名次</th><th>击杀额外奖励</th><th>未击杀结算</th></tr></thead><tbody>{boss.rewardPreview.killed.map((reward, i) => <tr key={i}><th>{i + 1}</th><td>{rewardText(reward)}</td><td>{rewardText(boss.rewardPreview!.closed[i])}</td></tr>)}</tbody></table></details>}</section></div>
  </div>;
}
