import { useEffect, useMemo, useState } from 'react';
import { BattleView } from '../battle/BattleView';
import { stateAt, useBattlePlayback, type BattleEvent, type ReplayBattle, type ReplayFighter } from '../battle/replay';
import './pve.css';

type Fighter = Omit<ReplayFighter, 'stats'> & {
  stats: { hp: number; atk: number; def: number; spd?: number; crt?: number; eva?: number };
  slotIndex?: number;
  starRating?: number;
};

type PveProfile = {
  energy: number;
  maximum_energy: number;
  recovery_seconds: number;
  energy_updated_at: number;
  next_recovery_at: number | null;
  server_time: number;
  team_slots: number[];
};

type RewardItem = { item_id: string; name?: string; quantity: number };
type Reward = { points: number; wallet_points?: number; items: RewardItem[] };

type Stage = {
  id: string;
  chapterId: string;
  name: string;
  kind: 'normal' | 'elite' | 'boss';
  recommendedStars: number;
  energyCost: number;
  trait: { id: string; name: string; description: string };
  firstClear: { points: number; items: RewardItem[] };
  enemies: Fighter[];
  unlocked: boolean;
  bestStars: number;
  clearCount: number;
};

type Chest = {
  stars: number;
  points: number;
  items: RewardItem[];
  claimed: boolean;
  available: boolean;
};

type Chapter = {
  id: string;
  name: string;
  description: string;
  stars: number;
  stages: Stage[];
  chests: Chest[];
};

export type PveState = {
  profile: PveProfile;
  team: Fighter[];
  chapters: Chapter[];
  nextStageId: string;
  hasRequiredRoster: boolean;
};

type Duel = ReplayBattle & {
  index: number;
  transition: string;
  traitDelta: number;
  displayLogs: string[];
  playerTeam: Fighter[];
  enemyTeam: Fighter[];
};

type ChallengeResult = {
  stage: Stage;
  victory: boolean;
  stars: number;
  firstClear: boolean;
  bestStars: number;
  reward: Reward;
  profile: PveProfile;
  duels: Duel[];
  playerTeam: Fighter[];
  enemyTeam: Fighter[];
  pve: PveState;
};

const kindLabels = { normal: '普通', elite: '精英', boss: '首领' };

function rewardText(reward: { points?: number; items?: RewardItem[] }) {
  const parts: string[] = [];
  if (reward.points) parts.push(`${reward.points} 积分`);
  for (const item of reward.items || []) parts.push(`${item.name || item.item_id} x${item.quantity}`);
  return parts.length ? parts.join(' / ') : '无额外奖励';
}

function starText(value: number) {
  return `${'★'.repeat(Math.max(0, value))}${'☆'.repeat(Math.max(0, 3 - value))}`;
}

export function PveView({
  fighters,
  request,
  onRefreshGame,
  onNotice,
  openFighters,
}: {
  fighters: Fighter[];
  request: (path: string, init?: RequestInit) => Promise<any>;
  onRefreshGame: () => Promise<void>;
  onNotice: (message: string) => void;
  openFighters: () => void;
}) {
  const [pve, setPve] = useState<PveState | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState('');
  const [selectedStageId, setSelectedStageId] = useState('');
  const [teamSlots, setTeamSlots] = useState<number[]>([]);
  const [challenge, setChallenge] = useState<ChallengeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadedAt, setLoadedAt] = useState(Date.now());
  const [, setClock] = useState(0);

  async function load() {
    const next = await request('/api/pve');
    setPve(next);
    setLoadedAt(Date.now());
    setTeamSlots(next.profile.team_slots || []);
    const nextStageId = next.nextStageId || next.chapters[0]?.stages[0]?.id || '';
    setSelectedStageId((current) => current || nextStageId);
    const containing = next.chapters.find((chapter: Chapter) => chapter.stages.some((stage) => stage.id === nextStageId));
    setSelectedChapterId((current) => current || containing?.id || next.chapters[0]?.id || '');
  }

  useEffect(() => {
    load().catch((error) => onNotice(error instanceof Error ? error.message : String(error)));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setClock((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const profile = pve?.profile;
  const estimatedEnergy = useMemo(() => {
    if (!profile) return 0;
    if (profile.energy >= profile.maximum_energy) return profile.maximum_energy;
    const estimatedServerNow = profile.server_time + Math.floor((Date.now() - loadedAt) / 1000);
    const recovered = Math.floor(Math.max(0, estimatedServerNow - profile.energy_updated_at) / profile.recovery_seconds);
    return Math.min(profile.maximum_energy, profile.energy + recovered);
  }, [profile, loadedAt, Date.now()]);

  const nextRecoverySeconds = useMemo(() => {
    if (!profile || estimatedEnergy >= profile.maximum_energy) return 0;
    const estimatedServerNow = profile.server_time + Math.floor((Date.now() - loadedAt) / 1000);
    const elapsed = Math.max(0, estimatedServerNow - profile.energy_updated_at);
    return profile.recovery_seconds - (elapsed % profile.recovery_seconds);
  }, [profile, loadedAt, estimatedEnergy, Date.now()]);

  const chapter = pve?.chapters.find((entry) => entry.id === selectedChapterId) || pve?.chapters[0];
  const selectedStage = chapter?.stages.find((entry) => entry.id === selectedStageId) || chapter?.stages[0];
  const fighterBySlot = new Map(fighters.map((fighter) => [Number(fighter.slotIndex), fighter]));

  function selectChapter(next: Chapter) {
    setSelectedChapterId(next.id);
    const firstOpen = next.stages.find((stage) => stage.unlocked && stage.clearCount === 0) || next.stages.find((stage) => stage.unlocked) || next.stages[0];
    setSelectedStageId(firstOpen.id);
    setChallenge(null);
  }

  function toggleSlot(slot: number) {
    setTeamSlots((current) => {
      if (current.includes(slot)) return current.filter((value) => value !== slot);
      if (current.length >= 3) return [...current.slice(1), slot];
      return [...current, slot];
    });
  }

  function moveSlot(index: number, offset: number) {
    setTeamSlots((current) => {
      const target = index + offset;
      if (target < 0 || target >= current.length) return current;
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  async function saveTeam() {
    if (teamSlots.length !== 3) throw new Error('请选择三名出战角色');
    const result = await request('/api/pve/team', { method: 'POST', body: JSON.stringify({ slots: teamSlots }) });
    setPve(result.state);
    setLoadedAt(Date.now());
  }

  async function beginChallenge() {
    if (!selectedStage) return;
    setBusy(true);
    try {
      if (teamSlots.length !== 3) throw new Error('请选择三名出战角色');
      if (teamSlots.join(',') !== (pve?.profile.team_slots || []).join(',')) await saveTeam();
      const result: ChallengeResult = await request(`/api/pve/stages/${encodeURIComponent(selectedStage.id)}/challenge`, { method: 'POST' });
      setChallenge(result);
      setPve(result.pve);
      setLoadedAt(Date.now());
      onNotice(result.victory ? `通关成功，获得 ${result.stars} 星` : '挑战失败，调整阵容后再试');
      await onRefreshGame();
    } catch (error) {
      onNotice(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  async function claimChest(chapterId: string, threshold: number) {
    setBusy(true);
    try {
      const result = await request(`/api/pve/chapters/${encodeURIComponent(chapterId)}/rewards/${threshold}/claim`, { method: 'POST' });
      setPve(result.pve);
      setLoadedAt(Date.now());
      onNotice(`已领取 ${threshold} 星章节宝箱`);
      await onRefreshGame();
    } catch (error) {
      onNotice(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  function openNextStage() {
    if (!challenge) return;
    const nextStageId = challenge.pve.nextStageId;
    const nextChapter = challenge.pve.chapters.find((entry) => entry.stages.some((stage) => stage.id === nextStageId));
    if (!nextChapter || nextStageId === challenge.stage.id) return;
    setPve(challenge.pve);
    setSelectedChapterId(nextChapter.id);
    setSelectedStageId(nextStageId);
    setChallenge(null);
  }

  if (!pve || !chapter || !selectedStage) return <div className="pve-loading">正在展开江湖舆图...</div>;
  if (challenge) {
    return <TeamBattleReplay result={challenge} onBack={() => setChallenge(null)} onNext={openNextStage} onRetry={beginChallenge} busy={busy} />;
  }

  return <div className="pve-view">
    <header className="pve-header">
      <div><span>江湖历练</span><h2>{chapter.name}</h2><p>{chapter.description}</p></div>
      <div className="pve-energy"><b>{estimatedEnergy}</b><span>/ {profile?.maximum_energy} 体力</span>{nextRecoverySeconds > 0 && <small>{Math.floor(nextRecoverySeconds / 60)}:{String(nextRecoverySeconds % 60).padStart(2, '0')} 后恢复 1 点</small>}</div>
    </header>

    <nav className="pve-chapters" aria-label="历练章节">
      {pve.chapters.map((entry, index) => <button key={entry.id} className={entry.id === chapter.id ? 'active' : ''} onClick={() => selectChapter(entry)}>
        <span>第 {index + 1} 章</span><strong>{entry.name}</strong><small>{entry.stars}/18 星</small>
      </button>)}
    </nav>

    <section className="pve-stage-map">
      {chapter.stages.map((stage, index) => <button key={stage.id} disabled={!stage.unlocked} className={`${stage.id === selectedStage.id ? 'selected' : ''} ${stage.kind}`} onClick={() => setSelectedStageId(stage.id)}>
        <span>{index + 1}</span><strong>{stage.name}</strong><small>{stage.unlocked ? starText(stage.bestStars) : '未解锁'}</small>
      </button>)}
    </section>

    <div className="pve-preparation">
      <section className="pve-stage-detail">
        <div className="pve-stage-title"><span>{kindLabels[selectedStage.kind]}</span><h3>{selectedStage.name}</h3><b>推荐 {selectedStage.recommendedStars} 星</b></div>
        <p className="pve-trait"><strong>{selectedStage.trait.name}</strong>{selectedStage.trait.description}</p>
        <div className="pve-enemies">
          {selectedStage.enemies.map((enemy, index) => <div key={enemy.name}>
            <span>{index + 1}</span><strong>{enemy.name}</strong><small>{enemy.martialArt.name} / {enemy.neigong?.name}</small>
            <em>气血 {enemy.stats.hp} · 攻 {enemy.stats.atk} · 防 {enemy.stats.def}</em>
          </div>)}
        </div>
        <p className="pve-reward-line">首通：{rewardText(selectedStage.firstClear)}</p>
      </section>

      <section className="pve-team-builder">
        <div className="pve-team-heading"><h3>出战阵容</h3><span>{teamSlots.length}/3</span></div>
        {!pve.hasRequiredRoster && <div className="pve-roster-warning"><p>需要先拥有三名角色才能进入历练。</p><button onClick={openFighters}>前往创建角色</button></div>}
        <div className="pve-roster">
          {fighters.map((fighter) => {
            const slot = Number(fighter.slotIndex);
            const order = teamSlots.indexOf(slot);
            return <button key={fighter.name} className={order >= 0 ? 'chosen' : ''} onClick={() => toggleSlot(slot)}>
              <span>{order >= 0 ? order + 1 : slot}</span><strong>{fighter.name}</strong><small>{fighter.starRating?.toFixed(1) || '-'} 星 · {fighter.martialArt.name}</small>
            </button>;
          })}
        </div>
        <div className="pve-order">
          {teamSlots.map((slot, index) => {
            const fighter = fighterBySlot.get(slot);
            return <div key={slot}><b>{index + 1}</b><span>{fighter?.name || `空槽位 ${slot}`}</span><button onClick={() => moveSlot(index, -1)} disabled={index === 0}>←</button><button onClick={() => moveSlot(index, 1)} disabled={index === teamSlots.length - 1}>→</button></div>;
          })}
        </div>
        <button className="pve-challenge" disabled={busy || !selectedStage.unlocked || teamSlots.length !== 3 || estimatedEnergy < selectedStage.energyCost} onClick={beginChallenge}>
          {busy ? '结算中...' : `挑战关卡 · ${selectedStage.energyCost} 体力`}
        </button>
      </section>
    </div>

    <section className="pve-chests">
      <h3>章节星级宝箱</h3>
      {chapter.chests.map((chest) => <div key={chest.stars} className={chest.available ? 'available' : ''}>
        <b>{chest.stars} 星</b><span>{rewardText(chest)}</span><button disabled={busy || chest.claimed || !chest.available} onClick={() => claimChest(chapter.id, chest.stars)}>{chest.claimed ? '已领取' : chest.available ? '领取' : '未达成'}</button>
      </div>)}
    </section>
  </div>;
}

function TeamBattleReplay({ result, onBack, onNext, onRetry, busy }: { result: ChallengeResult; onBack: () => void; onNext: () => void; onRetry: () => void; busy: boolean }) {
  const [duelIndex, setDuelIndex] = useState(0);
  const [intermission, setIntermission] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [syncedDuel, setSyncedDuel] = useState<Duel | null>(null);
  const duel = result.duels[duelIndex] || null;
  const playback = useBattlePlayback(duel);
  const replayState = duel ? stateAt(duel, playback.time) : null;

  useEffect(() => {
    setDuelIndex(0);
    setIntermission(false);
    setShowSummary(false);
  }, [result]);

  useEffect(() => {
    setIntermission(false);
    setSyncedDuel(duel);
  }, [duel]);

  useEffect(() => {
    if (!duel || syncedDuel !== duel || showSummary || playback.playing || playback.time < playback.duration) return;
    if (duelIndex >= result.duels.length - 1) {
      const timer = window.setTimeout(() => setShowSummary(true), 900);
      return () => window.clearTimeout(timer);
    }
    setIntermission(true);
    const timer = window.setTimeout(() => {
      setIntermission(false);
      setDuelIndex((value) => value + 1);
    }, 600);
    return () => window.clearTimeout(timer);
  }, [duelIndex, duel, syncedDuel, playback.playing, playback.time, playback.duration, result.duels.length, showSummary]);

  function replayAll() {
    setShowSummary(false);
    setIntermission(false);
    setDuelIndex(0);
    if (duelIndex === 0) playback.replay();
  }

  if (showSummary || !duel) return <BattleSummary result={result} onBack={onBack} onNext={onNext} onRetry={onRetry} replayAll={replayAll} busy={busy} />;

  return <div className="team-replay">
    <header className="team-replay-heading"><div><span>{result.stage.name}</span><strong>第 {duelIndex + 1}/{result.duels.length} 场</strong></div><button onClick={() => setShowSummary(true)}>跳至结算</button></header>
    <TeamRail label="我方" fighters={duel.playerTeam} activeName={duel.attacker.name} activeHp={replayState?.hp.a} />
    <BattleView battle={duel} playback={playback} startBattle={() => playback.replay()} showResult={false} />
    <TeamRail label="敌方" fighters={duel.enemyTeam} activeName={duel.defender.name} activeHp={replayState?.hp.b} />
    {intermission && <div className="team-intermission"><strong>换人</strong><span>{duel.transition || '下一场即将开始'}</span></div>}
  </div>;
}

function TeamRail({ label, fighters, activeName, activeHp }: { label: string; fighters: Fighter[]; activeName: string; activeHp?: number }) {
  return <div className="team-rail"><b>{label}</b>{fighters.map((fighter, index) => {
    const hp = fighter.name === activeName && activeHp !== undefined ? activeHp : fighter.currentHp ?? fighter.stats.hp;
    return <div key={`${index}-${fighter.name}`} className={`${fighter.name === activeName ? 'active' : ''} ${hp <= 0 ? 'fallen' : ''}`}><span>{index + 1}</span><strong>{fighter.name}</strong><i><em style={{ width: `${Math.max(0, hp / fighter.stats.hp * 100)}%` }} /></i><small>{hp}/{fighter.stats.hp}</small></div>;
  })}</div>;
}

function BattleSummary({ result, onBack, onNext, onRetry, replayAll, busy }: { result: ChallengeResult; onBack: () => void; onNext: () => void; onRetry: () => void; replayAll: () => void; busy: boolean }) {
  const hasNextStage = result.victory && result.pve.nextStageId !== result.stage.id;
  return <section className={`pve-summary ${result.victory ? 'victory' : 'defeat'}`}>
    <span className="pve-summary-mark">{result.victory ? '胜' : '败'}</span>
    <h2>{result.victory ? '历练告捷' : '暂且退守'}</h2>
    <p>{result.stage.name} · {result.victory ? starText(result.stars) : '未能通关'}</p>
    <div className="pve-summary-grid"><div><span>历史最佳</span><strong>{starText(result.bestStars)}</strong></div><div><span>获得奖励</span><strong>{result.victory ? rewardText(result.reward) : '无'}</strong></div><div><span>剩余体力</span><strong>{result.profile.energy}/{result.profile.maximum_energy}</strong></div></div>
    {result.firstClear && <p className="pve-first-clear">首次通关奖励已发放</p>}
    <div className="pve-summary-actions"><button onClick={onBack}>返回关卡</button><button onClick={replayAll}>整场重播</button>{hasNextStage && <button onClick={onNext}>下一关</button>}<button disabled={busy || result.profile.energy < result.stage.energyCost} onClick={onRetry}>{busy ? '结算中...' : '再次挑战'}</button></div>
  </section>;
}
