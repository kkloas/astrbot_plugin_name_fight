# Shared Web and AstrBot animation

## Release baseline

Rules and the three loadout catalogs are based on main commit 2229cda.
There are 18 martial arts (126 moves), 12 internal arts and 9 lightness arts.
The existing Web roster, growth, inventory and PVE remain available.
No loadout numbers or PVE stage numbers were retuned in this integration.
The user accepted the changed fixed-seed PVE results; test_pve.py records that
snapshot instead of the superseded pre-sync difficulty targets.

## One renderer

The source of truth is web_animation/battle/*.js. Both the Bot GIF capture page
and the React InkStage wrapper import these exact modules. The former Web
animation .ts modules are typed re-exports, not a second implementation.
Do not put new choreography into the wrappers. Public .d.ts files describe
the shared runtime for the Web TypeScript compiler.

New move scores, fixed-length limb poses and effect emission live in
web_animation/battle/expandedArts.js. Weapon geometry lives in inkWeapons.js.
The five added schools each have eight explicit move entries. Their actions
always select their authored implementation, including in mixed mode.
Existing schools retain their legacy/current variation.

Effects sample absolute replay time and the weapon pose. Do not use wall-clock
time or Math.random in drawing. Multiple visual strokes must not create extra
damage events. Misses may show trails, but must not show a landed-impact burst.
New internal and lightness effects are triggered by recorded engine events.

The engine keeps the main event format. Two Web-compatible extensions remain:
optional current_hp for PVE relay fights and deterministic victory variation.
Neither changes ordinary full-health Bot damage rules or consumes combat RNG.

## Verification

- python -m unittest discover -p "test_*.py"
- node test_battle_effects.mjs
- cd web/frontend and npm run build
- node verify-shared-runtime.cjs (running Vite; defaults to port 5173)
- python verify_bot_gif.py (real Chrome, Pillow and websockets required)

Browser checks cover all 126 moves, both sides and hit/miss cases. Set
PLAYWRIGHT_MODULE when Playwright is installed outside the frontend directory.
Set NAME_FIGHT_WEB_URL to test a different local port.
GIF output and screenshots go to output/, not player data directories.

## Linux Bot deployment

The checked-in web_animation directory is directly executable by Chrome.
Bot hosts do not need Node, Vite, React or a frontend build.
Install requirements.txt in the existing AstrBot Python virtual environment.
The working Linux Chrome lookup is retained; NAME_FIGHT_CHROME can override
the executable, and chromium/chromium-browser are supported fallbacks.

Before deployment, back up the existing plugin data directory and database.
Inspect git status and preserve local changes before updating.
The deployed checkout is currently codex/1.3, so git pull alone will not switch
it to main. After the release has been pushed, explicitly switch the deployment
checkout to main, set its upstream to origin/main, and pull with --ff-only.
Restart the actual systemd service only after dependencies are installed.
Do not guess its service name or replace the Python virtual environment.

No server deployment or message sending is performed by the local tests.
Run one Bot fight after restart and check its GIF generation/send logs.
