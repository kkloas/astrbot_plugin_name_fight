# New Martial Arts And Curved Figures

Checkpoint before this work: `9605cfc`.

## Scope

Two arts are appended to the shared configuration, each with eight moves:
`sword_danyu` and `blade_jingchao`. Existing entries are unchanged. Creation and
compatible reroll pools use the existing repository logic. No data migration or
player record replacement is performed. Restart the backend to reload its
in-memory configuration.

Both signature animations were approved and remain the entry points:

- `/motion-preview.html?art=sword_danyu`: airborne descending sword strike.
- `/motion-preview.html?art=blade_jingchao`: grounded advancing heavy cut.

All sixteen moves now have authored whole-body scores and timed effect strokes.
All thirteen arts use the approved curved figure renderer, in both legacy and
current motion modes. Old arts retain their existing choreography and 50/50
animation selection. New arts never select legacy animations.

## Numerical Contract

The accepted initial stats and sixteen multipliers are unchanged. The sword has
one 25% on-hit slow, speed multiplier 0.85 for two target turns. The blade has one
25% on-hit armor break, defense multiplier 0.8 for two target turns. Both use the
engine's default body-part distribution. Neither adds hard control, extra damage
events, lifesteal, freezing, or guaranteed status application. Cosmetic multiple
strokes still resolve one engine strike.

`python verify_new_martial_balance.py --seeds 16 --output output/new-martial-balance.json`
uses real modifiers and combat, without SQLite. Each new art fights all eleven
existing arts at three base panels, seven rotating internal/lightness pairs,
exchanged loadouts and both sides. Each plays 14,784 battles (29,568 total).

Initial results, draws counted as half a win:

| Art | Aggregate | Against Huashan | Against Shadow Leg |
| --- | ---: | ---: | ---: |
| Danyu | 47.19% | 34.52% | 59.23% |
| Jingchao | 47.25% | 35.49% | 58.78% |

These are fixture-dependent results, not a guarantee of universal balance or an
exhaustive loadout cross-product. Neither candidate dominates this sample.

## Animation Contract

`newMartialMotion.ts` owns sixteen whole-body timelines and fixed-length IK.
`curvedFigure.ts` paints slender quadratic contours for every art and state.
Curvature reduces near full extension; weapon grips and endpoints retain actual
rig positions. Longer reach never comes from changing bone lengths. The zither
keeps its fixed horizontal placement, and spear hands keep their shaft anchors.

Sword motions include rising cuts, long thrusts, returning cuts, low advancing
slashes, a crossing pair, an aerial cut and three distinct thrust/retract beats.
Blade motions include horizontal sweeps, a short parry/cut, rising cuts, dragging
returns, advancing double cuts, a descending aerial cut and two heavy wave cuts.
The two accepted signatures retain their original pose scores.

`newMartialEffects.ts` stages gathering particles, takeoff wind, weapon-tip
ribbons, hit-only fragments and landing ripples. Feather particles are tapered
leaves with an internal stroke. The blade uses split wave crests and ink flakes,
sampling the actual curved blade tip. Historical pose samples and seeded
arithmetic make pause, seek and replay deterministic. Damage and status effects
continue to come only from actual battle events.
Each authored stroke has a separate trail window. Higher-multiplier moves use a
larger particle budget even when the rolled damage is low; real damage still
controls hit emphasis. Early cosmetic strokes do not invent hit particles or
extra status procs. Preview damage is lower for ordinary moves than signatures.

## Verification

- `python -m unittest test_new_martial_arts test_battle_events test_battle_visuals test_web_battle_events test_action_gauge -q`
- `npm run build`
- `node verify-new-martial.cjs`
- `node verify-curved-figures.cjs`
- `node verify-move-profiles.cjs`
- `node verify-motion-variants.cjs` (the original seventy moves only)
- `python test_battle_visuals.py --fixtures`, then `node verify-motion-pve.cjs`

Browser scripts use the existing `PLAYWRIGHT_MODULE` convention, with the local
frontend on port 5175. PVE verification intercepts every mutation request and
uses recorded engine fixtures, without modifying player records.

All 86 moves are available in the preview selector. Identify the move name and
timeline milliseconds when requesting a pose or effect adjustment.
