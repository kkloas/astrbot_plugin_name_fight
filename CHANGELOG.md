# 1.4.2 - 2026-10-13 - AstrBot review fixes

- Use the logger imported from astrbot.api in the GIF renderer.
- Store persistent data in data/plugin_data/astrbot_plugin_name_fight.
- Migrate legacy saves with SQLite backup, including committed WAL data.
- Copy referenced legacy avatars and update their paths before publishing the database.
- Preserve existing destination saves and original source files; clean failed migration output.
- Serialize first-start migration and skip automatic migration for explicit database paths.
- Document the new storage path and require stopping old instances before upgrade.

# 1.4.1 - 2026-10-12 - Plugin release hardening

- Publish the AstrBot plugin separately from the Web application.
- Use version 1.4.1 after the existing v1.4.0 tag and document branch purposes.
- Require trusted administrators for boss and leaderboard management.
- Settle yesterday and the previous ISO week in Asia/Shanghai only.
- Commit settlement rewards, items and records atomically.
- Isolate active battles by group and cancel owned tasks on unload.
- Bound GIF workers and timeouts, retaining slots until workers finish.
- Validate bounded avatar downloads and trusted local cache paths asynchronously.
- Add plugin settings and retain the existing player database location.
- Keep generated media outside the plugin directory and clean delivered files.
- Replace bundled fonts with Noto Sans SC under the SIL Open Font License.
- Exclude Web assets, temporary media and development artifacts from distribution.

# Changelog

## 1.4.0 - 2026-04-14

### Added

- Added a group-scoped two-phase world boss activity with open, fight, rank, close, and settle commands
- Added shared phase-2 HP tracking, contribution ranking, daily attempt limits, and kill settlement rewards
- Added world boss message templates and repository tests covering activity lifecycle and settlement

### Fixed

- Fixed user-facing world boss text and metadata output to avoid mojibake in the released package

## 1.2.1 - 2026-04-02

### Changed

- Tagged the current pre-item-system codebase as the 1.2.1 GitHub backup baseline

## 1.2.0 - 2026-04-01

### Added

- Added deterministic fighter generation based on name hashing
- Added peak ranking titles and top-3 special display
- Added post-battle peak score change broadcast
- Added clearer `/fhelp` command descriptions
- Added `metadata.yaml`, `.gitignore`, and repository format guidance
- Added `BALANCE_MODEL.md` to document the combat model, attribute weighting, and martial-art balance evaluation

### Changed

- Switched ranking logic to an aggressive competitive peak-score model
- Updated leaderboard presentation to focus on peak score and honor titles
- Simplified fighter profile descriptions while keeping wuxia flavor and gameplay meaning
- Reworked README for GitHub-ready project presentation
- Highlighted triggered combat states inline with short target-tagged state markers instead of long explanatory sentences

### Fixed

- Fixed `/fc` owner lookup to use the correct repository method
- Fixed `/use` active fighter switching return handling
- Fixed profile ownership checks by adding repository ownership lookup
- Cleaned public-facing text that had been affected by encoding issues
- Fixed battle log compression so outcome lines are less likely to be merged into the final action line
- Added a conservative retry-and-drop fallback for occasional battle log send timeouts
- Corrected state marker encoding to avoid mojibake in combat output
