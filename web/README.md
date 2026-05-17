# Web Engine Prototype

This folder is the first HTML/CSS/JavaScript version of the game engine.

## Run locally

From the repo root:

```bash
python3 -m http.server 8000 -d web
```

Then open:

```text
http://localhost:8000
```

Do not open `index.html` directly from the file browser; the browser blocks `fetch()` for local JSON files in many cases.

## Current web features

- HTML/CSS layout with three panels: character/sidebar, main stage, event log.
- Character creation modal.
- Browser localStorage save/load for character, inventory, and accepted quests.
- Loads `core_content.json` generated from the Python content pack.
- World screen showing local NPCs, mobs, and gathering nodes.
- NPC interaction screen with dialogue, quest summaries, and quest acceptance tracking.
- Region/map travel screen.
- Clickable local combat prototype.
- Clickable local gathering prototype plus fishing mini-game with reel/wait/slacken choices.
- Inventory screen grouped by item kind.
- Database summary screen.
- Modular engine scaffolding:
  - `engine/constants.js` - race/job/nation/stat constants
  - `engine/content.js` - content-pack loader/indexer
  - `engine/state.js` - game state and save/load helpers
  - `engine/utils.js` - dice, weighted tables, cards, stat helpers
  - `engine/assets.js` - image/sound asset manager scaffold
- Placeholder folders for future images and sounds:
  - `assets/images/`
  - `assets/sounds/`
- SVG placeholder art for hero portrait, map/world, combat, and gathering panels.
- Web Audio synth placeholder sounds for UI confirm/cancel, combat hits, spell casting, fishing tension, and catches.

## Engine direction

Keep the Python/SQLite version as the data/prototype backend for now. The web client should grow into the main presentation/gameplay layer with:

- asset loading
- richer file-backed sound packs to replace the current synth placeholders
- scene/screen router
- entity/component-ish data objects
- combat system module
- inventory/equipment module
- content pack loader/validator
- eventual backend sync/export if needed
