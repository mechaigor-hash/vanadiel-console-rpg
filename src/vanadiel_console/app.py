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
    from vanadiel_console.db import connect, create_character, current_location, init_db, list_inventory, set_current_location
    from vanadiel_console.models import JOBS, NATIONS, RACES, SEXES, CharacterBuild, calculate_stats
    from vanadiel_console.systems import craft, finish_combat_victory, gather, load_mob_combatant, load_player_combatant, resolve_combat_turn, resolve_fishing_turn, start_fishing
    from vanadiel_console.ui import MenuOption, Navigator, Screen
else:
    from .db import connect, create_character, current_location, init_db, list_inventory, set_current_location
    from .models import JOBS, NATIONS, RACES, SEXES, CharacterBuild, calculate_stats
    from .systems import craft, finish_combat_victory, gather, load_mob_combatant, load_player_combatant, resolve_combat_turn, resolve_fishing_turn, start_fishing
    from .ui import MenuOption, Navigator, Screen

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
    location = current_location(con, character_id)
    print(f"\n{GREEN}{row['name']}{RESET} Lv{row['level']} {row['race']} {row['sex']} from {row['nation']}")
    sj = f" / {row['sub_job']}" if row["sub_job"] else ""
    print(f"Job: {row['main_job']}{sj}    EXP: {row['exp']}    Location: {location['name']}")
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


def browse_locations(con: sqlite3.Connection) -> None:
    print(f"\n{BOLD}Locations{RESET}")
    for row in con.execute("SELECT * FROM maps ORDER BY region, name"):
        water = f" / {row['water_type']} water" if row["water_type"] else ""
        print(f"  - {row['name']} [{row['region']}{water}]")


def browse_npcs(con: sqlite3.Connection) -> None:
    print(f"\n{BOLD}NPCs{RESET}")
    for row in con.execute("SELECT n.name, m.name AS map_name, n.dialogue FROM npcs n JOIN maps m ON m.slug=n.map_slug ORDER BY m.name, n.name"):
        print(f"  - {row['name']} @ {row['map_name']}: \"{row['dialogue']}\"")


def browse_mobs(con: sqlite3.Connection) -> None:
    print(f"\n{BOLD}Mobs{RESET}")
    for row in con.execute("SELECT mobs.name, family, job, level, maps.name AS map_name FROM mobs LEFT JOIN maps ON maps.slug=mobs.map_slug ORDER BY maps.name, level, mobs.name"):
        job = f" {row['job']}" if row["job"] else ""
        where = row["map_name"] or "Unknown"
        print(f"  - Lv{row['level']} {row['name']} ({row['family']}{job}) @ {where}")


def browse_current_location(con: sqlite3.Connection, character_id: int) -> None:
    loc = current_location(con, character_id)
    water = f" / {loc['water_type']} water" if loc["water_type"] else ""
    print(f"\n{BOLD}{loc['name']}{RESET} [{loc['region']}{water}]")
    print("\nNPCs here:")
    npcs = con.execute("SELECT name, dialogue FROM npcs WHERE map_slug = ? ORDER BY name", (loc["slug"],)).fetchall()
    if not npcs:
        print("  - None spotted.")
    for npc in npcs:
        print(f"  - {npc['name']}: \"{npc['dialogue']}\"")
    print("\nMobs here:")
    mobs = con.execute("SELECT name, family, job, level FROM mobs WHERE map_slug = ? ORDER BY level, name", (loc["slug"],)).fetchall()
    if not mobs:
        print("  - No nearby hostile mobs recorded yet.")
    for mob in mobs:
        job = f" {mob['job']}" if mob["job"] else ""
        print(f"  - Lv{mob['level']} {mob['name']} ({mob['family']}{job})")
    print("\nGathering nodes:")
    nodes = con.execute("SELECT slug, kind FROM gathering_nodes WHERE map_slug = ? ORDER BY kind, slug", (loc["slug"],)).fetchall()
    if not nodes:
        print("  - None recorded.")
    for node in nodes:
        print(f"  - {node['kind']}: {node['slug']}")


def status_screen(con: sqlite3.Connection, character_id: int) -> None:
    row = con.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    loc = current_location(con, character_id)
    print(f"\n{BOLD}Character Status{RESET}")
    print(f"Name: {row['name']}")
    print(f"Race/Sex/Nation: {row['race']} / {row['sex']} / {row['nation']}")
    print(f"Jobs: {row['main_job']}" + (f" / {row['sub_job']}" if row['sub_job'] else ""))
    print(f"Level/EXP: {row['level']} / {row['exp']}")
    print(f"Location: {loc['name']} ({loc['region']})")
    print("Stats: " + "  ".join(f"{s.upper()} {row[s]}" for s in ["hp", "mp", "str", "dex", "vit", "agi", "int", "mnd", "chr"]))
    inv_count = con.execute("SELECT COALESCE(SUM(quantity), 0) AS c FROM inventory WHERE character_id = ?", (character_id,)).fetchone()["c"]
    print(f"Inventory items: {inv_count}")


def inventory_screen(con: sqlite3.Connection, character_id: int) -> None:
    print(f"\n{BOLD}Inventory{RESET}")
    rows = list_inventory(con, character_id)
    if not rows:
        print("  Empty. The goblin pockets are tragically bare.")
        return
    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        grouped.setdefault(row["kind"], []).append(row)
    for kind in sorted(grouped):
        print(f"\n{CYAN}{kind.title()}{RESET}")
        for item in grouped[kind]:
            equipped = f" [{item['equipped_slot']}]" if item["equipped_slot"] else ""
            print(f"  - {item['name']} x{item['quantity']}{equipped}")


def help_screen() -> None:
    print(f"\n{BOLD}Help{RESET}")
    print("Use number keys to select menu options.")
    print("Global commands: b = Back, h = Home, q = Quit.")
    print("Travel changes your current map. Combat and gathering now use that map.")
    print("Combat: attack is steady, cast spends MP, defend reduces incoming damage, flee can fail.")
    print("Fishing: reel builds progress and tension, wait is safer, slacken lowers tension.")


def travel_screen(con: sqlite3.Connection, character_id: int) -> None:
    regions = con.execute("SELECT region, COUNT(*) AS c FROM maps GROUP BY region ORDER BY region").fetchall()
    print(f"\n{BOLD}Travel{RESET}")
    print("Choose a region first:")
    for i, row in enumerate(regions, start=1):
        print(f"  {i}. {row['region']} ({row['c']} maps)")
    raw = input("Region number, or blank to cancel> ").strip()
    if not raw:
        print(f"{YELLOW}Travel cancelled.{RESET}")
        return
    if not raw.isdigit() or not (1 <= int(raw) <= len(regions)):
        print(f"{RED}Invalid region.{RESET}")
        return
    region = regions[int(raw) - 1]["region"]
    maps = con.execute("SELECT slug, name, region FROM maps WHERE region = ? ORDER BY name", (region,)).fetchall()
    print(f"\n{BOLD}{region}{RESET}")
    for i, row in enumerate(maps, start=1):
        print(f"  {i}. {row['name']}")
    raw = input("Destination number, or blank to cancel> ").strip()
    if not raw:
        print(f"{YELLOW}Travel cancelled.{RESET}")
        return
    if not raw.isdigit() or not (1 <= int(raw) <= len(maps)):
        print(f"{RED}Invalid destination.{RESET}")
        return
    dest = maps[int(raw) - 1]
    set_current_location(con, character_id, dest["slug"])
    print(f"{GREEN}Travelled to {dest['name']}.{RESET}")


def choose_local_mob(con: sqlite3.Connection, character_id: int) -> str | None:
    loc = current_location(con, character_id)
    mobs = con.execute("SELECT slug, name, level, job FROM mobs WHERE map_slug = ? ORDER BY level, name", (loc["slug"],)).fetchall()
    if not mobs:
        print(f"{YELLOW}No mobs recorded for {loc['name']} yet. Use World > Mobs to browse all known mobs.{RESET}")
        return None
    print(f"\n{BOLD}Mobs in {loc['name']}{RESET}")
    for i, mob in enumerate(mobs, start=1):
        job = f" {mob['job']}" if mob["job"] else ""
        print(f"  {i}. Lv{mob['level']} {mob['name']}{job}")
    raw = input("Fight which mob? Blank to cancel> ").strip()
    if not raw:
        print(f"{YELLOW}Combat cancelled.{RESET}")
        return None
    if not raw.isdigit() or not (1 <= int(raw) <= len(mobs)):
        print(f"{RED}Invalid target.{RESET}")
        return None
    return mobs[int(raw) - 1]["slug"]


def local_combat_screen(con: sqlite3.Connection, character_id: int) -> None:
    mob_slug = choose_local_mob(con, character_id)
    if mob_slug:
        combat_screen(con, character_id, mob_slug)


def choose_local_node(con: sqlite3.Connection, character_id: int) -> str | None:
    loc = current_location(con, character_id)
    nodes = con.execute("SELECT slug, kind FROM gathering_nodes WHERE map_slug = ? ORDER BY kind, slug", (loc["slug"],)).fetchall()
    if not nodes:
        print(f"{YELLOW}No gathering nodes recorded for {loc['name']} yet.{RESET}")
        return None
    print(f"\n{BOLD}Gathering in {loc['name']}{RESET}")
    for i, node in enumerate(nodes, start=1):
        print(f"  {i}. {node['kind']} - {node['slug']}")
    raw = input("Use which node? Blank to cancel> ").strip()
    if not raw:
        print(f"{YELLOW}Gathering cancelled.{RESET}")
        return None
    if not raw.isdigit() or not (1 <= int(raw) <= len(nodes)):
        print(f"{RED}Invalid node.{RESET}")
        return None
    return nodes[int(raw) - 1]["slug"]


def local_gathering_screen(con: sqlite3.Connection, character_id: int) -> None:
    node_slug = choose_local_node(con, character_id)
    if not node_slug:
        return
    node = con.execute("SELECT kind FROM gathering_nodes WHERE slug = ?", (node_slug,)).fetchone()
    if "fishing" in node["kind"]:
        fishing_screen(con, character_id, node_slug)
    else:
        print(f"{GREEN}Gathered:{RESET} {gather(con, character_id, node_slug)[0]}")


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
    def header() -> None:
        print(ART)
        show_character(con, character_id)

    def action(fn) -> None:
        try:
            fn()
        except Exception as exc:  # Keep console game resilient while prototyping.
            print(f"{RED}Error: {exc}{RESET}")
        pause()

    screens = {
        "main": Screen(
            "main",
            "Main Menu",
            [
                MenuOption("1", "World browser", target="world"),
                MenuOption("2", "Travel", lambda: action(lambda: travel_screen(con, character_id))),
                MenuOption("3", "Combat", target="combat"),
                MenuOption("4", "Gathering", target="gathering"),
                MenuOption("5", "Crafting", target="crafting"),
                MenuOption("6", "Inventory", lambda: action(lambda: inventory_screen(con, character_id))),
                MenuOption("7", "Status", lambda: action(lambda: status_screen(con, character_id))),
                MenuOption("?", "Help", lambda: action(help_screen)),
            ],
        ),
        "world": Screen(
            "world",
            "World Browser",
            [
                MenuOption("1", "Locations", lambda: action(lambda: browse_locations(con))),
                MenuOption("2", "NPCs", lambda: action(lambda: browse_npcs(con))),
                MenuOption("3", "Mobs", lambda: action(lambda: browse_mobs(con))),
                MenuOption("4", "Current location details", lambda: action(lambda: browse_current_location(con, character_id))),
                MenuOption("5", "Quests and missions", lambda: action(lambda: browse_world(con))),
            ],
        ),
        "combat": Screen(
            "combat",
            "Combat",
            [
                MenuOption("1", "Fight a local mob", lambda: action(lambda: local_combat_screen(con, character_id))),
                MenuOption("2", "Training: Yagudo Acolyte Lv5 WHM", lambda: action(lambda: combat_screen(con, character_id, "yagudo_acolyte_l5"))),
                MenuOption("3", "Training: Forest Hare Lv2", lambda: action(lambda: combat_screen(con, character_id, "forest_hare_l2"))),
            ],
        ),
        "gathering": Screen(
            "gathering",
            "Gathering & Fishing",
            [
                MenuOption("1", "Use local gathering/fishing node", lambda: action(lambda: local_gathering_screen(con, character_id))),
                MenuOption("2", "Training: mine copper in Bastok Mines", lambda: action(lambda: print(f"{GREEN}Gathered:{RESET} {gather(con, character_id, 'bastok_copper_vein')[0]}"))),
                MenuOption("3", "Training: fish freshwater pond", lambda: action(lambda: fishing_screen(con, character_id, "ronfaure_pond"))),
                MenuOption("4", "Training: fish saltwater coast", lambda: action(lambda: fishing_screen(con, character_id, "bastore_surf"))),
                MenuOption("5", "Training: ice fish at Qufim", lambda: action(lambda: fishing_screen(con, character_id, "qufim_ice_hole"))),
            ],
        ),
        "crafting": Screen(
            "crafting",
            "Crafting",
            [
                MenuOption("1", "Craft Bronze Ingot", lambda: action(lambda: print(f"{GREEN}Crafted Bronze Ingot!{RESET}" if craft(con, character_id, "smelt_bronze") else f"{RED}Need 3 Copper Ore.{RESET}"))),
            ],
        ),
    }

    nav = Navigator(screens)
    while nav.running:
        clear()
        header()
        nav.render()
        nav.handle(input("> "))


def main() -> None:
    con = ensure_db()
    clear()
    print(ART)
    character_id = character_select(con) or new_character(con)
    adventure_menu(con, character_id)


if __name__ == "__main__":
    main()
