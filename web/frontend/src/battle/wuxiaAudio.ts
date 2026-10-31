// Procedural Web Audio Wuxia Sound Synthesizer (inspired by WuxiaAudio in code_artifact.html).
// Zero external audio assets required; runs purely on Web Audio API in the browser.

class WuxiaSoundEngine {
  private ctx: AudioContext | null = null;
  public enabled = true;

  private ensureContext(): AudioContext | null {
    if (!this.enabled || typeof window === 'undefined') return null;
    const AudioCtor = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtor) return null;
    if (!this.ctx) {
      try {
        this.ctx = new AudioCtor();
      } catch {
        return null;
      }
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  public unlock() {
    this.ensureContext();
  }

  public playSlash(heavy = false, crimson = false) {
    const ctx = this.ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const dur = heavy ? 0.34 : 0.19;
    const length = Math.max(1, Math.floor(ctx.sampleRate * dur));
    const buffer = ctx.createBuffer(1, length, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < length; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 1.55);
    }
    const noise = ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(crimson ? 320 : heavy ? 440 : 760, now);
    filter.frequency.exponentialRampToValueAtTime(crimson ? 980 : 2100, now + dur * 0.45);
    filter.frequency.exponentialRampToValueAtTime(220, now + dur);
    filter.Q.value = crimson ? 2.1 : 1.7;

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(heavy ? 0.24 : 0.14, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + dur);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);
    noise.start(now);
  }

  public playClang(heavy = false) {
    const ctx = this.ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const baseFreq = heavy ? 780 : 1040;
    const osc = ctx.createOscillator();
    const mod = ctx.createOscillator();
    const modGain = ctx.createGain();
    const gain = ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(baseFreq, now);
    osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.58, now + 0.32);

    mod.type = 'sine';
    mod.frequency.setValueAtTime(1480, now);
    modGain.gain.setValueAtTime(520, now);
    modGain.gain.exponentialRampToValueAtTime(8, now + 0.22);

    gain.gain.setValueAtTime(heavy ? 0.20 : 0.13, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

    mod.connect(modGain);
    modGain.connect(osc.frequency);
    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    mod.start(now);
    osc.stop(now + 0.36);
    mod.stop(now + 0.36);
  }

  public playDrum(power = 1) {
    const ctx = this.ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(132, now);
    osc.frequency.exponentialRampToValueAtTime(28, now + 0.38);

    gain.gain.setValueAtTime(Math.min(0.36, 0.22 * power), now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.42);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.44);
  }

  public playHit(heavy = false, crit = false, armed = true) {
    this.playDrum(crit ? 1.45 : heavy ? 1.15 : 0.78);
    if (armed) this.playClang(heavy || crit);
  }

  public playDodge() {
    const ctx = this.ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const dur = 0.14;
    const length = Math.max(1, Math.floor(ctx.sampleRate * dur));
    const buffer = ctx.createBuffer(1, length, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < length; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / length);
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    const filter = ctx.createBiquadFilter();
    filter.type = 'highpass';
    filter.frequency.value = 1200;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.09, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + dur);
    src.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);
    src.start(now);
  }

  public playUltimateGuqin() {
    const ctx = this.ensureContext();
    if (!ctx) return;
    this.playDrum(1.4);
    const notes = [196.0, 220.0, 261.63, 293.66, 392.0];
    notes.forEach((freq, i) => {
      const t = ctx.currentTime + i * 0.055;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, t);

      const lp = ctx.createBiquadFilter();
      lp.type = 'lowpass';
      lp.frequency.setValueAtTime(1350, t);
      lp.frequency.exponentialRampToValueAtTime(240, t + 1.15);

      gain.gain.setValueAtTime(0.001, t);
      gain.gain.linearRampToValueAtTime(0.11, t + 0.018);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 1.25);

      osc.connect(lp);
      lp.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 1.28);
    });
  }
}

export const wuxiaAudio = new WuxiaSoundEngine();
