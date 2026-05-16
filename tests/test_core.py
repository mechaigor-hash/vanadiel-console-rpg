from __future__ import annotations

from vanadiel_console.db import add_item, connect, create_character, init_db, list_inventory
from vanadiel_console.models import CharacterBuild, calculate_stats
from vanadiel_console.systems import craft, defeat_mob, fishing_nodes_for_water, gather


def memory_db():
    con = connect(":memory:")
    init_db(con)
    return con


def test_character_stats_are_affected_by_race_job_subjob_and_nation():
    taru_blm = CharacterBuild("Pip", "Tarutaru", "Female", "Windurst", "Black Mage", "White Mage")
    galka_war = CharacterBuild("Brog", "Galka", "Male", "Bastok", "Warrior", "Monk")
    assert calculate_stats(taru_blm)["mp"] > calculate_stats(galka_war)["mp"]
    assert calculate_stats(galka_war)["str"] > calculate_stats(taru_blm)["str"]


def test_create_character_writes_inventory_to_sqlite():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Mender", "Hume", "Female", "San d'Oria", "White Mage", None))
    names = {row["name"] for row in list_inventory(con, cid)}
    assert {"Ash Staff", "Scroll of Cure"}.issubset(names)


def test_weighted_yagudo_loot_contains_job_appropriate_table():
    con = memory_db()
    loot = con.execute("SELECT item_slug, weight FROM mob_loot WHERE mob_slug='yagudo_acolyte_l5'").fetchall()
    slugs = {row["item_slug"] for row in loot}
    assert "ash_staff" in slugs
    assert "scroll_cure" in slugs


def test_defeat_mob_grants_exp_and_possible_inventory_changes(monkeypatch):
    con = memory_db()
    cid = create_character(con, CharacterBuild("Fighter", "Elvaan", "Male", "Bastok", "Warrior", None))
    monkeypatch.setattr("random.randint", lambda a, b: 1)
    drops = defeat_mob(con, cid, "yagudo_acolyte_l5")
    assert drops
    exp = con.execute("SELECT exp FROM characters WHERE id=?", (cid,)).fetchone()["exp"]
    assert exp == 100


def test_gathering_fishing_water_types_and_crafting():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Crafter", "Hume", "Male", "Bastok", "Warrior", None))
    assert fishing_nodes_for_water(con, "fresh")
    assert fishing_nodes_for_water(con, "salt")
    assert fishing_nodes_for_water(con, "ice")
    gathered_slug, qty = gather(con, cid, "bastok_copper_vein")
    assert qty == 1
    assert gathered_slug in {"copper_ore", "beastcoin"}
    add_item(con, cid, "copper_ore", 3)
    assert craft(con, cid, "smelt_bronze") is True
    names = {row["slug"] for row in list_inventory(con, cid)}
    assert "bronze_ingot" in names
