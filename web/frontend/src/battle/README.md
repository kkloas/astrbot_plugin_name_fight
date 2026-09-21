# Ink Battle Replay

Procedural ink figures remain independent of character portraits. All 11 configured
martial arts and 70 moves have explicit visual mappings in `martialVisuals.ts`.
Weapon silhouettes cover swords, katana, blades, spears, judge pens, unarmed combat,
needles and zither. Palm and leg styles have different unarmed actions. Audio is not implemented.

- `engine.py` records real mutations during combat without additional RNG calls.
- Each turn starts on a 1900 ms presentation interval. Attacks begin at +550 ms,
  impacts at +950 ms, and turn logs/status snapshots arrive at +1600 ms.
- Damage carries the rolled amount plus exact HP before/after; overkill is clamped
  in HP, not in the displayed damage. Healing and reflected damage are separate events.
- `replay.ts` derives HP, statuses and logs from the same clock used by `InkStage`.
- Drawing is deterministic. Pause, speed, seek and replay do not run combat again.
- Initiative events record original tick accumulation, effective speeds, spending,
  first-strike boosts and low-HP boosts. Overflow above 100 is preserved.
  The HUD's initiative interpolation spreads the next recorded accumulation over
  the preceding exchange, so bars grow throughout the animation instead of snapping
  during the short turn gap. The scheduler and attack order are unchanged; boosts
  rebase interpolation, while speed changes alter its continuous growth rate.
  Raw snapshots remain available in stateAt.
- `inkWeapons.ts` draws weapons; `inkStrikes.ts` draws brush-stroke attacks,
  preparation and impact bursts. `inkEffects.ts` handles status auras,
  healing, leeching, reflection, guard and lightness-skill triggers.
- `choreography.ts` samples planted steps and deterministic contact holds.
  Melee advances include foot swings, a final lunge and a backward step or bound.
  Per-move patterns distinguish cross cuts, falling cuts, needle fans/rain,
  sound crescendos and focused thrusts; historical poses generate afterimages.
- Impact force uses strike damage / target maximum HP, with a small critical bonus.
  Heavy hits require at least 22% HP damage, or a critical hit of at least 13%.
  Camera emphasis additionally requires 32% damage or a weight >= 1.5 heavy move.
  Dodges have no impact burst. Visual contact holds last 22-100 ms and catch up
  within the same turn; event timestamps, HP and combat rules remain unchanged.
  Reduced-motion preferences disable camera translation and zoom.
- Internal skill effects distinguish leaf-like regeneration, scattered blood
  particles, armor-shaped guard, outward reflection, cloud-like burst healing and
  persistent crisis-defense outlines. Leeching has no connecting beam or line.
  All seven lightness styles use different trails sampled from actual past poses.
  Concurrent trigger captions are retained below the stage, outside the HUD.
- Victory metadata uses the existing text-outro classification: judged wins first,
  then <=5-action quick wins, >=55% HP dominant wins, <=20% HP clutch wins,
  otherwise standard wins; draws have their own sequence. Each has three cosmetic
  variants selected by a digest of the already-randomized battle log, without extra
  combat RNG calls. A 1.8-second deterministic closing animation precedes battle_end.
- Persistent statuses and weapon availability follow engine snapshots. A disarmed
  fighter retrieves the weapon during the skipped turn, not via a cosmetic timer.
- Source skill metadata identifies real passive triggers. Descriptive text is never
  parsed for mechanics: for example, the poisonous-needle prose does not add poison
  damage, and a visual flurry still has only the engine's single damage event.
- `guard` reports the existing body-part multiplier, including vulnerable areas;
  it does not invent a successful block or extra damage reduction.
- `battle.css` is scoped to the battle surface. On phones the battle takes priority
  over side panels; role management remains in its original tab.
- Vite proxies `/api` to the local backend on port 8000, including when its own port
  changes. Production hosting needs the equivalent `/api` reverse proxy.

## Verification

From the repository root:

```powershell
python -m unittest test_battle_events test_battle_visuals test_web_battle_events -v
python -m unittest test_action_gauge -v
python test_battle_visuals.py --fixtures
python test_action_gauge.py --fixtures
python test_battle_events.py --fixture
```

Build with `npm run build` in `web/frontend`.

`web/frontend/verify-battle.cjs` uses Playwright and a recorded engine fixture at
`output/playwright/battle-fixture.json`. It targets Vite on port 5175, reads the real
bootstrap, and intercepts duel requests so no player battles are recorded. Set
`PLAYWRIGHT_MODULE` to an installed Playwright package directory when it is not
available through normal Node resolution. Screenshots are written to `output/playwright`.

`web/frontend/verify-martial.cjs` consumes the generated `martial-fixtures.json`,
checks every mapped move and 13 configured effect categories, and captures desktop
and mobile examples. The fixtures are generated from actual config data; no live
player inventory, loadout or battle record is changed by the browser checks.

`web/frontend/verify-choreography.cjs` checks damage-relative force, dodge suppression,
planted-foot coordinates and contact-time monotonicity. It samples six move sequences
at six phases, verifies deterministic seeking and saves a visual contact sheet.

`web/frontend/verify-initiative.cjs` checks raw gauge/speed snapshots, continuous
HUD accumulation during attacks, all 14 internal/lightness skills, deterministic
replay and five viewport widths. `verify-victory.cjs` isolates the 18 cosmetic
category/variant combinations without writing player records.
