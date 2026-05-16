from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

if __package__ in {None, ""}:
    # Allow direct execution:
    #   python src/vanadiel_console/app.py
    # Normal package/module execution still uses the relative imports below.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from vanadiel_console.db import connect, create_character, init_db, list_inventory
    from vanadiel_console.models import JOBS, NATIONS, RACES, SEXES, CharacterBuild, calculate_stats
    from vanadiel_console.systems import craft, finish_combat_victory, gather, load_mob_combatant, load_player_combatant, resolve_combat_turn, resolve_fishing_turn, start_fishing
else:
    from .db import connect, create_character, init_db, list_inventory
    from .models import JOBS, NATIONS, RACES, SEXES, CharacterBuild, calculate_stats
    from .systems import craft, finish_combat_victory, gather, load_mob_combatant, load_player_combatant, resolve_combat_turn, resolve_fishing_turn, start_fishing

DB_PATH = Path(os.environ.get("VANADIEL_DB", "vanadiel.sqlite3"))

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"

ART = rf"""
{CYAN} __     __                 _ _      _   
 \ \   / /_ _ _ __   __ _  __| (_) ___| | 
  \ \ / / _` | '_ \ / _` |/ _` | |/ _ \ | 
   \ V / (_| | | | | (_| | (_| | |  __/ | 
    \_/ \__,_|_| |_|\__,_|\__,_|_|\___|_| 
{RESET}{YELLOW}        Console RPG Prototype{RESET}
"""


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    input(f"\n{YELLOW}Press Enter...{RESET}")


def choose(title: str, options: list[str], allow_none: bool = False) -> str | None:
    while True:
        print(f"\n{BOLD}{title}{RESET}")
        if allow_none:
            print("  0. None")
        for i, option in enumerate(options, start=1):
            print(f"  {i}. {option}")
        raw = input("> ").strip()
        if allow_none and raw == "0":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"{RED}Invalid choice, little goblin noises. Try again.{RESET}")


def ensure_db() -> sqlite3.Connection:
    con = connect(DB_PATH)
    init_db(con)
    return con


def character_select(con: sqlite3.Connection) -> int | None:
    chars = con.execute("SELECT id, name, race, main_job, sub_job, level FROM characters ORDER BY id").fetchall()
    if not chars:
        return None
    print(f"\n{BOLD}Characters{RESET}")
    for row in chars:
        sj = f"/{row['sub_job']}" if row["sub_job"] else ""
        print(f"  {row['id']}. {row['name']} - Lv{row['level']} {row['race']} {row['main_job']}{sj}")
    raw = input("Select character id or blank for new: ").strip()
    if not raw:
        return None
    if raw.isdigit() and any(row["id"] == int(raw) for row in chars):
        return int(raw)
    print(f"{RED}No such character.{RESET}")
    return None


def new_character(con: sqlite3.Connection) -> int:
    clear()
    print(ART)
    name = input("Character name: ").strip() or "Adventurer"
    race = choose("Race", list(RACES))
    sex = choose("Sex", list(SEXES))
    nation = choose("Starting nation", list(NATIONS))
    main_job = choose("Main job", list(JOBS))
    sub_options = [job for job in JOBS if job != main_job]
    sub_job = choose("Subjob (optional)", sub_options, allow_none=True)
    build = CharacterBuild(name=name, race=race, sex=sex, nation=nation, main_job=main_job, sub_job=sub_job)  # type: ignore[arg-type]
    stats = calculate_stats(build)
    print(f"\n{GREEN}Final stats:{RESET}")
    print("  " + "  ".join(f"{k.upper()} {v}" for k, v in stats.items()))
    if input("Create this character? [Y/n] ").strip().lower() == "n":
        return new_character(con)
    return create_character(con, build)


def show_character(con: sqlite3.Connection, character_id: int) -> None:
    row = con.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    print(f"\n{GREEN}{row['name']}{RESET} Lv{row['level']} {row['race']} {row['sex']} from {row['nation']}")
    sj = f" / {row['sub_job']}" if row["sub_job"] else ""
    print(f"Job: {row['main_job']}{sj}    EXP: {row['exp']}")
    print("Stats: " + "  ".join(f"{s.upper()} {row[s]}" for s in ["hp", "mp", "str", "dex", "vit", "agi", "int", "mnd", "chr"]))
    print("\nInventory:")
    for item in list_inventory(con, character_id):
        equipped = f" [{item['equipped_slot']}]" if item["equipped_slot"] else ""
        print(f"  - {item['name']} x{item['quantity']}{equipped}")


def browse_world(con: sqlite3.Connection) -> None:
    print(f"\n{BOLD}Maps{RESET}")
    for row in con.execute("SELECT * FROM maps ORDER BY region, name"):
        water = f", water={row['water_type']}" if row["water_type"] else ""
        print(f"  - {row['name']} ({row['region']}{water})")
    print(f"\n{BOLD}NPCs{RESET}")
    for row in con.execute("SELECT n.name, m.name AS map_name, n.dialogue FROM npcs n JOIN maps m ON m.slug=n.map_slug ORDER BY n.name"):
        print(f"  - {row['name']} @ {row['map_name']}: \"{row['dialogue']}\"")
    print(f"\n{BOLD}Quests & missions{RESET}")
    for row in con.execute("SELECT title, quest_type FROM quests ORDER BY quest_type, title"):
        print(f"  - [{row['quest_type']}] {row['title']}")


def print_drops(drops: list[tuple[str, int]]) -> str:
    if not drops:
        return "none"
    names: list[str] = []
    for slug, qty in drops:
        names.append(f"{slug} x{qty}")
    return ", ".join(names)


def combat_screen(con: sqlite3.Connection, character_id: int, mob_slug: str) -> None:
    player = load_player_combatant(con, character_id)
    mob = load_mob_combatant(con, mob_slug)
    print(f"\n{RED}A {mob.name} attacks!{RESET}")
    while player.hp > 0 and mob.hp > 0:
        print(f"\n{GREEN}{player.name}{RESET} HP {max(0, player.hp)} MP {player.mp}  vs  {RED}{mob.name}{RESET} HP {max(0, mob.hp)} MP {mob.mp}")
        print("  1. Attack")
        print("  2. Cast spell")
        print("  3. Defend")
        print("  4. Flee")
        choice = input("> ").strip()
        if choice == "1":
            action = "attack"
        elif choice == "2":
            action = "cast"
        elif choice == "3":
            action = "defend"
        elif choice == "4":
            import random

            if random.randint(1, 100) <= 55:
                print(f"{YELLOW}You escape!{RESET}")
                return
            print(f"{RED}Couldn't escape!{RESET}")
            action = "defend"
        else:
            print(f"{RED}Invalid combat choice.{RESET}")
            continue

        for line in resolve_combat_turn(player, mob, action):
            print(line)

    if mob.hp <= 0:
        exp, drops = finish_combat_victory(con, character_id, mob_slug)
        print(f"{GREEN}Victory!{RESET} EXP +{exp}. Drops: {print_drops(drops)}")
    else:
        print(f"{RED}You were knocked out. You wake up back near town, bruised and annoyed.{RESET}")


def fishing_screen(con: sqlite3.Connection, character_id: int, node_slug: str) -> None:
    node = con.execute("SELECT g.slug, g.kind, m.name AS map_name, m.water_type FROM gathering_nodes g JOIN maps m ON m.slug=g.map_slug WHERE g.slug=?", (node_slug,)).fetchone()
    if node:
        print(f"\n{CYAN}Fishing at {node['map_name']} ({node['water_type']} water).{RESET}")
    print("Build progress without snapping the line. Actions: reel / wait / slacken")
    state = start_fishing(con, node_slug)
    print(f"Something bites! It feels like {state.fish_name}.")
    for round_no in range(1, 9):
        raw = input(f"Round {round_no}> ").strip().lower()
        if raw in {"r", "reel"}:
            action = "reel"
        elif raw in {"w", "wait"}:
            action = "wait"
        elif raw in {"s", "slacken", "slack"}:
            action = "slacken"
        elif raw in {"q", "quit", "cancel"}:
            print(f"{YELLOW}You pack away the rod.{RESET}")
            return
        else:
            print(f"{RED}Use reel, wait, slacken, or quit.{RESET}")
            continue
        try:
            line = resolve_fishing_turn(con, character_id, state, action)
        except ValueError as exc:
            print(f"{RED}{exc}{RESET}")
            return
        print(line)
        if state.success:
            print(f"{GREEN}Landed: {state.fish_slug}!{RESET}")
            return
        if state.complete:
            print(f"{RED}Fishing attempt failed.{RESET}")
            return
    print(f"{YELLOW}The water goes quiet.{RESET}")


def adventure_menu(con: sqlite3.Connection, character_id: int) -> None:
    while True:
        clear()
        print(ART)
        show_character(con, character_id)
        print(f"\n{BOLD}Menu{RESET}")
        print("  1. Browse maps/NPCs/quests")
        print("  2. Fight sample mob: Yagudo Acolyte Lv5 WHM")
        print("  3. Mine copper in Bastok Mines")
        print("  4. Fish freshwater pond")
        print("  5. Fish saltwater coast")
        print("  6. Ice fish at Qufim")
        print("  7. Craft Bronze Ingot")
        print("  0. Quit")
        choice = input("> ").strip()
        try:
            if choice == "1":
                browse_world(con)
            elif choice == "2":
                combat_screen(con, character_id, "yagudo_acolyte_l5")
            elif choice == "3":
                print(f"{GREEN}Gathered:{RESET} {gather(con, character_id, 'bastok_copper_vein')[0]}")
            elif choice == "4":
                fishing_screen(con, character_id, "ronfaure_pond")
            elif choice == "5":
                fishing_screen(con, character_id, "bastore_surf")
            elif choice == "6":
                fishing_screen(con, character_id, "qufim_ice_hole")
            elif choice == "7":
                print(f"{GREEN}Crafted Bronze Ingot!{RESET}" if craft(con, character_id, "smelt_bronze") else f"{RED}Need 3 Copper Ore.{RESET}")
            elif choice == "0":
                return
            else:
                print(f"{RED}Invalid option.{RESET}")
        except Exception as exc:  # Keep console game resilient while prototyping.
            print(f"{RED}Error: {exc}{RESET}")
        pause()


def main() -> None:
    con = ensure_db()
    clear()
    print(ART)
    character_id = character_select(con) or new_character(con)
    adventure_menu(con, character_id)


if __name__ == "__main__":
    main()
