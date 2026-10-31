# Shared world boss artwork

`manifest.json` is the versioned source of asset names for both the Web dossier and Bot cards. Keep these assets in the release; do not store them only in a machine-local data directory.

- `dragon-chief-guardian-v1.png`: phase-one sword guardian, transparent RGBA.
- `dragon-chief-sovereign-v1.png`: phase-two dragon sovereign, transparent RGBA.
- `../battle/bossVisuals.js`: deterministic Canvas armor, gate/mountain backdrop, dragon seal, arrival, sword and healing effects. Combat animation does not download or rasterize the portraits per frame.

Names, stats, HP and skill descriptions are drawn from the encounter payload, never embedded into these portraits. The built-in image generation tool produced the artwork; no external API credential or CLI fallback was used.

Generation prompts:

1. Use case: stylized-concept. Project game asset: full-body transparent character illustration for a Chinese wuxia ink-painting browser game. Phase one of the world boss 'Dragon Chief', a human mountain-gate sword guardian. Single solitary adult male warrior, restrained upright guarding stance, long straight Chinese jian pointed diagonally down, weathered black-bronze lamellar armor with subtle dragon engraving, dark cloth layered robe, tied long dark hair, muted antique gold edges, sharp readable silhouette, painterly ink outlines with restrained realistic texture, front three-quarter view looking slightly left. Full figure including feet and sword, centered with generous transparent margin, no cropped limbs. Match a dark antique bronze dragon-themed boss card but make this an independent figure suitable over pale rice-paper backgrounds. Actual transparent alpha background. No letters, numbers, text, panels, card frames, drop shadow, scenery or second character.
2. Use case: stylized-concept. Project game asset: full-body transparent character illustration for a Chinese wuxia ink-painting browser game. Phase two true form of the world boss 'Dragon Chief'. Single imposing humanoid dragon sovereign swordmaster, dark antique bronze armor, sculptural dragon-headed helmet with branching swept horns and small jade glowing eyes, layered charcoal-black robe, broad heavy Chinese straight sword held low, calm grounded stance, front three-quarter view looking slightly left. Strong readable silhouette, painterly Chinese ink outlines and detailed but restrained bronze texture, gold and jade accents, heavier and more regal than a human gate guardian. Full figure including feet, horns and blade centered with generous transparent margins. Independent collectible-quality figure usable over pale rice-paper backgrounds. Actual transparent alpha background. No lettering, numbers, text, stat panels, frames, scenery, ground shadow or second character.
