from __future__ import annotations

import json
import random
import sqlite3
from collections.abc import Sequence

from .db import add_item


def weighted_choice(rows: Sequence[tuple[str, int]]) -> str:
    if not rows:
        raise ValueError("weighted_choice needs at least one row")
    total = sum(max(0, weight) for _, weight in rows)
    if total <= 0:
        raise ValueError("total weight must be positive")
    pick = random.randint(1, total)
    upto = 0
    for slug, weight in rows:
        upto += max(0, weight)
        if pick <= upto:
            return slug
    return rows[-1][0]


def roll_mob_loot(con: sqlite3.Connection, mob_slug: str) -> list[tuple[str, int]]:
    rows = con.execute("SELECT item_slug, weight, min_qty, max_qty FROM mob_loot WHERE mob_slug = ?", (mob_slug,)).fetchall()
    drops: list[tuple[str, int]] = []
    for row in rows:
        # Each row gets an independent weighted chance against 100, easy to tune in DB.
        if random.randint(1, 100) <= row["weight"]:
            drops.append((row["item_slug"], random.randint(row["min_qty"], row["max_qty"])))
    return drops


def defeat_mob(con: sqlite3.Connection, character_id: int, mob_slug: str) -> list[tuple[str, int]]:
    mob = con.execute("SELECT * FROM mobs WHERE slug = ?", (mob_slug,)).fetchone()
    if not mob:
        raise ValueError(f"Unknown mob: {mob_slug}")
    drops = roll_mob_loot(con, mob_slug)
    for item_slug, qty in drops:
        add_item(con, character_id, item_slug, qty)
    con.execute("UPDATE characters SET exp = exp + ? WHERE id = ?", (mob["level"] * 20, character_id))
    con.commit()
    return drops


def gather(con: sqlite3.Connection, character_id: int, node_slug: str) -> tuple[str, int]:
    node = con.execute("SELECT * FROM gathering_nodes WHERE slug = ?", (node_slug,)).fetchone()
    if not node:
        raise ValueError(f"Unknown gathering node: {node_slug}")
    table = json.loads(node["loot_table_json"])
    item_slug = weighted_choice([(entry["item"], int(entry["weight"])) for entry in table])
    add_item(con, character_id, item_slug, 1)
    con.commit()
    return item_slug, 1


def craft(con: sqlite3.Connection, character_id: int, recipe_slug: str) -> bool:
    recipe = con.execute("SELECT * FROM recipes WHERE slug = ?", (recipe_slug,)).fetchone()
    if not recipe:
        raise ValueError(f"Unknown recipe: {recipe_slug}")
    ingredients = json.loads(recipe["ingredients_json"])
    for item_slug, qty in ingredients.items():
        row = con.execute(
            """SELECT COALESCE(SUM(inv.quantity), 0) AS quantity FROM inventory inv JOIN items i ON i.id = inv.item_id
            WHERE inv.character_id = ? AND i.slug = ? AND inv.equipped_slot IS NULL""",
            (character_id, item_slug),
        ).fetchone()
        if not row or row["quantity"] < qty:
            return False
    for item_slug, qty in ingredients.items():
        remaining = qty
        rows = con.execute(
            """SELECT inv.rowid, inv.quantity FROM inventory inv JOIN items i ON i.id = inv.item_id
            WHERE inv.character_id = ? AND i.slug = ? AND inv.equipped_slot IS NULL ORDER BY inv.rowid""",
            (character_id, item_slug),
        ).fetchall()
        for row in rows:
            if remaining <= 0:
                break
            take = min(remaining, row["quantity"])
            con.execute("UPDATE inventory SET quantity = quantity - ? WHERE rowid = ?", (take, row["rowid"]))
            remaining -= take
    con.execute("DELETE FROM inventory WHERE quantity <= 0")
    add_item(con, character_id, recipe["result_item_slug"], 1)
    con.commit()
    return True


def fishing_nodes_for_water(con: sqlite3.Connection, water_type: str) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT g.* FROM gathering_nodes g JOIN maps m ON m.slug = g.map_slug
        WHERE g.kind LIKE '%fishing%' AND m.water_type = ? ORDER BY g.slug""",
        (water_type,),
    ).fetchall()
