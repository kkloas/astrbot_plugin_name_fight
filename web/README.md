# QQ account access

Open https://nfight.trpg.fun and send the displayed `/nfweb CODE` command to a QQ
group containing the Name Fight Bot. Return to the original browser to finish
login. Codes expire after five minutes and cannot sign in another browser.
HTTP visits to the public hostname redirect to HTTPS before login. Phones and
computers can sign in the same QQ account simultaneously: verify each browser's
own code. Logging out of one browser leaves the others signed in.
Reloading the login page first recovers verification from the browser cookie.
Pending codes stay available until expiry instead of being replaced on reload.

The Web game uses the same QQ account, fighters, items, points, and PvE progress.
Character replacement and item use on the Web also affect the QQ save. PvE does
not change PvP ratings. Login proves group membership at verification time and
lasts seven days; logging out immediately revokes that browser session.
Existing Bot avatars are read from the shared avatars directory, including
Bot-generated files whose database paths refer to an older installation.
Refresh the save to load updated avatars. Web character cards use the same
resolved avatar. Avatar access checks character ownership.

## Production

The user service `name-fight-web.service` runs the built frontend and FastAPI on
`127.0.0.1:8001`. The existing `trpg` Cloudflare Tunnel routes `nfight.trpg.fun`
to that listener. The required environment settings are:

```text
NFIGHT_DB_PATH=/home/trpg/AstrBot/data/name_fight_data/fighters.db
NFIGHT_PUBLIC_ORIGIN=https://nfight.trpg.fun
NFIGHT_WEB_PORT=8001
```

For local development, set `NFIGHT_PUBLIC_ORIGIN=http://127.0.0.1:8001` to use
development cookies. Production always uses Secure, HttpOnly, SameSite=Strict
cookies. The Bot confirms login by trusted QQ group event fields, not message
text containing an account number. Both processes must have access to the same
database and `.account-locks` directory.

The Web practice tools are restricted to QQ IDs listed in the server environment
variable `NFIGHT_WEB_ADMIN_IDS`, separated by commas. An empty value grants no
administrators. Configure this only in the server environment, not in Git. The
practice endpoints enforce the whitelist and do not update player saves. Route
`/motion-preview.html` through the Web backend if a separate frontend server
normally serves static files, so its access check is applied as well.

The frontend build requires Node.js 20.19.x or 22.12 and later.

```bash
cd web/frontend
npm ci
npm run build
systemctl --user restart name-fight-web.service
systemctl --user status name-fight-web.service
journalctl --user -u name-fight-web.service -n 50
```

`GET /api/health` reports service/database availability. Authentication and game
responses disable caching. Do not log cookies, verification codes, or request
bodies containing credentials.

## Validation and rollback

Run the authentication and storage tests with `web/.venv/bin/python -m unittest
test_web_auth test_shared_accounts test_web_pve test_web_items`. Run
`test_web_browser` after building the frontend with Chromium installed; its
server and player database are disposable. Run `test_web_mobile_layout` for
320-700px phone widths, landscape, long character names, character statistics,
item dialogs with a reduced viewport height, PvE replay and summary, and the
unchanged desktop character layout. Both browser tests use disposable saves.

Phone layouts use portrait-above-statistics character cards, wrapped controls,
and the current page before the information sidebars. Navigation stays visible
in two rows. The narrow layout also covers landscape phones up to 900px wide.
Mobile PvE pages disable shell backdrop blur and animated paper overlays. The
replay HUD has an opaque background, and the HUD and canvas arena contain their
own paints. HP and initiative fills scale without changing their layout width;
recorded values and playback timing remain unchanged. The layout test also
checks rendered fill lengths against replay values and samples the HUD
background across frames at a device scale factor of three.
Set `NFIGHT_TEST_DIST_DIR` to a staged frontend build to validate it before
publishing assets. Device-specific QQ browser flashes still need a real-device
check after deployment.

Before updating, back up the plugin, SQLite database using SQLite's backup API,
avatars, and tunnel config. For rollback, stop the Web service, restore the
previous plugin and tunnel configuration, and restart AstrBot and the tunnel.
Keep the current player database when rolling back code because these updates
add tables without deleting existing player data. Restore the saved database
only when rolling back data intentionally, since that discards later progress.
