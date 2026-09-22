# Ink Battle Replay

Procedural ink figures remain independent of character portraits. All 13 configured
martial arts and 86 moves have explicit visual mappings in `martialVisuals.ts`.
The two new arts have sixteen authored motion scores and staged effects. All arts
use the approved curved figure renderer; see [NEW_MARTIAL_REVIEW.md](./NEW_MARTIAL_REVIEW.md).
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
  Reduced-motion preferences disable camera translation. Camera zoom is removed
  so striking never enlarges the figures.
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

## Motion Samples

The game defaults to mixed animation variants. `motionVariants.ts` derives a
cosmetic 50/50 choice for each action from the recorded battle and action identity.
The same move can use either version on successive turns. Pause, seek, replay,
mirrored rendering and JSON round trips retain the choice; no gameplay RNG is used.

The legacy branch uses the retained choreography in `InkStage.tsx` and the
original `legacyTechniqueFor` mapping verified against Git checkpoint `f39413d`.
It uses that version's `drawTechnique`/`drawImpact` effects, without new profile
colors or accents. The current branch uses the new motion samplers and matching
effects. Each action chooses a complete branch, including historical afterimages.
Shared fixed-bone rendering, raised idle posture, removed foot marks and removed
camera zoom remain in both branches; this is not a repository rollback.

`/motion-preview.html` is a standalone, offline-data comparison of all 86 moves.
The original sword thrust, returning spear and airborne kick remain the first
three choices. Both panels share one clock; the left
disables effects, while the right uses the game's effects. No API is called.
The page is also included in the production build.
Its animation selector offers legacy, current and mixed modes. It initially shows
current mode for inspecting the newer samples; normal game battles default to mixed.

`sampleMotion.ts` uses two-bone IK, fixed limb lengths, alternating world-space
foot contacts and explicit timing for the hip, shoulder and striking limb.
Both spear grips share one shaft. Misses extend the follow-through; they never
add damage or change turn order. `moveMotion.ts` retains these three samples and
uses their locomotion foundation for the remaining named moves. Unknown moves
retain the existing fallback animations.
Tip trails sample the same motion clock, including contact holds.

`rig.ts` constrains the final rendered pose to fixed arms, legs, torso, neck and
shoulder width. This includes idle, attacks, reactions, skipped turns, death and
victory, not just the attack sampler. Standing idle has a raised pelvis; legacy
poses can no longer stretch the limbs during interpolation into the new rig.

`swordSequences.ts` overrides only six approved sword samples: You Feng Lai Yi
(descending aerial thrust), Tian Shen Dao Xuan (low rising thrust), Wu Bian Luo Mu
(three thrusts with explicit retractions), Jin Yan Heng Kong (airborne crosscut),
Hui Feng Zhan (two turning cuts), and Qing Shan Yin Yin (concealed burst thrust).
Each has a whole-body score including root travel, elevation, posture and sword
orientation. Other move choreography remains unchanged.
`swordEffects.ts` follows each stroke separately. Qing Shan (1.5 multiplier) and
Luo Mu (1.4) have stronger signature effects regardless of rolled HP damage;
actual hit-only contact bursts still require the engine strike event. The
cosmetic multi-stroke sequence does not add hit events or split damage.

`moveProfiles.ts` maps every configured art/move pair to an authored action style,
preparation timing, trajectory variant and effect theme. `moveMotion.ts` builds
windup, contact and recovery poses, with arcing hand paths around the shoulders
to avoid elbow flips. Spear grips stay on one shaft; ranged moves stay planted.
Leg sweeps compress only during their strike. Horizontal foot marks are removed
from the shared figure renderer, including idle, recovery and victory poses.

`moveEffects.ts` distinguishes petals, leaves, cloud wisps, inward breath curls,
calligraphic hooks, metallic flashes and sound crescents. Their tip trails follow
the sampled weapon or striking foot. Missed attacks aim at the original target
location, without contact bursts. Themes never imply status changes: snow does
not freeze, inward curls do not cause healing, and flurries do not add damage.
The existing true-event status effects and HP-relative impact strength remain.

Running uses an upright pelvis and short airborne strides. Brief compression is
reserved for takeoff, contact and landing; recovery uses a backward leap. The
returning spear sample fades out in midair and reappears before the strike.
Its opacity applies to the body, shadow, afterimages and tip trails, including
the effects-disabled preview. This is presentation only, not teleport mechanics.

The three samples use separate shoulder anchors, outward hand targets and a
150-unit maximum stride, with airborne split-leg poses. The arm IK retains a
small extension margin to avoid a snapping elbow at full extension. Legacy
poses are blended at sample boundaries, then resolved onto the shared rig.

Sword and spear finish their thrust with an extended arm and a longer root
lunge, stopping the body short to account for the greater reach. Cold Branch
Snow uses blue-white tip ribbons, deterministic snowflakes and a snow-crystal
contact burst instead of black hit flecks. Misses have a tip trail but no contact
burst; these effects never add freeze or any other combat status.

`verify-sample-motion.cjs` checks rig geometry, grip alignment, deterministic
seeking, both sides, misses, playback completion and four viewport widths.
`verify-move-profiles.cjs` checks all 70 names against the real configuration,
fixed bone lengths, spear grips, ground clearance, continuous motion, distinct
motion signatures, deterministic effects and narrow-screen preview layout.
It also produces a contact sheet for the main weapon families.
`verify-motion-pve.cjs` runs all 70 move fixtures and 13 effect fixtures through
the current chapter battle UI, intercepting every mutation request. The older
duel-navigation verification scripts target the superseded duel tab.

`verify-sword-revision.cjs` checks the final renderer for all six revised moves,
both sides and five outcomes, including full idle/action/reaction/death/victory
transitions. It asserts constant bone lengths and shoulder width, distinct
descending/rising attack geometry, three thrust extensions, deterministic seeking
and mobile layout, and captures 24 comparison frames.

`verify-motion-variants.cjs` renders all 70 moves in both modes, checks balanced
selection across repeated uses of one move, stable seeking/replay/serialization,
unchanged battle data and exact correspondence between mixed and forced-mode
frames. It also verifies fixed bones in both branches and captures comparisons.
