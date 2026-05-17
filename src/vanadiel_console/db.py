from __future__ import annotations

import json
import sqlite3
from importlib.resources import files
from pathlib import Path

from .models import CharacterBuild, STARTING_GEAR, calculate_stats

SCHEMA_VERSION = 1


class ContentValidationError(ValueError):
    """Raised when a JSON content pack has missing fields or bad references."""


def _require_fields(section: str, row: dict, fields: tuple[str, ...], errors: list[str]) -> None:
    missing = [field for field in fields if field not in row or row[field] in (None, "")]
    if missing:
        errors.append(f"{section}:{row.get('slug', '<missing slug>')} missing required field(s): {', '.join(missing)}")


def _slug_set(content: dict, section: str) -> set[str]:
    return {row.get("slug") for row in content.get(section, []) if row.get("slug")}


def validate_content_pack(content: dict) -> None:
    """Validate required fields and cross-references for a content pack.

    The checks intentionally stay lightweight/friendly so modders get a concise
    list of fixable problems before SQLite foreign-key failures or KeyErrors.
    """
    errors: list[str] = []
    required = {
        "items": ("slug", "name", "kind"),
        "maps": ("slug", "name", "region"),
        "npcs": ("slug", "name", "map_slug"),
        "quests": ("slug", "title"),
        "mobs": ("slug", "name", "family", "level"),
        "recipes": ("slug", "craft", "result_item_slug"),
        "gathering": ("slug", "map_slug", "kind"),
    }
    for section, fields in required.items():
        seen: set[str] = set()
        for row in content.get(section, []):
            _require_fields(section, row, fields, errors)
            slug = row.get("slug")
            if slug in seen:
                errors.append(f"{section}:{slug} duplicate slug")
            if slug:
                seen.add(slug)

    item_slugs = _slug_set(content, "items")
    map_slugs = _slug_set(content, "maps")
    npc_slugs = _slug_set(content, "npcs")
    mob_slugs = _slug_set(content, "mobs")
    quest_slugs = _slug_set(content, "quests")

    for npc in content.get("npcs", []):
        if npc.get("map_slug") and npc["map_slug"] not in map_slugs:
            errors.append(f"npcs:{npc.get('slug')} references unknown map_slug {npc['map_slug']}")
    for mob in content.get("mobs", []):
        if mob.get("map_slug") and mob["map_slug"] not in map_slugs:
            errors.append(f"mobs:{mob.get('slug')} references unknown map_slug {mob['map_slug']}")
    for quest in content.get("quests", []):
        if quest.get("start_npc_slug") and quest["start_npc_slug"] not in npc_slugs:
            errors.append(f"quests:{quest.get('slug')} references unknown start_npc_slug {quest['start_npc_slug']}")
        for prerequisite in quest.get("prerequisites", []):
            if prerequisite not in quest_slugs:
                errors.append(f"quests:{quest.get('slug')} references unknown prerequisite {prerequisite}")
        for objective in quest.get("objectives", []):
            if objective.get("type") == "gather" and objective.get("item") not in item_slugs:
                errors.append(f"quests:{quest.get('slug')} gather objective references unknown item {objective.get('item')}")
        for item_slug in quest.get("rewards", {}).get("items", {}):
            if item_slug not in item_slugs:
                errors.append(f"quests:{quest.get('slug')} reward references unknown item {item_slug}")
    for loot in content.get("loot", []):
        if loot.get("mob_slug") not in mob_slugs:
            errors.append(f"loot:{loot.get('mob_slug', '<missing mob>')} references unknown mob_slug {loot.get('mob_slug')}")
        if loot.get("item_slug") not in item_slugs:
            errors.append(f"loot:{loot.get('mob_slug', '<missing mob>')} references unknown item_slug {loot.get('item_slug')}")
        if loot.get("weight", 0) <= 0:
            errors.append(f"loot:{loot.get('mob_slug', '<missing mob>')} weight must be positive")
    for recipe in content.get("recipes", []):
        if recipe.get("result_item_slug") and recipe["result_item_slug"] not in item_slugs:
            errors.append(f"recipes:{recipe.get('slug')} references unknown result_item_slug {recipe['result_item_slug']}")
        for item_slug in recipe.get("ingredients", {}):
            if item_slug not in item_slugs:
                errors.append(f"recipes:{recipe.get('slug')} ingredient references unknown item {item_slug}")
    for node in content.get("gathering", []):
        if node.get("map_slug") and node["map_slug"] not in map_slugs:
            errors.append(f"gathering:{node.get('slug')} references unknown map_slug {node['map_slug']}")
        for entry in node.get("loot_table", []):
            if entry.get("item") not in item_slugs:
                errors.append(f"gathering:{node.get('slug')} references unknown loot item {entry.get('item')}")
            if entry.get("weight", 0) <= 0:
                errors.append(f"gathering:{node.get('slug')} loot weight must be positive")

    if errors:
        raise ContentValidationError("Content pack validation failed:\n- " + "\n- ".join(errors))


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    race TEXT NOT NULL,
    sex TEXT NOT NULL,
    nation TEXT NOT NULL,
    main_job TEXT NOT NULL,
    sub_job TEXT,
    level INTEGER NOT NULL DEFAULT 1,
    exp INTEGER NOT NULL DEFAULT 0,
    hp INTEGER NOT NULL, mp INTEGER NOT NULL,
    str INTEGER NOT NULL, dex INTEGER NOT NULL, vit INTEGER NOT NULL,
    agi INTEGER NOT NULL, int INTEGER NOT NULL, mnd INTEGER NOT NULL, chr INTEGER NOT NULL,
    current_map TEXT NOT NULL DEFAULT 'southern_sandoria'
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    stack_size INTEGER NOT NULL DEFAULT 1,
    data_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS inventory (
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    equipped_slot TEXT,
    PRIMARY KEY(character_id, item_id, equipped_slot)
);
CREATE TABLE IF NOT EXISTS key_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS character_key_items (
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    key_item_id INTEGER NOT NULL REFERENCES key_items(id),
    acquired_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(character_id, key_item_id)
);
CREATE TABLE IF NOT EXISTS maps (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    water_type TEXT,
    resource_nodes_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    map_slug TEXT NOT NULL REFERENCES maps(slug),
    dialogue TEXT NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS quests (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    quest_type TEXT NOT NULL DEFAULT 'side',
    start_npc_slug TEXT REFERENCES npcs(slug),
    prerequisites_json TEXT NOT NULL DEFAULT '[]',
    objectives_json TEXT NOT NULL DEFAULT '[]',
    rewards_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS character_quests (
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    quest_slug TEXT NOT NULL REFERENCES quests(slug),
    status TEXT NOT NULL DEFAULT 'available',
    progress_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY(character_id, quest_slug)
);
CREATE TABLE IF NOT EXISTS mobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    family TEXT NOT NULL,
    job TEXT,
    level INTEGER NOT NULL,
    map_slug TEXT REFERENCES maps(slug),
    stats_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS mob_loot (
    mob_slug TEXT NOT NULL REFERENCES mobs(slug) ON DELETE CASCADE,
    item_slug TEXT NOT NULL REFERENCES items(slug),
    weight INTEGER NOT NULL,
    min_qty INTEGER NOT NULL DEFAULT 1,
    max_qty INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY(mob_slug, item_slug)
);
CREATE TABLE IF NOT EXISTS recipes (
    slug TEXT PRIMARY KEY,
    craft TEXT NOT NULL,
    result_item_slug TEXT NOT NULL REFERENCES items(slug),
    skill_required INTEGER NOT NULL DEFAULT 0,
    ingredients_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS gathering_nodes (
    slug TEXT PRIMARY KEY,
    map_slug TEXT NOT NULL REFERENCES maps(slug),
    kind TEXT NOT NULL,
    loot_table_json TEXT NOT NULL DEFAULT '[]'
);
"""

ITEMS = [
    ("bronze_sword", "Bronze Sword", "weapon", {"slot": "main", "jobs": ["Warrior"], "damage": 4}),
    ("bronze_harness", "Bronze Harness", "armor", {"slot": "body", "defense": 2}),
    ("cesti", "Cesti", "weapon", {"slot": "main", "jobs": ["Monk"], "damage": 3}),
    ("kenpogi", "Kenpogi", "armor", {"slot": "body", "defense": 1}),
    ("ash_staff", "Ash Staff", "weapon", {"slot": "main", "jobs": ["White Mage"], "damage": 3}),
    ("scroll_cure", "Scroll of Cure", "scroll", {"spell": "Cure", "jobs": ["White Mage", "Red Mage"]}),
    ("willow_wand", "Willow Wand", "weapon", {"slot": "main", "jobs": ["Black Mage"], "damage": 2}),
    ("scroll_stone", "Scroll of Stone", "scroll", {"spell": "Stone", "jobs": ["Black Mage", "Red Mage"]}),
    ("wax_sword", "Wax Sword", "weapon", {"slot": "main", "jobs": ["Red Mage"], "damage": 3}),
    ("scroll_dia", "Scroll of Dia", "scroll", {"spell": "Dia", "jobs": ["White Mage", "Red Mage"]}),
    ("bronze_knife", "Bronze Knife", "weapon", {"slot": "main", "jobs": ["Thief"], "damage": 3}),
    ("bandits_vest", "Bandit's Vest", "armor", {"slot": "body", "defense": 1}),
    ("yagudo_feather", "Yagudo Feather", "material", {}),
    ("beastcoin", "Beastcoin", "currency", {}),
    ("moat_carp", "Moat Carp", "fish", {"water": "fresh"}),
    ("bastore_sardine", "Bastore Sardine", "fish", {"water": "salt"}),
    ("icefish", "Icefish", "fish", {"water": "ice"}),
    ("copper_ore", "Copper Ore", "material", {}),
    ("bronze_ingot", "Bronze Ingot", "material", {}),
]

MAPS = [
    ("southern_sandoria_gate", "Southern San d'Oria Gate", "Ronfaure", "fresh", ["logging", "fishing"]),
    ("bastok_mines", "Bastok Mines", "Gustaberg", None, ["mining"]),
    ("windurst_waters", "Windurst Waters", "Sarutabaruta", "fresh", ["fishing"]),
    ("bastore_coast", "Bastore Coast", "Zulkheim", "salt", ["fishing"]),
    ("qufim_ice_lake", "Qufim Ice Lake", "Qufim", "ice", ["ice_fishing"]),
]

NPCS = [
    ("gate_guard_aile", "Ailevia", "southern_sandoria_gate", "Keep your weapon sharp and your eyes sharper."),
    ("miner_desk", "Hungry Miner", "bastok_mines", "Bring me ore and I'll teach you the bones of smithing."),
]

QUESTS = [
    ("first_steps", "First Steps Outside the Gate", "main", "gate_guard_aile", [], [{"type": "defeat", "mob_family": "Yagudo", "count": 1}], {"gil": 100, "items": {"beastcoin": 1}}),
    ("ore_for_the_miner", "Ore for the Miner", "side", "miner_desk", [], [{"type": "gather", "item": "copper_ore", "count": 2}], {"items": {"bronze_ingot": 1}}),
]

MOBS = [
    ("yagudo_acolyte_l5", "Yagudo Acolyte", "Yagudo", "White Mage", 5, "southern_sandoria_gate", {"hp": 42, "mp": 28}),
    ("forest_hare_l2", "Forest Hare", "Beast", None, 2, "southern_sandoria_gate", {"hp": 24}),
]

LOOT = [
    ("yagudo_acolyte_l5", "ash_staff", 20, 1, 1),
    ("yagudo_acolyte_l5", "scroll_cure", 12, 1, 1),
    ("yagudo_acolyte_l5", "yagudo_feather", 50, 1, 2),
    ("yagudo_acolyte_l5", "beastcoin", 30, 1, 3),
    ("forest_hare_l2", "beastcoin", 10, 1, 1),
]

RECIPES = [("smelt_bronze", "Smithing", "bronze_ingot", 0, {"copper_ore": 3})]
GATHERING = [
    ("bastok_copper_vein", "bastok_mines", "mining", [{"item": "copper_ore", "weight": 80}, {"item": "beastcoin", "weight": 5}]),
    ("ronfaure_pond", "southern_sandoria_gate", "fishing", [{"item": "moat_carp", "weight": 70}]),
    ("bastore_surf", "bastore_coast", "fishing", [{"item": "bastore_sardine", "weight": 75}]),
    ("qufim_ice_hole", "qufim_ice_lake", "ice_fishing", [{"item": "icefish", "weight": 75}]),
]


def connect(path: str | Path = "vanadiel.sqlite3") -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    con.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)", (str(SCHEMA_VERSION),))
    seed(con)
    normalize_character_locations(con)
    con.commit()


def load_content_pack(path: str | Path | None = None) -> dict:
    """Load an extensible content pack.

    By default this reads the bundled core JSON pack. Modders can pass another
    JSON file with the same top-level keys to seed custom/private content.
    """
    if path is None:
        raw = files("vanadiel_console.data").joinpath("core_content.json").read_text(encoding="utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")
    content = json.loads(raw)
    validate_content_pack(content)
    return content


def seed(con: sqlite3.Connection, content_path: str | Path | None = None) -> None:
    content = load_content_pack(content_path)
    con.executemany("INSERT OR IGNORE INTO items(slug, name, kind, data_json) VALUES(?,?,?,?)", [(i["slug"], i["name"], i["kind"], json.dumps(i.get("data", {}))) for i in content.get("items", [])])
    con.executemany("INSERT OR IGNORE INTO maps(slug, name, region, water_type, resource_nodes_json) VALUES(?,?,?,?,?)", [(m["slug"], m["name"], m["region"], m.get("water_type"), json.dumps(m.get("resource_nodes", []))) for m in content.get("maps", [])])
    con.executemany("INSERT OR IGNORE INTO npcs(slug, name, map_slug, dialogue) VALUES(?,?,?,?)", [(n["slug"], n["name"], n["map_slug"], n.get("dialogue", "")) for n in content.get("npcs", [])])
    con.executemany("INSERT OR IGNORE INTO quests(slug, title, quest_type, start_npc_slug, prerequisites_json, objectives_json, rewards_json) VALUES(?,?,?,?,?,?,?)", [(q["slug"], q["title"], q.get("quest_type", "side"), q.get("start_npc_slug"), json.dumps(q.get("prerequisites", [])), json.dumps(q.get("objectives", [])), json.dumps(q.get("rewards", {}))) for q in content.get("quests", [])])
    con.executemany("INSERT OR IGNORE INTO mobs(slug, name, family, job, level, map_slug, stats_json) VALUES(?,?,?,?,?,?,?)", [(m["slug"], m["name"], m["family"], m.get("job"), m["level"], m.get("map_slug"), json.dumps(m.get("stats", {}))) for m in content.get("mobs", [])])
    con.executemany("INSERT OR IGNORE INTO mob_loot(mob_slug, item_slug, weight, min_qty, max_qty) VALUES(?,?,?,?,?)", [(l["mob_slug"], l["item_slug"], l["weight"], l.get("min_qty", 1), l.get("max_qty", 1)) for l in content.get("loot", [])])
    con.executemany("INSERT OR IGNORE INTO recipes(slug, craft, result_item_slug, skill_required, ingredients_json) VALUES(?,?,?,?,?)", [(r["slug"], r["craft"], r["result_item_slug"], r.get("skill_required", 0), json.dumps(r.get("ingredients", {}))) for r in content.get("recipes", [])])
    con.executemany("INSERT OR IGNORE INTO gathering_nodes(slug, map_slug, kind, loot_table_json) VALUES(?,?,?,?)", [(g["slug"], g["map_slug"], g["kind"], json.dumps(g.get("loot_table", []))) for g in content.get("gathering", [])])


def slug_for_item_name(con: sqlite3.Connection, name: str) -> str:
    row = con.execute("SELECT slug FROM items WHERE name = ?", (name,)).fetchone()
    if not row:
        raise ValueError(f"No item named {name}")
    return row["slug"]


STARTING_MAP_BY_NATION = {
    "San d'Oria": "southern_sandoria",
    "Bastok": "bastok_markets",
    "Windurst": "windurst_waters",
}


LEGACY_MAP_ALIASES = {
    "Southern San dOria Gate": "southern_sandoria",
    "Southern San d'Oria Gate": "southern_sandoria",
    "Southern San d'Oria": "southern_sandoria",
    "Bastok Mines": "bastok_mines_city",
    "Windurst Waters": "windurst_waters",
}


def normalize_character_locations(con: sqlite3.Connection) -> None:
    """Convert legacy display names to map slugs and repair bad locations."""
    rows = con.execute("SELECT id, nation, current_map FROM characters").fetchall()
    for row in rows:
        current = row["current_map"]
        candidate = LEGACY_MAP_ALIASES.get(current, current)
        exists = con.execute("SELECT 1 FROM maps WHERE slug = ?", (candidate,)).fetchone()
        if not exists:
            candidate = STARTING_MAP_BY_NATION.get(row["nation"], "southern_sandoria")
        if candidate != current:
            con.execute("UPDATE characters SET current_map = ? WHERE id = ?", (candidate, row["id"]))


def current_location(con: sqlite3.Connection, character_id: int) -> sqlite3.Row:
    row = con.execute(
        """SELECT m.* FROM characters c JOIN maps m ON m.slug = c.current_map WHERE c.id = ?""",
        (character_id,),
    ).fetchone()
    if row:
        return row
    normalize_character_locations(con)
    row = con.execute(
        """SELECT m.* FROM characters c JOIN maps m ON m.slug = c.current_map WHERE c.id = ?""",
        (character_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"Character {character_id} has no valid location")
    return row


def set_current_location(con: sqlite3.Connection, character_id: int, map_slug: str) -> None:
    if not con.execute("SELECT 1 FROM maps WHERE slug = ?", (map_slug,)).fetchone():
        raise ValueError(f"Unknown map: {map_slug}")
    con.execute("UPDATE characters SET current_map = ? WHERE id = ?", (map_slug, character_id))
    con.commit()


def create_character(con: sqlite3.Connection, build: CharacterBuild) -> int:
    stats = calculate_stats(build)
    current_map = STARTING_MAP_BY_NATION.get(build.nation, "southern_sandoria")
    cur = con.execute(
        """INSERT INTO characters(name, race, sex, nation, main_job, sub_job, hp, mp, str, dex, vit, agi, int, mnd, chr, current_map)
        VALUES(:name,:race,:sex,:nation,:main_job,:sub_job,:hp,:mp,:str,:dex,:vit,:agi,:int,:mnd,:chr,:current_map)""",
        {**build.__dict__, **stats, "current_map": current_map},
    )
    char_id = int(cur.lastrowid)
    for item_name in STARTING_GEAR[build.main_job]:
        add_item(con, char_id, slug_for_item_name(con, item_name), 1)
    con.commit()
    return char_id


def add_item(con: sqlite3.Connection, character_id: int, item_slug: str, qty: int = 1, slot: str | None = None) -> None:
    item = con.execute("SELECT id FROM items WHERE slug = ?", (item_slug,)).fetchone()
    if not item:
        raise ValueError(f"Unknown item slug: {item_slug}")
    con.execute(
        """INSERT INTO inventory(character_id, item_id, quantity, equipped_slot) VALUES(?,?,?,?)
        ON CONFLICT(character_id, item_id, equipped_slot) DO UPDATE SET quantity = quantity + excluded.quantity""",
        (character_id, item["id"], qty, slot),
    )


def item_data(con: sqlite3.Connection, item_slug: str) -> dict:
    row = con.execute("SELECT data_json FROM items WHERE slug = ?", (item_slug,)).fetchone()
    if not row:
        raise ValueError(f"Unknown item slug: {item_slug}")
    return json.loads(row["data_json"] or "{}")


def equipped_items(con: sqlite3.Connection, character_id: int) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT i.slug, i.name, i.kind, i.data_json, inv.equipped_slot
        FROM inventory inv JOIN items i ON i.id = inv.item_id
        WHERE inv.character_id = ? AND inv.equipped_slot IS NOT NULL
        ORDER BY inv.equipped_slot""",
        (character_id,),
    ).fetchall()


def equipment_bonuses(con: sqlite3.Connection, character_id: int) -> dict[str, int]:
    bonuses = {"attack": 0, "defense": 0, "magic": 0}
    for row in equipped_items(con, character_id):
        data = json.loads(row["data_json"] or "{}")
        bonuses["attack"] += int(data.get("damage", 0))
        bonuses["defense"] += int(data.get("defense", 0))
        bonuses["magic"] += int(data.get("magic", 0))
    return bonuses


def unequip_slot(con: sqlite3.Connection, character_id: int, slot: str) -> None:
    row = con.execute(
        """SELECT i.slug FROM inventory inv JOIN items i ON i.id = inv.item_id
        WHERE inv.character_id = ? AND inv.equipped_slot = ?""",
        (character_id, slot),
    ).fetchone()
    if not row:
        return
    con.execute("DELETE FROM inventory WHERE character_id = ? AND equipped_slot = ?", (character_id, slot))
    add_item(con, character_id, row["slug"], 1)
    con.commit()


def equip_item(con: sqlite3.Connection, character_id: int, item_slug: str) -> str:
    item = con.execute("SELECT id, name, data_json FROM items WHERE slug = ?", (item_slug,)).fetchone()
    if not item:
        raise ValueError(f"Unknown item slug: {item_slug}")
    data = json.loads(item["data_json"] or "{}")
    slot = data.get("slot")
    if not slot:
        raise ValueError(f"Item cannot be equipped: {item_slug}")
    character = con.execute("SELECT main_job FROM characters WHERE id = ?", (character_id,)).fetchone()
    if not character:
        raise ValueError(f"Unknown character id: {character_id}")
    allowed_jobs = data.get("jobs")
    if allowed_jobs and character["main_job"] not in allowed_jobs:
        raise ValueError(f"{character['main_job']} cannot equip {item['name']}")
    carried = con.execute(
        """SELECT inv.rowid, inv.quantity FROM inventory inv
        WHERE inv.character_id = ? AND inv.item_id = ? AND inv.equipped_slot IS NULL""",
        (character_id, item["id"]),
    ).fetchone()
    if not carried or carried["quantity"] < 1:
        raise ValueError(f"Item is not in inventory: {item_slug}")
    unequip_slot(con, character_id, slot)
    if carried["quantity"] == 1:
        con.execute("DELETE FROM inventory WHERE rowid = ?", (carried["rowid"],))
    else:
        con.execute("UPDATE inventory SET quantity = quantity - 1 WHERE rowid = ?", (carried["rowid"],))
    add_item(con, character_id, item_slug, 1, slot)
    con.commit()
    return slot


def list_inventory(con: sqlite3.Connection, character_id: int) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT i.slug, i.name, i.kind, inv.quantity, inv.equipped_slot
        FROM inventory inv JOIN items i ON i.id = inv.item_id
        WHERE inv.character_id = ? ORDER BY i.name""",
        (character_id,),
    ).fetchall()
