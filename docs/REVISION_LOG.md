# Revision Log

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
