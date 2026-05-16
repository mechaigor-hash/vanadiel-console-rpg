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
- [x] Moved starter content out of Python constants into bundled JSON content pack: `src/vanadiel_console/data/core_content.json`.
- [x] Added content-pack loader so future content can be added without editing core Python.
- [x] Added README with run/test instructions and project checklist.
- [x] Added revision log.
- [x] Added automated tests.
- [x] Test gate currently passing: `6 passed`.

## Needs done next

### GitHub / project setup

- [ ] Create GitHub repo as **public**: `mechaigor-hash/vanadiel-console-rpg`.
- [ ] Push local commits to GitHub.
- [ ] Open repo in browser and show Kalidor the link.
- [ ] Keep committing/pushing iterative revisions.

### Gameplay

- [x] Add proper turn-based combat instead of instant sample victories.
- [x] Add HP/MP tracking during combat.
- [x] Add starter spell casting in combat.
- [ ] Add job abilities beyond basic spell casting.
- [ ] Add equipment equip/unequip flow.
- [ ] Add derived attack/defense/magic stats from gear.
- [ ] Add level-up rules and EXP thresholds.
- [ ] Add death/return-home handling.

### Quest / mission systems

- [ ] Add quest journal UI.
- [ ] Add quest accept/active/complete states in gameplay.
- [ ] Add objective progress tracking.
- [ ] Add reward payout logic.
- [ ] Add nation-specific opening missions for Bastok, San d'Oria, and Windurst.
- [ ] Add prerequisites for missions/quests.

### Content authoring

- [ ] Add content-pack validation with friendly errors.
- [ ] Document the JSON schema for items, mobs, maps, quests, NPCs, recipes, and gathering nodes.
- [ ] Split bundled content into separate files by type once it grows.
- [ ] Add more starter-zone mobs and loot tables.
- [ ] Add more fish by water/body type.
- [ ] Add more mining/logging/harvesting nodes.
- [ ] Add shop/vendor data.

### UI / polish

- [ ] Add save-slot/character-management screen.
- [ ] Add better inventory screens grouped by item type.
- [ ] Add map/location travel menu.
- [ ] Add NPC interaction menu.
- [ ] Add help screen explaining commands/systems.
- [ ] Add terminal-width-aware layout.

### Testing / quality

- [ ] Add tests for content-pack validation.
- [ ] Add tests for quest progression.
- [x] Add tests for combat once implemented.
- [x] Add tests for interactive fishing once implemented.
- [ ] Add tests for equipment stat changes.
- [ ] Add CI once GitHub repo exists.
