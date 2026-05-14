import { useEffect, useMemo, useState, type CSSProperties } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

type Stats = {
  hp: number;
  atk: number;
  def: number;
  spd: number;
  crt: number;
  eva: number;
};

type Entry = {
  id: string;
  name: string;
  type?: string;
  description?: string;
};

type Fighter = {
  name: string;
  slotIndex?: number;
  isActive: boolean;
  starRating: number;
  baseStarRating: number;
  starExp: number;
  breakthroughStage: number;
  wins: number;
  battles: number;
  stats: Stats;
  martialArt: Entry;
  neigong: Entry;
  qinggong: Entry;
  cardUrl?: string;
};

type Item = {
  item_id: string;
  itemId?: string;
  name: string;
  price: number;
  quantity?: number;
  category: string;
};

type LeaderboardEntry = {
  fighter_name: string;
  elo_rating: number;
  wins: number;
  battles: number;
  win_rate: number;
};

type BattleEvent = {
  type: string;
  time: number;
  actor?: 'a' | 'b';
  target?: 'a' | 'b';
  amount?: number;
  hpBefore?: number;
  hpAfter?: number;
  maxHp?: number;
  crit?: boolean;
  status?: string;
  winner?: string | null;
  message?: string;
  final?: {
    a: { hp: number; maxHp: number };
    b: { hp: number; maxHp: number };
  };
};

type BattleResult = {
  attacker: Fighter;
  defender: Fighter;
  winner: string | null;
  state: Record<string, number | string | null>;
  events: BattleEvent[];
  logs: string[];
  displayLogs: string[];
  rating: Record<string, { name: string; before: number; after: number; delta: number }>;
};

type GameState = {
  session: { userId: string; groupId: string; maxFighters: number };
  fighters: Fighter[];
  activeFighter: Fighter | null;
  wallet: { points: number; last_signin_date: string };
  items: Item[];
  shop: Item[];
  leaderboard: LeaderboardEntry[];
  worldBoss: any;
  needsFirstFighter: boolean;
};

type View = 'jianghu' | 'fighters' | 'battle' | 'shop' | 'leaderboard' | 'boss';

const itemLabels: Record<string, string> = {
  star_exp_pill_s: '小星尘丹',
  star_exp_pill_m: '中星尘丹',
  breakthrough_pill: '破境丹',
  martial_token_basic: '洗髓符',
  martial_token_type: '换宗令',
  martial_token_choice: '天机残卷',
};

const statusLabels: Record<string, string> = {
  bleeding: '流血',
  stunned: '眩晕',
  slowed: '迟缓',
  weakened: '虚弱',
  disarmed: '缴械',
  armor_broken: '破甲',
};

// 与 render_profile.get_stat_color + text_resources.stat_comment 严格对齐：
// 白(0) / 绿(1) / 蓝(2) / 紫(3) / 橙(4)
const STAT_TIER_THRESHOLDS: Record<keyof Stats, number[]> = {
  hp: [384, 427, 465, 509, 553],
  atk: [73, 87, 99, 113, 125],
  def: [60, 75, 87, 100, 112],
  spd: [46, 58, 69, 81, 93],
  crt: [15, 21, 26, 31, 35],
  eva: [20, 26, 31, 36, 41],
};

const STAT_TIER_LABELS: Record<keyof Stats, string[]> = {
  hp: ['\u6c14\u606f\u865a\u6d6e', '\u672c\u5143\u7a0d\u6b20', '\u5185\u606f\u8fde\u7ef5', '\u6839\u57fa\u6df1\u539a', '\u6c14\u8840\u5982\u8679', '\u5317\u51a5\u5316\u751f'],
  atk: ['\u529b\u9053\u672a\u6210', '\u5b88\u62d9\u6c42\u7a33', '\u84c4\u52bf\u6210\u52b2', '\u950b\u8292\u6bd5\u9732', '\u6240\u5411\u62ab\u9761', '\u648c\u5929\u52a8\u5730'],
  def: ['\u4e0d\u582a\u4e00\u51fb', '\u8f7b\u7532\u8584\u9635', '\u4e25\u9635\u4ee5\u5f85', '\u5b88\u52bf\u6c89\u96c4', '\u4e0d\u52a8\u5982\u5c71', '\u82cd\u5c71\u8d1f\u96ea'],
  spd: ['\u8eab\u5f62\u8fdf\u6ede', '\u6b65\u5c65\u6c89\u7a33', '\u8fdb\u9000\u6709\u5ea6', '\u8eab\u8f7b\u5982\u71d5', '\u8ffd\u98ce\u9010\u7535', '\u6d6e\u5149\u63a0\u5f71'],
  crt: ['\u950b\u8292\u672a\u663e', '\u7a33\u4e2d\u6c42\u80dc', '\u5076\u9732\u5ce5\u5d58', '\u5947\u950b\u6697\u85cf', '\u6740\u673a\u70bd\u76db', '\u767d\u8679\u8d2f\u65e5'],
  eva: ['\u6b65\u6cd5\u751f\u758f', '\u820d\u907f\u5c31\u6321', '\u8f6c\u570e\u81ea\u5982', '\u95ea\u8f6c\u817e\u632a', '\u98d8\u6e3a\u96be\u6d4b', '\u7fe9\u82e5\u60ca\u9e3f'],
};

function statTier(key: keyof Stats, value: number): number {
  const t = STAT_TIER_THRESHOLDS[key];
  if (!t) return 0;
  for (let i = t.length - 1; i >= 0; i -= 1) {
    if (value >= t[i]) return i + 1;
  }
  return 0;
}

function statTierLabel(key: keyof Stats, value: number): string {
  const list = STAT_TIER_LABELS[key];
  if (!list) return '';
  return list[statTier(key, value)] || '';
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || response.statusText);
  }
  return response.json();
}

function displayItem(item: Item): string {
  const id = item.item_id || item.itemId || '';
  return itemLabels[id] || item.name || id;
}

function stars(value: number): string {
  return value >= 6 ? '★★★★★★' : '★★★★★'.slice(0, Math.floor(value)) + (value % 1 ? '☆' : '');
}

function hpPercent(hp: number, maxHp: number): string {
  if (!maxHp) return '0%';
  return `${Math.max(0, Math.min(100, (hp / maxHp) * 100))}%`;
}

export function App() {
  const [game, setGame] = useState<GameState | null>(null);
  const [view, setView] = useState<View>('jianghu');
  const [selectedName, setSelectedName] = useState<string>('');
  const [newName, setNewName] = useState('');
  const [replaceMode, setReplaceMode] = useState(false);
  const [notice, setNotice] = useState('');
  const [battle, setBattle] = useState<BattleResult | null>(null);
  const [eventIndex, setEventIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [choiceOptions, setChoiceOptions] = useState<any | null>(null);

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (!battle || !playing) return;
    if (eventIndex >= battle.events.length - 1) {
      setPlaying(false);
      return;
    }
    const timer = window.setTimeout(() => setEventIndex((current) => current + 1), 680 / speed);
    return () => window.clearTimeout(timer);
  }, [battle, eventIndex, playing, speed]);

  // 提示自动消失
  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(''), 3400);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const selected = useMemo(() => {
    if (!game) return null;
    return game.fighters.find((fighter) => fighter.name === selectedName) || game.activeFighter || game.fighters[0] || null;
  }, [game, selectedName]);

  const currentEvent = battle?.events[eventIndex];
  const battleHp = useMemo(() => {
    if (!battle) return null;
    let a = battle.attacker.stats.hp;
    let b = battle.defender.stats.hp;
    for (const event of battle.events.slice(0, eventIndex + 1)) {
      if (event.type === 'damage' && event.target === 'a' && typeof event.hpAfter === 'number') a = event.hpAfter;
      if (event.type === 'damage' && event.target === 'b' && typeof event.hpAfter === 'number') b = event.hpAfter;
      if (event.type === 'battle_end' && event.final) {
        a = event.final.a.hp;
        b = event.final.b.hp;
      }
    }
    return { a, b };
  }, [battle, eventIndex]);

  async function refresh() {
    const state = await api<GameState>('/api/session/bootstrap');
    setGame(state);
    if (!selectedName && state.activeFighter) setSelectedName(state.activeFighter.name);
  }

  async function mutate<T>(action: () => Promise<T>, success: string) {
    try {
      setNotice('');
      const result: any = await action();
      if (result.state) setGame(result.state);
      if (result.snapshot) setGame(result.snapshot);
      setNotice(success);
      return result;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : String(error));
      return null;
    }
  }

  async function createFighter(slot?: number) {
    if (!newName.trim()) {
      setNotice('请输入角色名');
      return;
    }
    const result = await mutate(
      () =>
        api('/api/fighters', {
          method: 'POST',
          body: JSON.stringify({ name: newName.trim(), replaceSlot: slot }),
        }),
      slot ? '旧命格已替换' : '角色已入江湖',
    );
    if (result) {
      setNewName('');
      setReplaceMode(false);
      setSelectedName(result.fighter.name);
      setView('fighters');
    } else if (game && game.fighters.length >= game.session.maxFighters) {
      setReplaceMode(true);
    }
  }

  async function startBattle() {
    const result = await mutate<BattleResult>(
      () =>
        api('/api/battles/duel', {
          method: 'POST',
          body: JSON.stringify({ attackerName: selected?.name || undefined }),
        }),
      '战斗已结算，正在播放',
    );
    if (result) {
      setBattle(result as BattleResult);
      setEventIndex(0);
      setPlaying(true);
      setView('battle');
    }
  }

  if (!game) {
    return <div className="loading">正在铺开江湖卷轴...</div>;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-main">江湖行</span>
          <span className="seal">名战</span>
        </div>
        <nav>
          {[
            ['jianghu', '总览'],
            ['fighters', '人物'],
            ['battle', '对战'],
            ['shop', '背包'],
            ['leaderboard', '排行'],
            ['boss', '世界BOSS'],
          ].map(([key, label]) => (
            <button key={key} className={view === key ? 'active' : ''} onClick={() => setView(key as View)}>
              {label}
            </button>
          ))}
        </nav>
        <div className="resource-strip">
          <span>积分 {game.wallet.points}</span>
          <button onClick={() => mutate(() => api('/api/signin', { method: 'POST' }), '今日签到完成')}>签到</button>
        </div>
      </header>

      <main className="game-grid">
        <aside className="side-panel">
          <h2>角色信息</h2>
          {game.activeFighter ? <HeroCard fighter={game.activeFighter} compact /> : <p>尚无出战角色</p>}
          <DailyPanel game={game} />
        </aside>

        <section className="main-panel">
          {notice && <div className="notice" key={notice}>{notice}</div>}
          <div className="view-stage" key={view}>
          {view === 'jianghu' && (
            <JianghuView
              game={game}
              newName={newName}
              setNewName={setNewName}
              createFighter={() => createFighter()}
              startBattle={startBattle}
              setView={setView}
              battle={battle}
              currentEvent={currentEvent}
              battleHp={battleHp}
              eventIndex={eventIndex}
              setEventIndex={setEventIndex}
              playing={playing}
              setPlaying={setPlaying}
              speed={speed}
              setSpeed={setSpeed}
            />
          )}
          {view === 'fighters' && (
            <FightersView
              game={game}
              selected={selected}
              selectedName={selectedName}
              setSelectedName={setSelectedName}
              newName={newName}
              setNewName={setNewName}
              replaceMode={replaceMode}
              setReplaceMode={setReplaceMode}
              createFighter={createFighter}
              setActive={(name: string) =>
                mutate(
                  () =>
                    api('/api/fighters/active', {
                      method: 'POST',
                      body: JSON.stringify({ name }),
                    }),
                  '已设为当前出战',
                )
              }
              feed={(name: string, itemId: string) =>
                mutate(
                  () =>
                    api(`/api/fighters/${encodeURIComponent(name)}/feed`, {
                      method: 'POST',
                      body: JSON.stringify({ itemId, quantity: 1 }),
                    }),
                  '培养完成',
                )
              }
              breakthrough={(name: string) =>
                mutate(() => api(`/api/fighters/${encodeURIComponent(name)}/breakthrough`, { method: 'POST' }), '突破完成')
              }
              reroll={(name: string, category: string, itemId: string) =>
                mutate(
                  () =>
                    api(`/api/fighters/${encodeURIComponent(name)}/reroll`, {
                      method: 'POST',
                      body: JSON.stringify({ category, itemId }),
                    }),
                  '洗练完成',
                )
              }
              createChoices={async (name: string) => {
                const result: any = await mutate(
                  () =>
                    api(`/api/fighters/${encodeURIComponent(name)}/choices`, {
                      method: 'POST',
                      body: JSON.stringify({ category: 'martial_art', itemId: 'martial_token_choice' }),
                    }),
                  '候选已生成',
                );
                if (result) setChoiceOptions(result.result);
              }}
            />
          )}
          {view === 'battle' && (
            <BattleView
              battle={battle}
              currentEvent={currentEvent}
              hp={battleHp}
              eventIndex={eventIndex}
              setEventIndex={setEventIndex}
              playing={playing}
              setPlaying={setPlaying}
              speed={speed}
              setSpeed={setSpeed}
              startBattle={startBattle}
            />
          )}
          {view === 'shop' && <ShopView game={game} buy={(id, quantity) => mutate(() => api('/api/shop/buy', { method: 'POST', body: JSON.stringify({ itemId: id, quantity }) }), '购买成功')} />}
          {view === 'leaderboard' && <LeaderboardView entries={game.leaderboard} />}
          {view === 'boss' && <BossView boss={game.worldBoss} />}
          </div>
        </section>

        <aside className="right-panel">
          <h2>江湖册</h2>
          {selected ? <DetailPanel fighter={selected} /> : <p>选择一个角色查看详情。</p>}
          {choiceOptions && (
            <div className="choice-box">
              <h3>天机候选</h3>
              {choiceOptions.options.map((option: Entry) => (
                <button
                  key={option.id}
                  onClick={async () => {
                    await mutate(
                      () =>
                        api(`/api/fighters/${encodeURIComponent(choiceOptions.fighter_name)}/choices/apply`, {
                          method: 'POST',
                          body: JSON.stringify({ category: choiceOptions.category, choiceId: option.id }),
                        }),
                      '候选已确认',
                    );
                    setChoiceOptions(null);
                  }}
                >
                  {option.name}
                </button>
              ))}
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

function HeroCard({ fighter, compact = false }: { fighter: Fighter; compact?: boolean }) {
  return (
    <div className={`hero-card ${compact ? 'compact' : ''}`}>
      <FighterPortrait fighter={fighter} />
      <div className="hero-meta">
        <h3>{fighter.name}</h3>
        <p className="star-line"><span className="star-symbols">{stars(fighter.starRating)}</span><span className="star-num">{fighter.starRating.toFixed(1)}星</span></p>
        <p className="style-line">{fighter.martialArt.name}</p>
        <StatBars stats={fighter.stats} />
      </div>
    </div>
  );
}

function FighterPortrait({ fighter, size = 'normal' }: { fighter: Fighter; size?: 'normal' | 'large' | 'arena' }) {
  const [failed, setFailed] = useState(false);
  const rating = fighter.starRating || 0;
  const breakthrough = fighter.breakthroughStage || 0;
  const hasCard = (rating >= 5 || breakthrough > 0) && !failed;
  const cardUrl = hasCard && fighter.cardUrl ? `${API_BASE}${fighter.cardUrl}` : '';
  const tierClass = rating >= 6 || breakthrough > 0 ? 'tier-6' : rating >= 5 ? 'tier-5' : rating >= 4 ? 'tier-4' : 'tier-3';
  if (cardUrl) {
    return (
      <div className={`portrait portrait-card ${tierClass} size-${size}`}>
        <img src={cardUrl} alt={`${fighter.name} card`} onError={() => setFailed(true)} />
      </div>
    );
  }
  // 低星/未生成卡面的回落：纸卷式水墨大字
  return (
    <div className={`portrait portrait-ink ${tierClass} size-${size}`}>
      <div className="ink-scroll">
        <span className="ink-char">{fighter.name.slice(0, 1)}</span>
        <span className="ink-sub">{fighter.martialArt?.name?.slice(0, 2) || ''}</span>
      </div>
      <span className="ink-seal">{rating >= 5 ? '绝' : rating >= 4 ? '上' : '中'}</span>
    </div>
  );
}

function StatBars({ stats }: { stats: Stats }) {
  // 把所有六维都展示出来，颜色与档位严格对齐原版
  const rows: Array<[keyof Stats, string, number, boolean]> = [
    ['hp',  '气血', 900, false],
    ['atk', '攻击', 180, false],
    ['def', '防御', 160, false],
    ['spd', '速度', 130, false],
    ['crt', '暴击', 50,  true],
    ['eva', '闪避', 50,  true],
  ];
  return (
    <div className="stat-bars">
      {rows.map(([key, label, max, isPercent]) => {
        const value = Number(stats[key]);
        const tier = statTier(key, value);
        const pct = hpPercent(value, max);
        const tierLabel = statTierLabel(key, value);
        return (
          <div className={`stat-row tier-${tier}`} key={key} title={`${label} ${isPercent ? value.toFixed(1) + '%' : value.toFixed(0)} · ${tierLabel}`}>
            <span className="stat-label">{label}</span>
            <div className="stat-track"><i style={{ width: pct }} /></div>
            <b className="stat-value">{isPercent ? value.toFixed(1) + '%' : value.toFixed(0)}</b>
          </div>
        );
      })}
    </div>
  );
}

function DailyPanel({ game }: { game: GameState }) {
  const activeBoss = game.worldBoss?.activity;
  return (
    <div className="paper-section">
      <h3>日常</h3>
      <p>角色仓库 {game.fighters.length}/{game.session.maxFighters}</p>
      <p>背包物品 {game.items.reduce((sum, item) => sum + Number(item.quantity || 0), 0)}</p>
      <p>世界BOSS {activeBoss ? `${activeBoss.phase2_current_hp}/${activeBoss.phase2_max_hp}` : '未开启'}</p>
    </div>
  );
}

function JianghuView({
  game,
  newName,
  setNewName,
  createFighter,
  startBattle,
  setView,
  battle,
  currentEvent,
  battleHp,
  eventIndex,
  setEventIndex,
  playing,
  setPlaying,
  speed,
  setSpeed,
}: any) {
  const active = game.activeFighter;
  const boss = game.worldBoss?.activity;
  return (
    <div className="overview-view">
      <section className="center-stage">
        {game.needsFirstFighter ? (
          <div className="stage-empty">
            <span className="section-mark">Name Fight</span>
            <h1>创建你的第一名角色</h1>
            <CreateBox newName={newName} setNewName={setNewName} createFighter={createFighter} />
          </div>
        ) : battle ? (
          <BattleView
            battle={battle}
            currentEvent={currentEvent}
            hp={battleHp}
            eventIndex={eventIndex}
            setEventIndex={setEventIndex}
            playing={playing}
            setPlaying={setPlaying}
            speed={speed}
            setSpeed={setSpeed}
            startBattle={startBattle}
          />
        ) : (
          <StageReady active={active} startBattle={startBattle} setView={setView} />
        )}
      </section>

      <section className="workflow-grid">
        <button className="workflow-card" onClick={() => setView('fighters')}>
          <span>01</span>
          <h3>角色仓库</h3>
          <p>当前 {game.fighters.length}/{game.session.maxFighters} 名角色，可创建、替换并设置出战。</p>
        </button>
        <button className="workflow-card" onClick={() => setView('fighters')}>
          <span>02</span>
          <h3>培养养成</h3>
          <p>使用升星丹、突破丹和武学洗练道具，全部走现有道具体系。</p>
        </button>
        <button className="workflow-card" onClick={startBattle}>
          <span>03</span>
          <h3>1v1 试炼</h3>
          <p>调用现有战斗引擎结算，再用血条、伤害飘字和战报回放。</p>
        </button>
        <button className="workflow-card" onClick={() => setView('leaderboard')}>
          <span>04</span>
          <h3>排行榜</h3>
          <p>{game.leaderboard.length ? `已有 ${game.leaderboard.length} 条排行记录。` : '完成一场战斗后进入排行。'}</p>
        </button>
      </section>

      <section className="status-grid">
        <div className="status-card">
          <h3>当前出战</h3>
          {active ? (
            <>
              <p>{active.name} | {active.martialArt.name}</p>
              <p>气血 {active.stats.hp} / 攻击 {active.stats.atk} / 防御 {active.stats.def}</p>
            </>
          ) : (
            <p>暂无出战角色。</p>
          )}
        </div>
        <div className="status-card">
          <h3>资源</h3>
          <p>积分 {game.wallet.points}</p>
          <p>背包物品 {game.items.reduce((sum: number, item: Item) => sum + Number(item.quantity || 0), 0)}</p>
        </div>
        <div className="status-card">
          <h3>世界BOSS</h3>
          {boss ? (
            <>
              <p>{boss.boss_name}</p>
              <p>二阶段气血 {boss.phase2_current_hp}/{boss.phase2_max_hp}</p>
            </>
          ) : (
            <p>未开启。</p>
          )}
        </div>
      </section>
    </div>
  );
}

function StageReady({ active, startBattle, setView }: { active: Fighter | null; startBattle: () => void; setView: (view: View) => void }) {
  return (
    <div className="stage-ready">
      <div className="stage-ink-bg" />
      <div className="stage-fighter left">
        {active ? <FighterPortrait fighter={active} size="large" /> : (
          <div className="portrait portrait-ink tier-3 size-large empty">
            <div className="ink-scroll"><span className="ink-char">?</span></div>
          </div>
        )}
        <h3>{active?.name || '暂无角色'}</h3>
        <p>{active ? `${active.martialArt.name} / ${active.neigong.name}` : '请先创建角色'}</p>
      </div>
      <div className="stage-versus">
        <span>VS</span>
        <button onClick={startBattle} disabled={!active}>开始试炼</button>
      </div>
      <div className="stage-fighter right ghost">
        <div className="portrait portrait-ink tier-3 size-large">
          <div className="ink-scroll"><span className="ink-char">影</span><span className="ink-sub">试炼</span></div>
          <span className="ink-seal">影</span>
        </div>
        <h3>试炼影身</h3>
        <p>按当前角色生成的试炼对手</p>
      </div>
      <div className="stage-footer">
        <button onClick={() => setView('fighters')}>角色仓库</button>
        <button onClick={() => setView('shop')}>培养道具</button>
        <button onClick={() => setView('leaderboard')}>排行榜</button>
      </div>
    </div>
  );
}

function CreateBox({ newName, setNewName, createFighter }: any) {
  return (
    <div className="create-box">
      <h2>创建角色</h2>
      <input value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="输入角色名" />
      <button onClick={createFighter}>创建</button>
    </div>
  );
}

function FightersView(props: any) {
  const { game, selectedName, setSelectedName, newName, setNewName, replaceMode, setReplaceMode, createFighter, setActive, feed, breakthrough, reroll, createChoices } = props;
  return (
    <div className="fighters-view">
      <div className="toolbar">
        <input value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="新角色名" />
        <button onClick={() => createFighter()}>创建</button>
        <button onClick={() => setReplaceMode(!replaceMode)}>替换栏位</button>
      </div>
      {replaceMode && (
        <div className="replace-strip">
          {game.fighters.map((fighter: Fighter) => (
            <button key={fighter.name} onClick={() => createFighter(fighter.slotIndex)}>
              替换 {fighter.slotIndex}. {fighter.name}
            </button>
          ))}
        </div>
      )}
      <div className="card-grid">
        {game.fighters.map((fighter: Fighter) => (
          <button key={fighter.name} className={`fighter-card ${selectedName === fighter.name ? 'selected' : ''}`} onClick={() => setSelectedName(fighter.name)}>
            <HeroCard fighter={fighter} />
          </button>
        ))}
      </div>
      {props.selected && (
        <div className="operation-panel">
          <button onClick={() => setActive(props.selected.name)}>设为出战</button>
          <button onClick={() => feed(props.selected.name, 'star_exp_pill_s')}>小丹培养</button>
          <button onClick={() => feed(props.selected.name, 'star_exp_pill_m')}>中丹培养</button>
          <button onClick={() => breakthrough(props.selected.name)}>突破</button>
          <button onClick={() => reroll(props.selected.name, 'martial_art', 'martial_token_basic')}>洗武学</button>
          <button onClick={() => reroll(props.selected.name, 'neigong', 'martial_token_type')}>换内功</button>
          <button onClick={() => reroll(props.selected.name, 'qinggong', 'martial_token_type')}>换轻功</button>
          <button onClick={() => createChoices(props.selected.name)}>天机候选</button>
        </div>
      )}
    </div>
  );
}

function DetailPanel({ fighter }: { fighter: Fighter }) {
  const rows: Array<[keyof Stats, string, boolean]> = [
    ['hp', '气血', false],
    ['atk', '攻击', false],
    ['def', '防御', false],
    ['spd', '速度', false],
    ['crt', '暴击', true],
    ['eva', '闪避', true],
  ];
  return (
    <div className="detail-panel">
      <h3>{fighter.name}</h3>
      <p>战绩 {fighter.wins}/{fighter.battles}</p>
      <p>资质 {fighter.starRating.toFixed(1)} 星</p>
      <p>武学 {fighter.martialArt.name}</p>
      <p>内功 {fighter.neigong.name}</p>
      <p>轻功 {fighter.qinggong.name}</p>
      <div className="tier-grid">
        {rows.map(([key, label, isPercent]) => {
          const value = Number(fighter.stats[key]);
          const tier = statTier(key, value);
          const comment = statTierLabel(key, value);
          const valText = isPercent ? `${value.toFixed(1)}%` : value.toFixed(0);
          return (
            <div className={`tier-chip tier-${tier}`} key={key} title={`${label} ${valText} · ${comment}`}>
              <span className="chip-label">{label}</span>
              <span className="chip-value">{valText}</span>
              <span className="chip-comment">{comment}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function BattleView({ battle, currentEvent, hp, eventIndex, setEventIndex, playing, setPlaying, speed, setSpeed, startBattle }: any) {
  if (!battle) {
    return (
      <div className="empty-battle">
        <h2>战斗剧场</h2>
        <p>选择当前出战角色后，可以直接开始一场试炼。</p>
        <button onClick={startBattle}>开始试炼</button>
      </div>
    );
  }
  const aHp = hp?.a ?? battle.attacker.stats.hp;
  const bHp = hp?.b ?? battle.defender.stats.hp;
  return (
    <div className="battle-view">
      <div className="battle-status">
        <span>{eventIndex >= battle.events.length - 1 ? '战斗已结束，正在回放' : '战斗回放中'}</span>
        <button title="战斗仍由现有引擎结算，这里只负责可视化回放。">?</button>
      </div>
      <div className="arena">
        <Combatant side="left" fighter={battle.attacker} hp={aHp} active={currentEvent?.actor === 'a'} hit={currentEvent?.target === 'a' && currentEvent?.type === 'damage'} />
        <div className="clash-mark">{currentEvent?.type === 'damage' ? `-${currentEvent.amount}` : currentEvent?.type === 'dodge' ? '闪' : '战'}</div>
        <Combatant side="right" fighter={battle.defender} hp={bHp} active={currentEvent?.actor === 'b'} hit={currentEvent?.target === 'b' && currentEvent?.type === 'damage'} />
        <DamageLayer event={currentEvent} eventIndex={eventIndex} />
      </div>
      <div className="battle-controls">
        <button onClick={() => setPlaying(!playing)}>{playing ? '暂停' : '播放'}</button>
        <button onClick={() => setEventIndex(0)}>重播</button>
        <button onClick={() => setEventIndex(battle.events.length - 1)}>跳过</button>
        <button onClick={() => setSpeed(speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1)}>倍速 {speed}x</button>
      </div>
      <div className="battle-log">
        <h3>战报</h3>
        {visibleBattleLogs(battle, eventIndex).map((line: string, index: number) => (
          <p key={`${index}-${line}`}>{line}</p>
        ))}
      </div>
    </div>
  );
}

function visibleBattleLogs(battle: BattleResult, eventIndex: number): string[] {
  const logs = battle.displayLogs?.length ? battle.displayLogs : battle.logs;
  if (!logs.length) return [];
  const progress = battle.events.length <= 1 ? 1 : eventIndex / (battle.events.length - 1);
  const visibleCount = Math.max(1, Math.ceil(logs.length * progress));
  return logs.slice(0, visibleCount);
}

function Combatant({ side, fighter, hp, active, hit }: { side: string; fighter: Fighter; hp: number; active: boolean; hit: boolean }) {
  return (
    <div className={`combatant ${side} ${active ? 'active' : ''} ${hit ? 'hit' : ''}`}>
      <div className="hp-line"><i style={{ width: hpPercent(hp, fighter.stats.hp) }} /></div>
      <FighterPortrait fighter={fighter} size="arena" />
      <h3>{fighter.name}</h3>
      <p>{hp}/{fighter.stats.hp}</p>
    </div>
  );
}

function DamageLayer({ event, eventIndex }: { event?: BattleEvent; eventIndex: number }) {
  if (!event) return null;
  const isDamage = event.type === 'damage' && typeof event.amount === 'number';
  const isDodge = event.type === 'dodge';
  if (!isDamage && !isDodge) return null;
  const side = event.target === 'a' ? 'left' : 'right';
  const style: CSSProperties = side === 'left' ? { left: '25%' } : { left: '75%' };
  let cls = 'damage-pop';
  let text = '';
  if (isDamage) {
    cls += event.crit ? ' crit' : '';
    text = event.crit ? `暴击 -${event.amount}` : `-${event.amount}`;
  } else {
    cls += ' dodge';
    text = '闪';
  }
  return (
    <div className="damage-layer">
      <div key={`${eventIndex}-${event.type}-${event.target}`} className={cls} style={style}>{text}</div>
    </div>
  );
}

function ShopView({ game, buy }: { game: GameState; buy: (id: string, quantity: number) => void }) {
  return (
    <div className="shop-view">
      <section>
        <h2>商店</h2>
        <div className="shop-grid">
          {game.shop.map((item) => (
            <div className="shop-card" key={item.item_id}>
              <h3>{displayItem(item)}</h3>
              <p>价格 {item.price}</p>
              <button onClick={() => buy(item.item_id, 1)}>购买</button>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2>背包</h2>
        <div className="bag-list">
          {game.items.length ? game.items.map((item) => <p key={item.item_id}>{displayItem(item)} x{item.quantity}</p>) : <p>背包空空。</p>}
        </div>
      </section>
    </div>
  );
}

function LeaderboardView({ entries }: { entries: LeaderboardEntry[] }) {
  return (
    <div className="leaderboard">
      <h2>巅峰排行</h2>
      {entries.length ? entries.map((entry, index) => (
        <div className="rank-row" key={entry.fighter_name}>
          <b>{index + 1}</b>
          <span>{entry.fighter_name}</span>
          <i>{entry.elo_rating}</i>
          <em>{entry.wins}/{entry.battles}</em>
        </div>
      )) : <p>暂无排行，先打一场。</p>}
    </div>
  );
}

function BossView({ boss }: { boss: any }) {
  const activity = boss?.activity;
  if (!activity) {
    return <div className="boss-view"><h2>世界BOSS</h2><p>当前没有开启的世界BOSS。</p></div>;
  }
  return (
    <div className="boss-view">
      <h2>{activity.boss_name}</h2>
      <div className="boss-hp"><i style={{ width: hpPercent(activity.phase2_current_hp, activity.phase2_max_hp) }} /></div>
      <p>{activity.phase2_current_hp}/{activity.phase2_max_hp}</p>
      <p>今日剩余挑战 {boss.remainingAttempts}/{boss.dailyLimit}</p>
      <h3>贡献榜</h3>
      {boss.rank?.length ? boss.rank.map((entry: any, index: number) => <p key={entry.user_id}>{index + 1}. {entry.display_name} {entry.total_damage}</p>) : <p>暂无贡献。</p>}
    </div>
  );
}
