# Vanadiel Console RPG

Single-player Python console RPG prototype inspired by classic Final Fantasy XI-style systems. This is **not** a full recreation or asset dump; it is an extensible original codebase for a text RPG with familiar MMO-shaped mechanics.

## Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
vanadiel
```

Or without installing:

```bash
PYTHONPATH=src python3 -m vanadiel_console.app
```

The game creates `vanadiel.sqlite3` in the current directory unless `VANADIEL_DB=/path/file.sqlite3` is set.

## Test

```bash
pip install -e '.[dev]'
pytest
```

## Current features

- Colour console UI and ASCII title screen.
- Text-GUI screen navigator with Main / World / Travel / Combat / Gathering / Crafting menus, plus back/home/quit controls.
- Status and Help screens for quick orientation.
- Inventory screen grouped by item kind.
- Region-grouped travel picker so the map list is less painful to navigate.
- Character creation with race, sex, starting nation, main job, and optional subjob.
- Starting races: Hume, Elvaan, Tarutaru, Mithra, Galka.
- Starting six jobs: Warrior, Monk, White Mage, Black Mage, Red Mage, Thief.
- Race, nation, main job, and subjob all affect stats.
- SQLite persistence for characters, inventory, key items, gear slots, maps, NPCs, mobs, loot, quests, recipes, and gathering nodes.
- Extensible seed tables for maps, NPCs, mobs, quests/main missions, crafting, fishing, mining, and resource gathering.
- Expanded 75-era-through-Wings-of-the-Goddess seed slice: starter cities/fields, classic party zones, WotG past zones, representative NPCs, and 30+ representative mobs up to level 72 campaign-style enemies.
- Weighted mob loot tables, including a level 5 White Mage Yagudo sample that can drop WHM-flavoured gear/scrolls.
- Interactive turn-based combat with attack, cast, defend, flee, EXP, and loot payout.
- Location-driven combat: local encounters are listed from the character's current map.
- Interactive fishing with reel/wait/slacken tension management.
- Location-driven gathering/fishing: local nodes are listed from the character's current map.
- Fishing split by water type: freshwater, saltwater, and ice fishing samples.

## Extending content

Bundled starter content now lives in `src/vanadiel_console/data/core_content.json`:

- `items` adds gear, materials, scrolls, fish, etc.
- `maps` defines regions, water type, and resource node categories.
- `npcs` defines location and dialogue.
- `quests` defines side quests and main missions using objective/reward objects.
- `mobs` and `loot` define mob stats and weighted drops.
- `recipes` defines crafting.
- `gathering` defines fishing/mining/resource nodes.

The Python seeder can also load another JSON file with the same top-level keys, so future private/mod content can be added without editing code.

## Repository

Planned GitHub visibility: **public**.

GitHub: <https://github.com/mechaigor-hash/vanadiel-console-rpg>

Project checklist is also tracked in [`TODO.md`](TODO.md).

## Checklist

### Revision 1 foundation

- [x] Create new Python project/repo.
- [x] Add SQLite schema covering characters, inventory, key items, gear slots, maps, NPCs, mobs, loot, quests, missions, recipes, and gathering.
- [x] Add character creation choices for race, sex, nation, main job, and subjob.
- [x] Add stat calculation affected by race/nation/job/subjob.
- [x] Seed starting races and six starting jobs.
- [x] Seed starting gear per job.
- [x] Add colour/ASCII console menu.
- [x] Add sample NPCs, maps, quests, and main mission structure.
- [x] Add crafting, mining, and fishing/resource gathering systems.
- [x] Add freshwater/saltwater/ice fishing examples.
- [x] Add weighted loot for mobs, including Lv5 WHM Yagudo sample.
- [x] Add automated tests for core systems.

### Next revisions

- [x] Move seed content into external data packs.
- [x] Add public project TODO/checklist artifact.
- [x] Create public GitHub repository and push commits.
- [ ] Add content-pack validation with friendly error messages.
- [ ] Add save-slot selection and better character management.
- [ ] Add equipment equip/unequip and derived combat stats.
- [x] Add turn-based combat loop rather than instant sample victories.
- [x] Add interactive fishing tension loop.
- [ ] Add quest journal progression and completion rewards.
- [ ] Add nation-specific opening missions.
- [x] Add first expanded 75-era/WotG seed slice for maps, NPCs, mobs, and loot.
- [ ] Continue fleshing out maps, NPCs, mobs, fish, recipes, mining/logging nodes.
- [ ] Add balancing pass for races/jobs/subjobs.
- [x] Add richer terminal UI screens and simple movement between menus.
- [x] Add travel menu and current-location display.
- [x] Make combat/gathering menus use current-location mobs/nodes.
- [x] Add inventory browser grouped by item type.
- [ ] Add help text and terminal-width-aware layout.
- [ ] Package release builds.

## Discord project note

Created from Kalidor's request in Discord `#general`.
