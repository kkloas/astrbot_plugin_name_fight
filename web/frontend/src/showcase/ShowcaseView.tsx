import { useEffect, useState } from 'react';
import { BattleView } from '../battle/BattleView';
import { useBattlePlayback, type ReplayBattle } from '../battle/replay';

type Entry = { id: string; name: string };
type Config = { martialArts: Entry[]; neigong: Entry[]; qinggong: Entry[] };
type Stats = { hp: number; atk: number; def: number; spd: number; crt: number; eva: number };
type Fighter = { name: string; stats: Stats; martialArt: Entry; neigong: Entry; qinggong: Entry };
const labels: Record<keyof Stats, string> = { hp: '气血', atk: '攻击', def: '防御', spd: '速度', crt: '暴击', eva: '闪避' };

export function ShowcaseView({ request }: { request: <T>(path: string, init?: RequestInit) => Promise<T> }) {
  const [config, setConfig] = useState<Config | null>(null);
  const [fighters, setFighters] = useState<(Fighter | null)[]>([null, null]);
  const [battle, setBattle] = useState<ReplayBattle | null>(null);
  const [error, setError] = useState('');
  const playback = useBattlePlayback(battle);
  async function random(index: number) {
    try {
      const fighter = await request<Fighter>('/api/admin/practice/random', { method: 'POST' });
      fighter.name = index === 0 ? '演武甲' : '演武乙';
      setFighters(current => current.map((item, i) => i === index ? fighter : item));
      setError('');
    } catch (e) { setError(e instanceof Error ? e.message : '生成失败'); }
  }
  useEffect(() => {
    request<Config>('/api/admin/practice/config').then(setConfig).catch(e => setError(String(e)));
    void random(0); void random(1);
  }, []);
  function update(index: number, fighter: Fighter) {
    setFighters(current => current.map((item, i) => i === index ? fighter : item));
  }
  async function start() {
    if (!fighters[0] || !fighters[1]) return;
    const payload = (fighter: Fighter) => ({ name: fighter.name, stats: fighter.stats, martialArtId: fighter.martialArt.id, neigongId: fighter.neigong.id, qinggongId: fighter.qinggong.id });
    try {
      setBattle(await request<ReplayBattle>('/api/admin/practice/battle', { method: 'POST', body: JSON.stringify({ attacker: payload(fighters[0]), defender: payload(fighters[1]) }) }));
      setError('');
    } catch (e) { setError(e instanceof Error ? e.message : '演武失败'); }
  }
  return <div className="showcase-view">
    <section className="showcase-intro">
      <h2>演武堂 · 管理员测试</h2>
      <p>随机生成角色后可调整战斗属性和功法. 演武不会改变玩家存档, 输入的是实际战斗属性.</p>
      <div className="showcase-cards">{fighters.map((fighter, index) => fighter && config && <article key={index}>
        <h3>{index === 0 ? '甲方' : '乙方'}</h3>
        <label>角色名 <input value={fighter.name} maxLength={40} onChange={e => update(index, { ...fighter, name: e.target.value })} /></label>
        <div className="practice-stats">{(Object.keys(labels) as (keyof Stats)[]).map(key => <label key={key}>{labels[key]} <input type="number" min={key === 'hp' || key === 'spd' ? 1 : 0} max={key === 'crt' || key === 'eva' ? 100 : key === 'hp' ? 1000000 : 100000} step={key === 'crt' || key === 'eva' || key === 'spd' ? 'any' : 1} value={fighter.stats[key]} onChange={e => update(index, { ...fighter, stats: { ...fighter.stats, [key]: Number(e.target.value) } })} /></label>)}</div>
        {([['martialArt', '武学', config.martialArts], ['neigong', '内功', config.neigong], ['qinggong', '轻功', config.qinggong]] as const).map(([key, label, options]) => <label key={key}>{label} <select value={fighter[key].id} onChange={e => { const entry = options.find(item => item.id === e.target.value); if (entry) update(index, { ...fighter, [key]: entry }); }}>{options.map(entry => <option key={entry.id} value={entry.id}>{entry.name}</option>)}</select></label>)}
        <button onClick={() => void random(index)}>重新随机生成</button>
      </article>)}</div>
      <div className="showcase-actions"><button onClick={() => void start()}>开始演武</button><a href="/motion-preview.html" target="_blank" rel="noreferrer">进入招式与功法特效拆解台</a></div>
      {error && <p role="alert">{error}</p>}
    </section>
    <BattleView battle={battle} playback={playback} startBattle={() => void start()} />
  </div>;
}
