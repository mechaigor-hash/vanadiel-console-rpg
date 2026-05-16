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
- Character creation with race, sex, starting nation, main job, and optional subjob.
- Starting races: Hume, Elvaan, Tarutaru, Mithra, Galka.
- Starting six jobs: Warrior, Monk, White Mage, Black Mage, Red Mage, Thief.
- Race, nation, main job, and subjob all affect stats.
- SQLite persistence for characters, inventory, key items, gear slots, maps, NPCs, mobs, loot, quests, recipes, and gathering nodes.
- Extensible seed tables for maps, NPCs, mobs, quests/main missions, crafting, fishing, mining, and resource gathering.
- Weighted mob loot tables, including a level 5 White Mage Yagudo sample that can drop WHM-flavoured gear/scrolls.
- Fishing split by water type: freshwater, saltwater, and ice fishing samples.

## Extending content

For now content is seeded in `src/vanadiel_console/db.py`:

- `ITEMS` adds gear, materials, scrolls, fish, etc.
- `MAPS` defines regions, water type, and resource node categories.
- `NPCS` defines location and dialogue.
- `QUESTS` defines side quests and main missions using JSON-like objectives/rewards.
- `MOBS` and `LOOT` define mob stats and weighted drops.
- `RECIPES` defines crafting.
- `GATHERING` defines fishing/mining/resource nodes.

Future revisions should move this data into external JSON/YAML packs so new quests, NPCs, maps, items, mobs, fish, and recipes can be added without editing Python.

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

- [ ] Move seed content into external data packs.
- [ ] Add save-slot selection and better character management.
- [ ] Add equipment equip/unequip and derived combat stats.
- [ ] Add turn-based combat loop rather than instant sample victories.
- [ ] Add quest journal progression and completion rewards.
- [ ] Add nation-specific opening missions.
- [ ] Add more maps, NPCs, mobs, fish, recipes, mining/logging nodes.
- [ ] Add balancing pass for races/jobs/subjobs.
- [ ] Add richer terminal UI screens and help text.
- [ ] Package release builds.

## Discord project note

Created from Kalidor's request in Discord `#general`.
