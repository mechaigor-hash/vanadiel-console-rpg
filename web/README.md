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
- Browser localStorage save/load.
- Loads `core_content.json` generated from the Python content pack.
- World screen showing local NPCs, mobs, and gathering nodes.
- Region/map travel screen.
- Clickable local combat prototype.
- Clickable local gathering/fishing prototype.
- Inventory screen grouped by item kind.
- Database summary screen.
- Placeholder folders for future images and sounds:
  - `assets/images/`
  - `assets/sounds/`

## Engine direction

Keep the Python/SQLite version as the data/prototype backend for now. The web client should grow into the main presentation/gameplay layer with:

- asset loading
- sound manager
- scene/screen router
- entity/component-ish data objects
- combat system module
- inventory/equipment module
- content pack loader/validator
- eventual backend sync/export if needed
