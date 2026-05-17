from __future__ import annotations

from vanadiel_console.db import ContentValidationError, add_item, connect, create_character, current_location, equip_item, equipment_bonuses, equipped_items, init_db, list_inventory, load_content_pack, set_current_location, unequip_slot
from vanadiel_console.models import CharacterBuild, calculate_stats
from vanadiel_console.systems import accept_quest, apply_experience, auto_combat, available_quests, craft, defeat_mob, exp_to_next_level, fishing_attempt, fishing_nodes_for_water, gather, mark_quest_complete, missing_quest_prerequisites, quest_is_unlocked


def memory_db():
    con = connect(":memory:")
    init_db(con)
    return con


def test_core_content_pack_loads_from_json():
    content = load_content_pack()
    assert any(item["slug"] == "scroll_cure" for item in content["items"])
    assert any(mob["slug"] == "yagudo_acolyte_l5" for mob in content["mobs"])
    assert any(zone["slug"] == "jugner_forest_s" for zone in content["maps"])
    assert any(mob["slug"] == "campaign_orc_l72" for mob in content["mobs"])


def test_content_pack_validation_reports_bad_references(tmp_path):
    bad_pack = tmp_path / "bad_content.json"
    bad_pack.write_text(
        """{
          \"items\": [{\"slug\": \"copper_ore\", \"name\": \"Copper Ore\", \"kind\": \"material\"}],
          \"maps\": [{\"slug\": \"bastok_mines\", \"name\": \"Bastok Mines\", \"region\": \"Gustaberg\"}],
          \"npcs\": [{\"slug\": \"bad_npc\", \"name\": \"Bad NPC\", \"map_slug\": \"missing_map\"}],
          \"quests\": [{\"slug\": \"bad_quest\", \"title\": \"Bad Quest\", \"start_npc_slug\": \"missing_npc\", \"objectives\": [{\"type\": \"gather\", \"item\": \"missing_item\", \"count\": 1}]}],
          \"mobs\": [], \"loot\": [], \"recipes\": [], \"gathering\": []
        }""",
        encoding="utf-8",
    )
    try:
        load_content_pack(bad_pack)
    except ContentValidationError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected bad content pack to fail validation")
    assert "npcs:bad_npc references unknown map_slug missing_map" in message
    assert "quests:bad_quest references unknown start_npc_slug missing_npc" in message
    assert "quests:bad_quest gather objective references unknown item missing_item" in message


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
    assert current_location(con, cid)["slug"] == "southern_sandoria"


def test_inventory_rows_include_kind_for_grouped_ui():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Sorter", "Hume", "Male", "Bastok", "Warrior", None))
    rows = list_inventory(con, cid)
    kinds = {row["kind"] for row in rows}
    assert "weapon" in kinds
    assert "armor" in kinds


def test_equipment_flow_changes_derived_bonuses_and_inventory_slots():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Gearcheck", "Hume", "Male", "Bastok", "Warrior", None))
    assert equipment_bonuses(con, cid) == {"attack": 0, "defense": 0, "magic": 0}

    assert equip_item(con, cid, "bronze_sword") == "main"
    assert equip_item(con, cid, "bronze_harness") == "body"
    bonuses = equipment_bonuses(con, cid)
    assert bonuses["attack"] == 4
    assert bonuses["defense"] == 2
    slots = {row["equipped_slot"] for row in equipped_items(con, cid)}
    assert slots == {"main", "body"}

    unequip_slot(con, cid, "main")
    assert equipment_bonuses(con, cid)["attack"] == 0
    carried = {row["slug"]: row for row in list_inventory(con, cid) if row["equipped_slot"] is None}
    assert carried["bronze_sword"]["quantity"] == 1


def test_equipment_rejects_wrong_job_gear():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Mage", "Hume", "Female", "Windurst", "White Mage", None))
    add_item(con, cid, "bronze_sword", 1)
    try:
        equip_item(con, cid, "bronze_sword")
    except ValueError as exc:
        assert "cannot equip" in str(exc)
    else:
        raise AssertionError("Expected wrong-job equipment to be rejected")


def test_character_location_can_be_changed_for_travel():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Walker", "Hume", "Male", "Bastok", "Warrior", None))
    assert current_location(con, cid)["slug"] == "bastok_markets"
    set_current_location(con, cid, "west_ronfaure")
    assert current_location(con, cid)["name"] == "West Ronfaure"


def test_weighted_yagudo_loot_contains_job_appropriate_table():
    con = memory_db()
    loot = con.execute("SELECT item_slug, weight FROM mob_loot WHERE mob_slug='yagudo_acolyte_l5'").fetchall()
    slugs = {row["item_slug"] for row in loot}
    assert "ash_staff" in slugs
    assert "scroll_cure" in slugs


def test_expanded_era_content_seeds_locations_npcs_and_mobs():
    con = memory_db()
    counts = {
        "maps": con.execute("SELECT COUNT(*) AS c FROM maps").fetchone()["c"],
        "npcs": con.execute("SELECT COUNT(*) AS c FROM npcs").fetchone()["c"],
        "mobs": con.execute("SELECT COUNT(*) AS c FROM mobs").fetchone()["c"],
    }
    assert counts["maps"] >= 40
    assert counts["npcs"] >= 15
    assert counts["mobs"] >= 30
    wotg = con.execute("SELECT name FROM maps WHERE slug='southern_sandoria_s'").fetchone()
    assert wotg["name"] == "Southern San d'Oria (S)"


def test_quest_prerequisites_gate_followup_until_complete():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Questor", "Hume", "Female", "San d'Oria", "Warrior", None))
    available = {row["slug"] for row in available_quests(con, cid)}
    assert "first_steps" in available
    assert "gate_guard_followup" not in available
    assert missing_quest_prerequisites(con, cid, "gate_guard_followup") == ["first_steps"]
    assert quest_is_unlocked(con, cid, "gate_guard_followup") is False
    try:
        accept_quest(con, cid, "gate_guard_followup")
    except ValueError as exc:
        assert "first_steps" in str(exc)
    else:
        raise AssertionError("Expected locked follow-up quest to be rejected")

    mark_quest_complete(con, cid, "first_steps")
    assert quest_is_unlocked(con, cid, "gate_guard_followup") is True
    accept_quest(con, cid, "gate_guard_followup")
    active = con.execute("SELECT status FROM character_quests WHERE character_id=? AND quest_slug='gate_guard_followup'", (cid,)).fetchone()
    assert active["status"] == "active"


def test_experience_thresholds_level_character_and_refresh_stats():
    con = memory_db()
    cid = create_character(con, CharacterBuild("Leveler", "Hume", "Male", "Bastok", "Warrior", None))
    before = con.execute("SELECT level, exp, hp, str FROM characters WHERE id=?", (cid,)).fetchone()
    assert exp_to_next_level(before["level"]) == 100
    gained = apply_experience(con, cid, 100)
    after = con.execute("SELECT level, exp, hp, str FROM characters WHERE id=?", (cid,)).fetchone()
    assert gained == 1
    assert after["level"] == 2
    assert after["exp"] == 100
    assert after["hp"] > before["hp"]
    assert after["str"] > before["str"]


def test_combat_victory_can_trigger_level_up(monkeypatch):
    con = memory_db()
    cid = create_character(con, CharacterBuild("Bopper", "Hume", "Male", "Bastok", "Warrior", None))
    monkeypatch.setattr("random.randint", lambda a, b: 1)
    defeat_mob(con, cid, "yagudo_acolyte_l5")
    row = con.execute("SELECT level, exp FROM characters WHERE id=?", (cid,)).fetchone()
    assert row["level"] == 2
    assert row["exp"] == 100


def test_defeat_mob_grants_exp_and_possible_inventory_changes(monkeypatch):
    con = memory_db()
    cid = create_character(con, CharacterBuild("Fighter", "Elvaan", "Male", "Bastok", "Warrior", None))
    monkeypatch.setattr("random.randint", lambda a, b: 1)
    drops = defeat_mob(con, cid, "yagudo_acolyte_l5")
    assert drops
    exp = con.execute("SELECT exp FROM characters WHERE id=?", (cid,)).fetchone()["exp"]
    assert exp == 100


def test_interactive_combat_can_defeat_sample_mob(monkeypatch):
    con = memory_db()
    cid = create_character(con, CharacterBuild("Brawler", "Galka", "Male", "Bastok", "Warrior", "Monk"))
    monkeypatch.setattr("random.randint", lambda a, b: b)
    result = auto_combat(con, cid, "forest_hare_l2", ["attack", "attack", "attack", "attack"])
    assert result.victory is True
    assert result.exp == 40
    assert any("attacks" in line for line in result.log)


def test_interactive_fishing_can_award_fish(monkeypatch):
    con = memory_db()
    cid = create_character(con, CharacterBuild("Angler", "Hume", "Female", "Windurst", "Red Mage", None))
    monkeypatch.setattr("random.randint", lambda a, b: 30 if (a, b) == (18, 30) else a)
    success, fish_slug, log = fishing_attempt(con, cid, "ronfaure_pond", ["reel", "reel", "reel", "reel"])
    assert success is True
    assert fish_slug == "moat_carp"
    assert any("Caught" in line for line in log)
    names = {row["slug"] for row in list_inventory(con, cid)}
    assert "moat_carp" in names


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
