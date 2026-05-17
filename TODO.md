# Vanadiel Console RPG - TODO / Checklist

## Done so far

- [x] Created new local project/repo: `vanadiel-console-rpg`.
- [x] Added Python package structure under `src/vanadiel_console`.
- [x] Added console/text GUI with colour and ASCII title art.
- [x] Added character creation flow.
- [x] Added selectable race, sex, starting nation, main job, and optional subjob.
- [x] Added starting races: Hume, Elvaan, Tarutaru, Mithra, Galka.
- [x] Added starting six jobs: Warrior, Monk, White Mage, Black Mage, Red Mage, Thief.
- [x] Race, nation, main job, and subjob affect stats.
- [x] Added SQLite schema and seeding.
- [x] Persisted characters, inventory, gear slot field, key items, maps, NPCs, mobs, weighted loot, quests, missions, recipes, and gathering nodes.
- [x] Added starting gear per job.
- [x] Added sample maps, NPCs, quests, and main mission structure.
- [x] Added weighted mob loot system.
- [x] Added Lv5 White Mage Yagudo sample with WHM-flavoured loot table: staff, Cure scroll, feather, beastcoins.
- [x] Added crafting foundation.
- [x] Added mining/resource gathering foundation.
- [x] Added fishing foundation with freshwater, saltwater, and ice-fishing examples.
- [x] Added interactive turn-based combat with attack/cast/defend/flee choices.
- [x] Added interactive fishing with reel/wait/slacken tension management.
- [x] Added reusable text-GUI screen navigator with back/home/quit controls.
- [x] Split gameplay into Main / World / Combat / Gathering / Crafting screens.
- [x] Added Travel menu and current-location display in the character header.
- [x] Made combat and gathering menus location-driven using the character's current map.
- [x] Added Status and Help screens.
- [x] Improved Travel menu by grouping destinations by region.
- [x] Added grouped Inventory screen.
- [x] Added first HTML/CSS/JavaScript web engine prototype.
- [x] Added browser UI panels, character creation modal, event log, travel/combat/gathering/inventory/database screens.
- [x] Added placeholder asset folders for future images and sounds.
- [x] Split browser engine scaffolding into constants/content/state/utils/assets modules.
- [x] Added SVG placeholder art for hero, map/world, combat, and gathering panels.
- [x] Added combat HUD bars in the web UI.
- [x] Added Web Audio synth placeholders for UI/combat/spell/fishing feedback.
- [x] Added web fishing HUD mini-game with reel/wait/slacken tension management.
- [x] Added web NPC interaction screen with dialogue and quest acceptance.
- [x] Added web quest objective progress tracking and reward payout.
- [x] Added web quest journal with active/completed/available quest groups.
- [x] Added web equipment equip/unequip screen and combat stat bonuses.
- [x] Added SQLite equipment helpers and stat-change tests.
- [x] Hardened GitHub CI with Python 3.11/3.12/3.13 matrix and compile step.
- [x] Added level-up EXP thresholds and stat refresh.
- [x] Added web portable JSON save export/import bridge.
- [x] Added content-pack validation with friendly cross-reference errors.
- [x] Expanded first 75-era/WotG content seed slice: 40+ maps, 15+ NPCs, 30+ mobs, and additional loot tables.
- [x] Moved starter content out of Python constants into bundled JSON content pack: `src/vanadiel_console/data/core_content.json`.
- [x] Added content-pack loader so future content can be added without editing core Python.
- [x] Added README with run/test instructions and project checklist.
- [x] Added revision log.
- [x] Added automated tests.
- [x] Test gate currently passing: `13 passed`.

## Needs done next

### GitHub / project setup

- [x] Create GitHub repo as **public**: `mechaigor-hash/vanadiel-console-rpg`.
- [x] Push local commits to GitHub.
- [x] Open repo in browser and show Kalidor the link.
- [ ] Keep committing/pushing iterative revisions.

### Gameplay

- [x] Add proper turn-based combat instead of instant sample victories.
- [x] Add HP/MP tracking during combat.
- [x] Add starter spell casting in combat.
- [ ] Add job abilities beyond basic spell casting.
- [x] Add equipment equip/unequip flow.
- [x] Add derived attack/defense/magic stats from gear.
- [x] Add level-up rules and EXP thresholds.
- [ ] Add death/return-home handling.

### Quest / mission systems

- [x] Add quest journal UI.
- [x] Add quest accept/active/complete states in gameplay.
- [x] Add objective progress tracking.
- [x] Add reward payout logic.
- [ ] Add nation-specific opening missions for Bastok, San d'Oria, and Windurst.
- [x] Add prerequisites for missions/quests.

### Content authoring

- [x] Add content-pack validation with friendly errors.
- [x] Document the JSON schema for items, mobs, maps, quests, NPCs, recipes, and gathering nodes.
- [ ] Split bundled content into separate files by type once it grows.
- [x] Add first pass of starter-zone mobs and loot tables.
- [ ] Add deeper starter-zone mob coverage from wiki pages.
- [ ] Add more fish by water/body type.
- [ ] Add more mining/logging/harvesting nodes.
- [ ] Add shop/vendor data.

### UI / polish

- [x] Add first HTML/CSS web UI prototype.
- [ ] Add save-slot/character-management screen.
- [x] Add better inventory screens grouped by item type.
- [x] Add basic map/location browser menu.
- [x] Add map/location travel menu.
- [x] Add NPC interaction menu.
- [x] Add help screen explaining commands/systems.
- [ ] Add terminal-width-aware layout.

### Web engine

- [x] Create `web/` client with HTML/CSS/JS.
- [x] Load JSON content pack in browser.
- [x] Add localStorage save/load.
- [x] Add visual layout and screen routing.
- [x] Split web engine into modules.
- [x] Add image/sound asset manager scaffold.
- [x] Add sprite/map placeholder image assets.
- [x] Add sample UI/combat/fishing sounds.
- [x] Sync web client with SQLite/backend or add export/import bridge.

### Testing / quality

- [x] Add tests for content-pack validation.
- [x] Add tests for quest progression.
- [x] Add tests for combat once implemented.
- [x] Add tests for interactive fishing once implemented.
- [x] Add tests for equipment stat changes.
- [x] Add CI once GitHub repo exists.
