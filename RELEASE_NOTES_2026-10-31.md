# Web Practice and Battle Effects Update

This update adds an administrator-only Web practice hall, independent fighter
attributes and loadout selection, and a skill-effects preview with stage and
loop controls. It also updates the two master-arts figures, the Biyun and
Chixiao internal-skill effects, and the White Python Whip recovery animation.

Set `NFIGHT_WEB_ADMIN_IDS` to a comma-separated list of administrator QQ IDs
in the Web server environment. An empty list grants no administrator access.
If a separate web server serves frontend files, route `/motion-preview.html`
through the Web backend to enforce its access check. No database migration or
Bot configuration change is required. Local test data and launchers are not
included in this update.

Verification includes a clean `npm ci` and frontend build, isolated Web, game,
and Bot test suites, browser login and battle testing, and animation checks.
The Windows avatar symlink test was skipped because the account lacks symlink
creation privileges. The existing npm lockfile audit reports 8 vulnerabilities
(1 low, 2 moderate, 5 high); dependencies were not upgraded in this update.

Deployment and rollback follow `UPDATE_POLICY.md` and `SERVER_UPDATE.md`.
Keep the previous code and frontend build available for rollback, and back up
the actual server database, avatars, and configuration before deployment.
