import { useState } from 'react';
import { BattleView } from '../battle/BattleView';
import { useBattlePlayback, type ReplayBattle } from '../battle/replay';
import type { SceneTheme } from '../battle/InkStage';

const cards = [
  { id: 'ink', title: '玄墨剑典', sub: '太极玄墨功 · 踏雪无痕', moves: '起笔问墨 / 残月掠影 / 墨影穿云 / 破空剑气 / 泼墨回风 / 太极封锋 / 万剑归宗 / 绝技·一剑霜寒', scene: 'snow' as SceneTheme },
  { id: 'crimson', title: '赤霄断魂刀', sub: '赤霄煞心诀 · 纵云梯', moves: '赤霞横江 / 裂甲断岳 / 残阳撩月 / 血影旋斩 / 焚风踏浪 / 赤练裂地 / 狂煞乱舞 / 绝技·赤霄断魂', scene: 'bloodmoon' as SceneTheme },
];

export function ShowcaseView({ request }: { request: <T>(path: string, init?: RequestInit) => Promise<T> }) {
  const [battle, setBattle] = useState<ReplayBattle | null>(null);
  const [scene, setScene] = useState<SceneTheme>('sunset');
  const [error, setError] = useState('');
  const playback = useBattlePlayback(battle);

  async function start(swap = false) {
    setError('');
    try {
      const data = await request<ReplayBattle>('/api/battles/showcase', { method: 'POST', body: JSON.stringify({ swap }) });
      setBattle(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : '演武失败');
    }
  }

  return <div className="showcase-view">
    <section className="showcase-intro">
      <h2>演武堂 · 新武学试演</h2>
      <p>水墨剑影对赤霄断魂：两套新武学、新内功、新轻功全程实战演示。画面为 Web 专属增强版（动态画境、墨色招式特效、琴音）；Bot 版仍使用原有单张底图。</p>
      <div className="showcase-cards">
        {cards.map(card => <article key={card.id}>
          <h3>{card.title}</h3><strong>{card.sub}</strong><p>{card.moves}</p>
          <button onClick={() => setScene(card.scene)}>切换为「{card.scene === 'snow' ? '寒江孤雪' : '朱砂血月'}」画境</button>
        </article>)}
      </div>
      <div className="showcase-actions">
        <button onClick={() => start(false)}>开始演武</button>
        <button onClick={() => start(true)}>交换站位再战</button>
        <a href="/motion-preview.html?art=sword_xuanmo&move=%E4%B8%87%E5%89%91%E5%BD%92%E5%AE%97" target="_blank" rel="noreferrer">逐招拆解台 · 玄墨剑典</a>
        <a href="/motion-preview.html?art=blade_chixiao&move=%E7%BB%9D%E6%8A%80%C2%B7%E8%B5%A4%E9%9C%84%E6%96%AD%E9%AD%82" target="_blank" rel="noreferrer">逐招拆解台 · 赤霄断魂刀</a>
      </div>
      {error && <p role="alert">{error}</p>}
    </section>
    <BattleView key={scene} battle={battle} playback={playback} startBattle={() => start(false)} defaultScene={scene} />
  </div>;
}
