import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../api';

type Challenge = { code: string; command: string; expiresAt: number };
const CHALLENGE_CACHE_KEY = 'nfight-login-challenge';

function cacheChallenge(challenge: Challenge | null) {
  try {
    if (challenge) localStorage.setItem(CHALLENGE_CACHE_KEY, JSON.stringify(challenge));
    else localStorage.removeItem(CHALLENGE_CACHE_KEY);
  } catch {
    // Cookies still allow verified login recovery when browser storage is disabled.
  }
}

function readCachedChallenge(): Challenge | null {
  try {
    const cached = JSON.parse(localStorage.getItem(CHALLENGE_CACHE_KEY) || 'null');
    if (cached && typeof cached.code === 'string' && /^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{8}$/.test(cached.code)
      && typeof cached.expiresAt === 'number' && cached.expiresAt * 1000 > Date.now()) {
      return { code: cached.code, command: `/nfweb ${cached.code}`, expiresAt: cached.expiresAt };
    }
  } catch {
    // An unavailable or stale cache must not prevent a new login challenge.
  }
  return null;
}

export function LoginView({ onAuthenticated }: { onAuthenticated: () => Promise<void> }) {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [now, setNow] = useState(Date.now());
  const authenticated = useRef(onAuthenticated);
  authenticated.current = onAuthenticated;
  const started = useRef(false);
  const creating = useRef(false);

  async function createChallenge(recover = false) {
    if (creating.current) return;
    creating.current = true;
    setBusy(true);
    setNotice('');
    setChallenge(null);
    try {
      if (recover) {
        try {
          const result = await api<{ status: string }>('/api/auth/challenge/exchange', { method: 'POST' });
          if (result.status === 'authenticated') {
            cacheChallenge(null);
            await authenticated.current();
            return;
          }
          const cached = readCachedChallenge();
          if (cached) {
            setChallenge(cached);
            setNow(Date.now());
            return;
          }
        } catch (error) {
          if (!(error instanceof ApiError && error.status === 410)) throw error;
          cacheChallenge(null);
        }
      }
      const next = await api<Challenge>('/api/auth/challenge', { method: 'POST' });
      cacheChallenge(next);
      setChallenge(next);
      setNow(Date.now());
    } catch (error) {
      setNotice(error instanceof Error ? error.message : String(error));
    } finally {
      creating.current = false;
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!started.current) {
      started.current = true;
      void createChallenge(true);
    }
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!challenge) return;
    let cancelled = false;
    let timer: number;
    async function poll() {
      if (cancelled || Date.now() >= challenge!.expiresAt * 1000) return;
      try {
        const result = await api<{ status: string }>('/api/auth/challenge/exchange', { method: 'POST' });
        if (cancelled) return;
        if (result.status === 'authenticated') {
          cacheChallenge(null);
          await authenticated.current();
          return;
        }
      } catch (error) {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 410) {
          cacheChallenge(null);
          setChallenge(null);
          setNotice('验证码已失效, 请重新获取');
          return;
        }
        setNotice(error instanceof Error ? error.message : String(error));
      }
      if (!cancelled) timer = window.setTimeout(poll, 3000);
    }
    timer = window.setTimeout(poll, 1000);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [challenge]);

  const remaining = challenge ? Math.max(0, Math.ceil((challenge.expiresAt * 1000 - now) / 1000)) : 0;

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(challenge!.command);
      setNotice('已复制, 请发送到 Bot 所在的 QQ 群');
    } catch {
      setNotice('请长按下方指令, 手动复制到 QQ 群');
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-brand"><span className="seal">名战</span><span>江湖行</span></div>
        <h1 id="login-title">用你的 QQ 角色进入江湖</h1>
        <p>验证 QQ 身份后, 自动加载你在群里的角色、积分和背包。</p>
        <ol className="login-steps">
          <li>复制下方指令。</li>
          <li>发送到 Name Fight Bot 所在的 QQ 群。</li>
          <li>回到此页面, 验证成功后会自动进入游戏。</li>
        </ol>
        {challenge && remaining > 0 ? (
          <div className="login-challenge">
            <code aria-label="QQ 群验证指令">{challenge.command}</code>
            <button onClick={copyCommand}>复制验证指令</button>
            <p role="status">等待群内验证, 剩余 {Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, '0')}</p>
          </div>
        ) : (
          <button onClick={() => void createChallenge()} disabled={busy}>{busy ? '正在获取验证码...' : '获取新的验证码'}</button>
        )}
        <p className="login-notice" role="status">{notice}</p>
        <p className="login-footnote">手机和电脑可以同时登录同一个 QQ, 请在每台设备上分别获取验证码并验证. 网页与 QQ 共用存档, 培养、替换角色和使用道具都会同步。仅发送你自己打开的本网页生成的指令。</p>
      </section>
    </main>
  );
}
