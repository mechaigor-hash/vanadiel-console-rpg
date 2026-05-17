# Revision Log

## Revision 22 - SQLite equipment helpers and tests

- Added Python equipment helpers for item data lookup, equipped item listing, derived attack/defense/magic bonuses, equip, and unequip.
- Equipment now moves items between carried inventory and equipped slots with job restriction checks.
- Added tests covering equipment bonus changes, slot movement, unequip restoration, and wrong-job rejection.
- Verified the existing GitHub Actions pytest workflow remains present.

## Revision 22 - GitHub pytest CI

- Added `.github/workflows/test.yml` to run the Python pytest suite on pushes and pull requests to `main`.
- CI installs the package with dev dependencies using Python 3.11, then runs `pytest -q`.
- Updated README and TODO to mark CI complete and refresh the current local test count.

## Revision 21 - Quest prerequisite gating

- Added a follow-up gate-guard quest that stays locked until `first_steps` is complete.
- Added Python quest prerequisite helpers for missing prerequisites, unlock checks, available quest filtering, acceptance, and completion marking.
- Updated the web quest journal and NPC quest cards to separate available vs locked leads and prevent accepting locked quests.
- Added test coverage for locked quest rejection and unlock-after-completion flow.

## Revision 20 - Content schema documentation

- Added `docs/CONTENT_SCHEMA.md` covering every top-level content-pack section: items, maps, NPCs, quests, mobs, loot, recipes, and gathering nodes.
- Documented required/optional fields, known item/stat/data keys, cross-reference expectations, examples, validation rules, and a safe authoring order.
- Linked the schema guide from the README and checked off the content-schema roadmap item in TODO.

## Revision 19 - Content-pack validation

- Added friendly content-pack validation before seeding JSON into SQLite.
- Validation now checks required fields, duplicate slugs, bad map/NPC/item/mob/quest references, and non-positive loot weights.
- Added `ContentValidationError` with a consolidated list of fixable content errors.
- Added pytest coverage for invalid content-pack reference reporting.

## Revision 18 - Web save export/import bridge

- Added Export and Import controls to the web header.
- Added portable JSON save export for character, inventory, equipment, quest state, and quest progress.
- Added JSON import that applies the save, persists it to localStorage, and refreshes the current UI.
- Refactored web save state serialization into reusable `serializableState()` and `applySave()` helpers.

## Revision 17 - Web equipment flow

- Added an Equipment screen to the web sidebar.
- Added equip/unequip actions for inventory gear by slot with basic job restrictions.
- Save/load now persists equipped gear.
- Equipped weapon damage and armor defense now feed into web combat damage mitigation.

## Revision 16 - Web quest journal

- Added a Quest Journal screen to the web sidebar.
- Journal groups active quests, completed quests, and available leads.
- Active quest cards show objective progress, start NPC/location, readiness, and completion action when turn-in is ready.
- Quest completion now refreshes either the NPC screen or journal depending on where it was triggered.

## Revision 15 - Web quest progress and rewards

- Added quest objective progress tracking for defeat and gather objectives in the web client.
- Combat victories now advance matching defeat objectives; gathering and fishing catches advance matching gather objectives.
- NPC quest cards now show progress, unlock completion when ready, and pay gil/item rewards.
- Save/load now persists quest progress alongside accepted/completed quests.

## Revision 14 - Web NPC interaction screen

- Added an NPC screen to the web sidebar and world screen quick action.
- Added local NPC cards with dialogue, quest callouts, objective summaries, and rewards.
- Added quest acceptance tracking in web state/localStorage.
- Indexed NPCs and quests during content-pack loading for interaction lookups.

## Revision 13 - Web sound placeholders and fishing HUD

- Added Web Audio synth sound placeholders for UI confirm/cancel, combat hits, spell casting, fishing tension, and catches.
- Added `web/assets/sounds/README.md` documenting how to swap synth placeholders for future audio files.
- Replaced one-click web fishing with a reel/wait/slacken mini-game using progress, line tension, and patience HUD bars.
- Wired combat, character creation, travel, gathering, and fishing actions to the sound manager.

## Revision 12 - Web placeholder art and combat HUD

- Added SVG placeholder art assets for hero portrait, map/world, combat, and gathering panels.
- Wired placeholder art into the web layout.
- Added combat HUD boxes and HP bars for player/enemy during web combat.
- Updated asset manifest and docs/TODO.

## Revision 11 - Modular web engine scaffold

- Split browser engine scaffolding into modules under `web/src/engine/`:
  - constants
  - content loading/indexing
  - state/save/load
  - utilities
  - asset manager
- Added `AssetManager` scaffold for future image preloading and sound playback.
- Rewired `web/src/engine.js` to import engine modules.
- Updated web docs and TODO.

## Revision 10 - HTML web engine prototype

- Added `web/` browser client with HTML/CSS/JavaScript.
- Added a three-panel game layout: character/sidebar, main stage, event log.
- Added character creation modal using the same race/nation/job stat logic as the Python prototype.
- Added browser localStorage save/load.
- Added web screens for World, Travel, Combat, Gathering, Inventory, and Database summary.
- Web client loads `web/core_content.json`, copied from the Python content pack.
- Added placeholder asset folders for future images and sounds.
- Added web README and root README run instructions.

## Revision 9 - Inventory UI and safer local prompts

- Added Inventory screen grouped by item kind.
- Added Inventory option to the Main Menu.
- Local combat and gathering prompts now support blank-to-cancel.
- Added a test ensuring inventory rows expose item kind for grouped UI.

## Revision 8 - UI orientation pass

- Added Status screen with character identity, jobs, level/EXP, location, stats, and inventory count.
- Added Help screen explaining global navigation, travel, combat, and fishing controls.
- Improved Travel flow by grouping destinations by region before choosing a map.
- Added Help/Status options to the Main Menu.

## Revision 7 - Location-driven menu flow

- Added current-location helpers and legacy location normalization.
- New characters now start in a nation-appropriate city map slug.
- Character header now shows current location.
- Added Travel screen to move between seeded maps.
- Added Current Location details screen showing local NPCs, mobs, and gathering nodes.
- Combat can now choose mobs from the current map.
- Gathering/fishing can now choose nodes from the current map.
- Kept training shortcuts for quick testing.
- Added tests for starting location and travel/location updates.

## Revision 6 - Text-GUI navigation and 75-era/WotG seed slice

- Added reusable `ui.py` text-GUI navigator with screen objects, menu options, breadcrumbs, and back/home/quit commands.
- Reworked the adventure menu into Main / World / Combat / Gathering / Crafting screens.
- Added separate world browser screens for locations, NPCs, mobs, and quests/missions.
- Expanded `core_content.json` toward a 75-era through Wings of the Goddess cutoff:
  - starting city zones and starter fields for San d'Oria, Bastok, and Windurst
  - classic party/progression zones such as Valkurm Dunes, Qufim Island, Garlaige Citadel, Crawler's Nest, Davoi, Beadeaux, Castle Oztroja
  - WotG past-zone seeds such as Southern San d'Oria (S), Bastok Markets (S), Windurst Waters (S), Jugner Forest (S), Pashhow Marshlands (S), Meriphataud Mountains (S)
  - representative story/useful NPCs and representative mob families/jobs/level bands up to level 72 campaign-style enemies
- Added more items/materials/crystals/scrolls and weighted loot tables.
- Added tests that assert expanded era content seeds into SQLite.

## Revision 5 - Interactive combat and fishing

- Replaced instant sample combat in the UI with an interactive turn-based combat screen.
- Added combat actions: attack, cast spell, defend, and flee.
- Added HP/MP tracking during combat, mob counterattacks/casting, EXP payout, and weighted loot payout on victory.
- Added reusable combat helpers plus an automated combat runner for tests.
- Replaced instant fishing menu results with an interactive fishing loop using `reel`, `wait`, and `slacken` tension/progress choices.
- Added reusable fishing state/turn helpers and tests.

## Revision 2 - JSON content pack extraction

- Moved starter content into bundled JSON data pack: `src/vanadiel_console/data/core_content.json`.
- Added `load_content_pack()` so custom content packs can seed the same SQLite systems later.
- Updated README extension notes and checklist.
- Added test coverage for bundled content-pack loading.

## Revision 1 - Foundation prototype

- Created Python package `vanadiel_console`.
- Added SQLite schema and seed data for extensible RPG systems.
- Added character creation with race, sex, nation, main/subjob and stat effects.
- Added inventory/key item/gear persistence tables.
- Added sample maps, NPCs, quests/main mission shape, mobs, weighted loot, crafting, fishing, mining, and gathering.
- Added colour console menu and ASCII art title.
- Added pytest coverage for stat calculation, SQLite persistence, weighted loot setup, gathering/fishing, and crafting.

Known limitations:

- Combat is currently instant sample combat.
- Seed data still lives in Python instead of external content packs.
- Quest progression schema exists, but full journal/progression UI is not implemented yet.
