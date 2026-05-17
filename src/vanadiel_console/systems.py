from __future__ import annotations

import json
import random
import sqlite3
from dataclasses import dataclass
from collections.abc import Sequence

from .db import STARTING_MAP_BY_NATION, add_item
from .models import CharacterBuild, calculate_stats


@dataclass
class Combatant:
    name: str
    hp: int
    mp: int
    str_: int
    vit: int
    dex: int
    agi: int
    int_: int
    mnd: int
    level: int = 1


@dataclass
class CombatResult:
    victory: bool
    fled: bool
    exp: int
    drops: list[tuple[str, int]]
    log: list[str]


@dataclass
class FishingState:
    node_slug: str
    fish_slug: str
    fish_name: str
    tension: int
    progress: int = 0
    rounds: int = 0
    complete: bool = False
    success: bool = False


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



def exp_to_next_level(level: int) -> int:
    """Cumulative EXP required for the next level. Simple early-game curve."""
    return max(1, level) * 100


def apply_experience(con: sqlite3.Connection, character_id: int, exp: int) -> int:
    """Add EXP, apply level-ups, refresh base stats, and return levels gained."""
    row = con.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown character id: {character_id}")
    total_exp = row["exp"] + exp
    level = row["level"]
    levels_gained = 0
    while total_exp >= exp_to_next_level(level):
        level += 1
        levels_gained += 1
    if levels_gained:
        stats = calculate_stats(CharacterBuild(row["name"], row["race"], row["sex"], row["nation"], row["main_job"], row["sub_job"]), level=level)
        con.execute(
            """UPDATE characters SET level=?, exp=?, hp=?, mp=?, str=?, dex=?, vit=?, agi=?, int=?, mnd=?, chr=? WHERE id=?""",
            (level, total_exp, stats["hp"], stats["mp"], stats["str"], stats["dex"], stats["vit"], stats["agi"], stats["int"], stats["mnd"], stats["chr"], character_id),
        )
    else:
        con.execute("UPDATE characters SET exp = ? WHERE id = ?", (total_exp, character_id))
    return levels_gained

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
    apply_experience(con, character_id, mob["level"] * 20)
    con.commit()
    return drops


def load_player_combatant(con: sqlite3.Connection, character_id: int) -> Combatant:
    row = con.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown character id: {character_id}")
    return Combatant(
        name=row["name"],
        hp=row["hp"],
        mp=row["mp"],
        str_=row["str"],
        vit=row["vit"],
        dex=row["dex"],
        agi=row["agi"],
        int_=row["int"],
        mnd=row["mnd"],
        level=row["level"],
    )


def load_mob_combatant(con: sqlite3.Connection, mob_slug: str) -> Combatant:
    row = con.execute("SELECT * FROM mobs WHERE slug = ?", (mob_slug,)).fetchone()
    if not row:
        raise ValueError(f"Unknown mob: {mob_slug}")
    stats = json.loads(row["stats_json"])
    level = row["level"]
    return Combatant(
        name=row["name"],
        hp=int(stats.get("hp", 18 + level * 6)),
        mp=int(stats.get("mp", 0)),
        str_=int(stats.get("str", 5 + level)),
        vit=int(stats.get("vit", 4 + level)),
        dex=int(stats.get("dex", 4 + level)),
        agi=int(stats.get("agi", 4 + level)),
        int_=int(stats.get("int", 4 + level)),
        mnd=int(stats.get("mnd", 4 + level)),
        level=level,
    )


def physical_damage(attacker: Combatant, defender: Combatant, defend_bonus: int = 0) -> int:
    variance = random.randint(0, 3)
    attack = attacker.str_ + attacker.dex // 2 + attacker.level + variance
    defense = defender.vit // 2 + defender.agi // 3 + defend_bonus
    return max(1, attack - defense)


def spell_damage(caster: Combatant, target: Combatant) -> tuple[str, int, int]:
    if caster.mp >= 8:
        cost = 8
        dmg = max(3, caster.int_ + caster.mnd // 2 + random.randint(1, 6) - target.mnd // 3)
        return "Stone", cost, dmg
    if caster.mp >= 4:
        cost = 4
        dmg = max(2, caster.int_ // 2 + random.randint(1, 4))
        return "Dia", cost, dmg
    return "fizzle", 0, 0


def resolve_combat_turn(player: Combatant, mob: Combatant, action: str) -> list[str]:
    """Resolve one player action and one mob response in-place."""
    log: list[str] = []
    action = action.lower().strip()
    defend_bonus = 0

    if action == "attack":
        dmg = physical_damage(player, mob)
        mob.hp -= dmg
        log.append(f"{player.name} attacks {mob.name} for {dmg} damage.")
    elif action == "cast":
        spell, cost, dmg = spell_damage(player, mob)
        if cost == 0:
            log.append(f"{player.name} tries to cast, but lacks MP.")
        else:
            player.mp -= cost
            mob.hp -= dmg
            log.append(f"{player.name} casts {spell} for {dmg} damage. (-{cost} MP)")
    elif action == "defend":
        defend_bonus = max(2, player.vit // 2)
        log.append(f"{player.name} braces for impact.")
    else:
        raise ValueError(f"Unknown combat action: {action}")

    if mob.hp <= 0:
        log.append(f"{mob.name} is defeated!")
        return log

    if mob.mp >= 8 and random.randint(1, 100) <= 35:
        spell, cost, dmg = spell_damage(mob, player)
        mob.mp -= cost
        player.hp -= dmg
        log.append(f"{mob.name} casts {spell} for {dmg} damage.")
    else:
        dmg = physical_damage(mob, player, defend_bonus=defend_bonus)
        player.hp -= dmg
        log.append(f"{mob.name} hits back for {dmg} damage.")
    return log


def finish_combat_victory(con: sqlite3.Connection, character_id: int, mob_slug: str) -> tuple[int, list[tuple[str, int]]]:
    mob = con.execute("SELECT level FROM mobs WHERE slug = ?", (mob_slug,)).fetchone()
    if not mob:
        raise ValueError(f"Unknown mob: {mob_slug}")
    exp = mob["level"] * 20
    drops = roll_mob_loot(con, mob_slug)
    for item_slug, qty in drops:
        add_item(con, character_id, item_slug, qty)
    apply_experience(con, character_id, exp)
    con.commit()
    return exp, drops


def return_home_after_knockout(con: sqlite3.Connection, character_id: int) -> str:
    """Recover a knocked-out character at their nation home point.

    This is intentionally forgiving for the prototype: no EXP loss yet, full HP/MP
    restored from current level stats, and location reset to the starting nation.
    """
    row = con.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown character id: {character_id}")
    home_map = STARTING_MAP_BY_NATION.get(row["nation"], "southern_sandoria")
    stats = calculate_stats(CharacterBuild(row["name"], row["race"], row["sex"], row["nation"], row["main_job"], row["sub_job"]), level=row["level"])
    con.execute(
        """UPDATE characters SET current_map=?, hp=?, mp=? WHERE id=?""",
        (home_map, stats["hp"], stats["mp"], character_id),
    )
    con.commit()
    return home_map


def auto_combat(con: sqlite3.Connection, character_id: int, mob_slug: str, actions: Sequence[str]) -> CombatResult:
    """Non-interactive combat runner for tests and future automation."""
    player = load_player_combatant(con, character_id)
    mob = load_mob_combatant(con, mob_slug)
    log: list[str] = []
    for action in actions:
        if action == "flee":
            fled = random.randint(1, 100) <= 55
            log.append("You escape!" if fled else "You fail to escape!")
            if fled:
                return CombatResult(False, True, 0, [], log)
        else:
            log.extend(resolve_combat_turn(player, mob, action))
        if mob.hp <= 0:
            exp, drops = finish_combat_victory(con, character_id, mob_slug)
            return CombatResult(True, False, exp, drops, log)
        if player.hp <= 0:
            home_map = return_home_after_knockout(con, character_id)
            log.append(f"{player.name} is knocked out and returns to {home_map}.")
            return CombatResult(False, False, 0, [], log)
    return CombatResult(False, False, 0, [], log)


def completed_quest_slugs(con: sqlite3.Connection, character_id: int) -> set[str]:
    rows = con.execute(
        "SELECT quest_slug FROM character_quests WHERE character_id = ? AND status = 'complete'",
        (character_id,),
    ).fetchall()
    return {row["quest_slug"] for row in rows}


def quest_prerequisites(con: sqlite3.Connection, quest_slug: str) -> list[str]:
    row = con.execute("SELECT prerequisites_json FROM quests WHERE slug = ?", (quest_slug,)).fetchone()
    if not row:
        raise ValueError(f"Unknown quest: {quest_slug}")
    return list(json.loads(row["prerequisites_json"] or "[]"))


def missing_quest_prerequisites(con: sqlite3.Connection, character_id: int, quest_slug: str) -> list[str]:
    completed = completed_quest_slugs(con, character_id)
    return [slug for slug in quest_prerequisites(con, quest_slug) if slug not in completed]


def quest_is_unlocked(con: sqlite3.Connection, character_id: int, quest_slug: str) -> bool:
    return not missing_quest_prerequisites(con, character_id, quest_slug)


def available_quests(con: sqlite3.Connection, character_id: int) -> list[sqlite3.Row]:
    rows = con.execute(
        """SELECT * FROM quests
        WHERE slug NOT IN (SELECT quest_slug FROM character_quests WHERE character_id = ?)
        ORDER BY quest_type, title""",
        (character_id,),
    ).fetchall()
    return [row for row in rows if quest_is_unlocked(con, character_id, row["slug"])]


def accept_quest(con: sqlite3.Connection, character_id: int, quest_slug: str) -> None:
    missing = missing_quest_prerequisites(con, character_id, quest_slug)
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Quest {quest_slug} is locked; complete prerequisite(s): {names}")
    con.execute(
        """INSERT INTO character_quests(character_id, quest_slug, status, progress_json) VALUES(?,?, 'active', '{}')
        ON CONFLICT(character_id, quest_slug) DO NOTHING""",
        (character_id, quest_slug),
    )
    con.commit()


def mark_quest_complete(con: sqlite3.Connection, character_id: int, quest_slug: str) -> None:
    con.execute(
        """INSERT INTO character_quests(character_id, quest_slug, status, progress_json) VALUES(?,?, 'complete', '{}')
        ON CONFLICT(character_id, quest_slug) DO UPDATE SET status = 'complete'""",
        (character_id, quest_slug),
    )
    con.commit()


def gather(con: sqlite3.Connection, character_id: int, node_slug: str) -> tuple[str, int]:
    node = con.execute("SELECT * FROM gathering_nodes WHERE slug = ?", (node_slug,)).fetchone()
    if not node:
        raise ValueError(f"Unknown gathering node: {node_slug}")
    table = json.loads(node["loot_table_json"])
    item_slug = weighted_choice([(entry["item"], int(entry["weight"])) for entry in table])
    add_item(con, character_id, item_slug, 1)
    con.commit()
    return item_slug, 1


def start_fishing(con: sqlite3.Connection, node_slug: str) -> FishingState:
    node = con.execute("SELECT * FROM gathering_nodes WHERE slug = ?", (node_slug,)).fetchone()
    if not node:
        raise ValueError(f"Unknown fishing node: {node_slug}")
    if "fishing" not in node["kind"]:
        raise ValueError(f"Node is not fishable: {node_slug}")

    table = json.loads(node["loot_table_json"])
    fish_slug = weighted_choice([(entry["item"], int(entry["weight"])) for entry in table])
    fish = con.execute("SELECT name FROM items WHERE slug = ?", (fish_slug,)).fetchone()
    fish_name = fish["name"] if fish else fish_slug

    return FishingState(node_slug=node_slug, fish_slug=fish_slug, fish_name=fish_name, tension=random.randint(25, 45))


def resolve_fishing_turn(con: sqlite3.Connection, character_id: int, state: FishingState, action: str) -> str:
    if state.complete:
        return "The fishing attempt is already over."

    action = action.lower().strip()
    fish_pull = random.randint(6, 18)
    state.rounds += 1
    if action == "reel":
        state.progress += random.randint(18, 30)
        state.tension += fish_pull + 8
        line = f"You reel hard. Progress {state.progress}%, tension {state.tension}%."
    elif action == "slacken":
        state.tension = max(0, state.tension - random.randint(15, 28))
        state.progress = max(0, state.progress - random.randint(0, 8))
        line = f"You slacken the line. Progress {state.progress}%, tension {state.tension}%."
    elif action == "wait":
        state.progress += random.randint(5, 13)
        state.tension += fish_pull - 6
        line = f"You wait for the right pull. Progress {state.progress}%, tension {state.tension}%."
    else:
        raise ValueError(f"Unknown fishing action: {action}")

    if state.tension >= 100:
        state.complete = True
        return f"{line} The line snaps!"
    if state.tension <= 5 and random.randint(1, 100) <= 45:
        state.complete = True
        return f"{line} The fish slips the hook."
    if state.progress >= 100:
        add_item(con, character_id, state.fish_slug, 1)
        con.commit()
        state.complete = True
        state.success = True
        return f"{line} Caught {state.fish_name}!"
    if state.rounds >= 8:
        state.complete = True
        return f"{line} The fish gets away after a long struggle."
    return line


def fishing_attempt(con: sqlite3.Connection, character_id: int, node_slug: str, tension_actions: Sequence[str]) -> tuple[bool, str | None, list[str]]:
    """Resolve a full fishing attempt from a sequence of actions.

    Player actions are simple text choices: `reel`, `wait`, and `slacken`.
    The fish builds tension over rounds; too much tension snaps the line, too
    little gives the fish a chance to escape. Success awards one fish item.
    """
    state = start_fishing(con, node_slug)
    log = [f"Something bites! It feels like {state.fish_name}."]
    for action in (list(tension_actions) or ["wait"])[:8]:
        log.append(resolve_fishing_turn(con, character_id, state, action))
        if state.complete:
            break
    return state.success, state.fish_slug if state.success else None, log


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
