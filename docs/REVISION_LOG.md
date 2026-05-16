# Revision Log

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
