# Server update guide: Web and AstrBot

This guide covers the `dev-web` branch and the Web and AstrBot components in this repository. It does not assume a particular server path, service name, reverse proxy, or Python environment.

## What this update contains

- Xuanmo sword and Chixiao blade arts, their associated internal arts and lightness skills, the Web showcase and motion preview.
- Shared animation changes and Web-only enhanced ink assets and effects, including the Baimang whip. The Bot GIF renderer uses the shared animation modules, while Web-only effects require the Web enhanced renderer.
- Related battle configuration and tests. The `dev-web` branch also contains the earlier Web and PVE update already present in commit `2472de4`.
- The generated animation images are source assets under `web_animation/battle/assets/`. The built frontend under `web/frontend/dist/` is generated on the server and is not tracked by Git.

## 1. Identify the running installation and back up data

1. Find the actual repository directory, the AstrBot plugin installation, the Web backend and frontend deployment, and the Python environments and service names used by this server. If Web and the plugin use different checkouts, update and verify each checkout separately.
2. Back up the database, avatars, configuration and other server-specific data before changing versions. Use an SQLite-consistent backup or stop every process that writes to the database before copying it. Keep the backup outside the Git checkout.
3. The default database is `name_fight_data/fighters.db` beside the repository. When the repository is directly under an AstrBot `plugins` directory, the default data directory is beside that `plugins` directory instead. Confirm the actual database path and any custom configuration on the server before backing up.
4. Record the current revision and branch in every checkout:

```sh
git status --short --branch
git rev-parse HEAD
git remote -v
```

If there are local changes, untracked files that may conflict, an unexpected remote, or an unknown deployment layout, preserve them and resolve the situation before switching branches or pulling. Do not use `git reset --hard` or `git clean` as a routine update step.

## 2. Compare with GitHub and update the checkout

From the actual repository directory:

```sh
git fetch origin
git log --oneline --left-right HEAD...origin/dev-web
git diff --stat HEAD origin/dev-web
git status --short --branch
```

Review the changes first. If the server has a local `dev-web` branch, switch to it only after confirming that the working tree is safe to switch:

```sh
git switch dev-web
git pull --ff-only origin dev-web
git rev-parse HEAD
```

If there is no local `dev-web` branch, and `origin/dev-web` exists after fetching, create a tracking branch with `git switch --track origin/dev-web`, then run the `git pull --ff-only` and revision check above. If switching or fast-forwarding fails, stop and inspect the local changes and branch history rather than forcing the update. Repeat the comparison for any separate Web or plugin checkout.

## 3. Update the Web deployment

- Use the existing backend Python environment and install dependencies from `web/backend/requirements.txt` when required. The supplied backend launcher also checks `web/.python-packages` before installed packages, so confirm which environment the running service actually uses.
- Build the frontend using Node and npm in the Web checkout:

```sh
cd web/frontend
npm ci
npm run build
```

- Publish `web/frontend/dist/` using the existing frontend deployment method. Restart the actual Web backend and frontend services as required by that deployment. Do not guess service names. Production routing must continue to send `/api` requests to the backend.
- Open the Web application and `/motion-preview.html`. Verify the new arts and the Baimang whip with Web enhanced effects enabled. Browser refresh or cache invalidation may be needed after deploying new frontend assets.

## 4. Update the AstrBot plugin

- Confirm that the plugin checkout was updated in step 2 and that its actual AstrBot Python environment has the dependencies in the repository root `requirements.txt`. Keep the existing environment and server-specific configuration.
- The Bot GIF renderer loads `web_animation` from the plugin checkout and requires a compatible Chrome or Chromium installation. `NAME_FIGHT_CHROME` may specify the browser executable when needed.
- Restart the actual AstrBot service using the server's existing procedure, then run one non-destructive test battle and check the GIF and service logs. Web-enhanced-only visuals are not a promise that the Bot GIF looks identical.

## 5. Verify and roll back if necessary

- Confirm the revision in each checkout with `git rev-parse HEAD`, check the Web backend and frontend, test one Web battle and one Bot battle, and inspect service logs.
- If an update or verification fails, stop and retain the database backup and the recorded prior revisions. Restore the prior version using the server's established rollback procedure; restore a database only when necessary and only after stopping its writers. A forced checkout or reset can discard local work, so inspect the server state before choosing a rollback command.
