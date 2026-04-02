# Changelog

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
