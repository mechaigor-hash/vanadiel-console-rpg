# Content Pack JSON Schema

The bundled content pack lives at `src/vanadiel_console/data/core_content.json`. The web client mirrors it at `web/core_content.json` when content is copied forward.

This is a pragmatic authoring schema rather than a formal JSON Schema file. The runtime validates required fields, duplicate slugs, and known cross-references before seeding SQLite.

## Top-level shape

```json
{
  "items": [],
  "maps": [],
  "npcs": [],
  "quests": [],
  "mobs": [],
  "loot": [],
  "recipes": [],
  "gathering": []
}
```

All `slug` values should be stable lowercase identifiers using underscores, for example `bronze_sword` or `southern_sandoria`.

## `items`

Required fields:

- `slug` — unique item id.
- `name` — display name.
- `kind` — broad category such as `weapon`, `armor`, `scroll`, `material`, `currency`, or `fish`.

Optional fields:

- `data` — object for item-specific rules.

Known `data` keys:

- `slot` — equipment slot, currently commonly `main` or `body`.
- `jobs` — array of jobs allowed to use the item.
- `damage` — weapon damage bonus.
- `defense` — armor defense bonus.
- `spell` — spell learned/cast by scroll-style items.
- `water` — fish water type such as `fresh`, `salt`, or `ice`.

Example:

```json
{
  "slug": "bronze_sword",
  "name": "Bronze Sword",
  "kind": "weapon",
  "data": {
    "slot": "main",
    "jobs": ["Warrior"],
    "damage": 4
  }
}
```

## `maps`

Required fields:

- `slug` — unique map id.
- `name` — display name.
- `region` — world/region grouping used by travel UI.

Optional fields:

- `water_type` — `fresh`, `salt`, `ice`, or `null`.
- `resource_nodes` — array of broad gathering tags such as `logging`, `mining`, `fishing`, `harvesting`, or `ice_fishing`.

Example:

```json
{
  "slug": "west_ronfaure",
  "name": "West Ronfaure",
  "region": "Ronfaure",
  "water_type": "fresh",
  "resource_nodes": ["logging", "fishing"]
}
```

## `npcs`

Required fields:

- `slug` — unique NPC id.
- `name` — display name.
- `map_slug` — existing `maps.slug` where the NPC appears.

Optional fields:

- `dialogue` — default interaction text.

Example:

```json
{
  "slug": "gate_guard_aile",
  "name": "Ailevia",
  "map_slug": "southern_sandoria",
  "dialogue": "Keep your weapon sharp and your eyes sharper."
}
```

## `quests`

Required fields:

- `slug` — unique quest/mission id.
- `title` — display title.

Optional fields:

- `quest_type` — `main`, `mission`, `side`, or another grouping string. Defaults to `side` in SQLite.
- `start_npc_slug` — existing `npcs.slug` where the quest starts.
- `prerequisites` — array of quest slugs that must already be completed. The current validator checks that referenced quest slugs exist; gameplay unlock enforcement is next on the roadmap.
- `objectives` — array of objective objects.
- `rewards` — reward object.

Known objective forms:

```json
{ "type": "defeat", "mob_family": "Yagudo", "count": 1 }
{ "type": "gather", "item": "copper_ore", "count": 2 }
```

Known reward keys:

- `gil` — integer gil amount.
- `items` — object mapping `items.slug` to quantity.

Example:

```json
{
  "slug": "first_steps",
  "title": "First Steps Outside the Gate",
  "quest_type": "main",
  "start_npc_slug": "gate_guard_aile",
  "prerequisites": [],
  "objectives": [
    { "type": "defeat", "mob_family": "Yagudo", "count": 1 }
  ],
  "rewards": {
    "gil": 100,
    "items": { "beastcoin": 1 }
  }
}
```

## `mobs`

Required fields:

- `slug` — unique mob id.
- `name` — display name.
- `family` — mob family used by quest objectives and grouping.
- `level` — integer level.

Optional fields:

- `job` — mob job, such as `Warrior`, `White Mage`, or `Thief`.
- `map_slug` — existing `maps.slug` where this mob can appear.
- `stats` — object for combat stats.

Known `stats` keys:

- `hp`
- `mp`
- future-safe numeric stats such as `attack`, `defense`, or spell tuning values.

Example:

```json
{
  "slug": "yagudo_acolyte_l5",
  "name": "Yagudo Acolyte",
  "family": "Yagudo",
  "job": "White Mage",
  "level": 5,
  "map_slug": "west_sarutabaruta",
  "stats": { "hp": 42, "mp": 28 }
}
```

## `loot`

Required fields:

- `mob_slug` — existing `mobs.slug`.
- `item_slug` — existing `items.slug`.
- `weight` — positive integer relative drop weight.

Optional fields:

- `min_qty` — minimum quantity, defaults to `1`.
- `max_qty` — maximum quantity, defaults to `1`.

Example:

```json
{
  "mob_slug": "yagudo_acolyte_l5",
  "item_slug": "yagudo_feather",
  "weight": 50,
  "min_qty": 1,
  "max_qty": 2
}
```

## `recipes`

Required fields:

- `slug` — unique recipe id.
- `craft` — craft name, such as `Smithing`.
- `result_item_slug` — existing `items.slug` produced by the recipe.

Optional fields:

- `skill_required` — integer craft skill threshold, defaults to `0`.
- `ingredients` — object mapping `items.slug` to quantity.

Example:

```json
{
  "slug": "bronze_ingot_smithing",
  "craft": "Smithing",
  "result_item_slug": "bronze_ingot",
  "skill_required": 0,
  "ingredients": { "copper_ore": 3 }
}
```

## `gathering`

Required fields:

- `slug` — unique gathering node id.
- `map_slug` — existing `maps.slug`.
- `kind` — node type such as `mining`, `logging`, `fishing`, `harvesting`, or `ice_fishing`.

Optional fields:

- `loot_table` — array of weighted item entries.

Loot table entry fields:

- `item` — existing `items.slug`.
- `weight` — positive integer relative weight.
- `min_qty` — optional minimum quantity.
- `max_qty` — optional maximum quantity.

Example:

```json
{
  "slug": "bastok_mines_copper_vein",
  "map_slug": "bastok_mines",
  "kind": "mining",
  "loot_table": [
    { "item": "copper_ore", "weight": 80, "min_qty": 1, "max_qty": 3 }
  ]
}
```

## Current validation rules

`validate_content_pack()` currently checks:

- required fields for all major sections;
- duplicate slugs within each section;
- NPC, mob, and gathering `map_slug` references;
- quest `start_npc_slug`, prerequisite, gather-objective item, and reward item references;
- loot mob/item references and positive weights;
- recipe result/ingredient item references;
- gathering loot item references and positive weights.

Run validation through the test suite:

```bash
source .venv/bin/activate
pytest -q
```

## Authoring checklist

Before adding a large content slice:

- Add maps first.
- Add items before loot, recipes, gathering, and quest rewards that reference them.
- Add NPCs before quests that start from them.
- Add mobs before mob loot tables.
- Keep slugs stable; changing a slug is a save-breaking content migration.
- Add or update tests when introducing new objective/reward mechanics.
