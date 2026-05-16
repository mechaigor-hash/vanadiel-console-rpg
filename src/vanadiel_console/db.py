from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .models import CharacterBuild, STARTING_GEAR, calculate_stats

SCHEMA_VERSION = 1

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
    current_map TEXT NOT NULL DEFAULT 'Southern San dOria Gate'
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
    con.commit()


def seed(con: sqlite3.Connection) -> None:
    con.executemany("INSERT OR IGNORE INTO items(slug, name, kind, data_json) VALUES(?,?,?,?)", [(s, n, k, json.dumps(d)) for s, n, k, d in ITEMS])
    con.executemany("INSERT OR IGNORE INTO maps(slug, name, region, water_type, resource_nodes_json) VALUES(?,?,?,?,?)", [(s, n, r, w, json.dumps(nodes)) for s, n, r, w, nodes in MAPS])
    con.executemany("INSERT OR IGNORE INTO npcs(slug, name, map_slug, dialogue) VALUES(?,?,?,?)", NPCS)
    con.executemany("INSERT OR IGNORE INTO quests(slug, title, quest_type, start_npc_slug, prerequisites_json, objectives_json, rewards_json) VALUES(?,?,?,?,?,?,?)", [(s, t, qt, npc, json.dumps(pre), json.dumps(obj), json.dumps(rew)) for s, t, qt, npc, pre, obj, rew in QUESTS])
    con.executemany("INSERT OR IGNORE INTO mobs(slug, name, family, job, level, map_slug, stats_json) VALUES(?,?,?,?,?,?,?)", [(s, n, f, j, lvl, m, json.dumps(st)) for s, n, f, j, lvl, m, st in MOBS])
    con.executemany("INSERT OR IGNORE INTO mob_loot(mob_slug, item_slug, weight, min_qty, max_qty) VALUES(?,?,?,?,?)", LOOT)
    con.executemany("INSERT OR IGNORE INTO recipes(slug, craft, result_item_slug, skill_required, ingredients_json) VALUES(?,?,?,?,?)", [(s, c, r, sk, json.dumps(ing)) for s, c, r, sk, ing in RECIPES])
    con.executemany("INSERT OR IGNORE INTO gathering_nodes(slug, map_slug, kind, loot_table_json) VALUES(?,?,?,?)", [(s, m, k, json.dumps(loot)) for s, m, k, loot in GATHERING])


def slug_for_item_name(con: sqlite3.Connection, name: str) -> str:
    row = con.execute("SELECT slug FROM items WHERE name = ?", (name,)).fetchone()
    if not row:
        raise ValueError(f"No item named {name}")
    return row["slug"]


def create_character(con: sqlite3.Connection, build: CharacterBuild) -> int:
    stats = calculate_stats(build)
    cur = con.execute(
        """INSERT INTO characters(name, race, sex, nation, main_job, sub_job, hp, mp, str, dex, vit, agi, int, mnd, chr)
        VALUES(:name,:race,:sex,:nation,:main_job,:sub_job,:hp,:mp,:str,:dex,:vit,:agi,:int,:mnd,:chr)""",
        {**build.__dict__, **stats},
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


def list_inventory(con: sqlite3.Connection, character_id: int) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT i.slug, i.name, i.kind, inv.quantity, inv.equipped_slot
        FROM inventory inv JOIN items i ON i.id = inv.item_id
        WHERE inv.character_id = ? ORDER BY i.name""",
        (character_id,),
    ).fetchall()
