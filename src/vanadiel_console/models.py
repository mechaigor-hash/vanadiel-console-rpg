from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


STATS = ("hp", "mp", "str", "dex", "vit", "agi", "int", "mnd", "chr")

RACES: dict[str, dict[str, int]] = {
    "Hume": {"hp": 30, "mp": 18, "str": 7, "dex": 7, "vit": 7, "agi": 7, "int": 7, "mnd": 7, "chr": 7},
    "Elvaan": {"hp": 34, "mp": 15, "str": 9, "dex": 6, "vit": 8, "agi": 5, "int": 5, "mnd": 8, "chr": 8},
    "Tarutaru": {"hp": 24, "mp": 30, "str": 5, "dex": 7, "vit": 6, "agi": 8, "int": 10, "mnd": 8, "chr": 7},
    "Mithra": {"hp": 31, "mp": 17, "str": 7, "dex": 9, "vit": 6, "agi": 9, "int": 7, "mnd": 6, "chr": 7},
    "Galka": {"hp": 40, "mp": 10, "str": 9, "dex": 7, "vit": 10, "agi": 6, "int": 5, "mnd": 6, "chr": 6},
}

SEXES = ("Male", "Female")

NATIONS: dict[str, dict[str, int]] = {
    "Bastok": {"str": 1, "vit": 1},
    "San d'Oria": {"mnd": 1, "chr": 1},
    "Windurst": {"mp": 3, "int": 1},
}

JOBS: dict[str, dict[str, int]] = {
    "Warrior": {"hp": 12, "mp": 0, "str": 3, "dex": 1, "vit": 2, "agi": 1, "int": 0, "mnd": 0, "chr": 0},
    "Monk": {"hp": 16, "mp": 0, "str": 2, "dex": 2, "vit": 3, "agi": 1, "int": 0, "mnd": 1, "chr": 0},
    "White Mage": {"hp": 6, "mp": 14, "str": 0, "dex": 0, "vit": 1, "agi": 0, "int": 1, "mnd": 3, "chr": 1},
    "Black Mage": {"hp": 5, "mp": 16, "str": 0, "dex": 0, "vit": 0, "agi": 1, "int": 4, "mnd": 1, "chr": 0},
    "Red Mage": {"hp": 8, "mp": 10, "str": 1, "dex": 1, "vit": 1, "agi": 1, "int": 2, "mnd": 2, "chr": 1},
    "Thief": {"hp": 8, "mp": 0, "str": 1, "dex": 3, "vit": 1, "agi": 3, "int": 1, "mnd": 0, "chr": 1},
}

STARTING_GEAR = {
    "Warrior": ["Bronze Sword", "Bronze Harness"],
    "Monk": ["Cesti", "Kenpogi"],
    "White Mage": ["Ash Staff", "Scroll of Cure"],
    "Black Mage": ["Willow Wand", "Scroll of Stone"],
    "Red Mage": ["Wax Sword", "Scroll of Dia"],
    "Thief": ["Bronze Knife", "Bandit's Vest"],
}


@dataclass(frozen=True)
class CharacterBuild:
    name: str
    race: str
    sex: str
    nation: str
    main_job: str
    sub_job: str | None = None


def add_stats(*parts: Mapping[str, int]) -> dict[str, int]:
    total = {stat: 0 for stat in STATS}
    for part in parts:
        for stat in STATS:
            total[stat] += int(part.get(stat, 0))
    return total


def calculate_stats(build: CharacterBuild, level: int = 1) -> dict[str, int]:
    if build.race not in RACES:
        raise ValueError(f"Unknown race: {build.race}")
    if build.nation not in NATIONS:
        raise ValueError(f"Unknown nation: {build.nation}")
    if build.main_job not in JOBS:
        raise ValueError(f"Unknown main job: {build.main_job}")
    if build.sub_job and build.sub_job not in JOBS:
        raise ValueError(f"Unknown subjob: {build.sub_job}")

    sub = {k: v // 2 for k, v in JOBS[build.sub_job].items()} if build.sub_job else {}
    base = add_stats(RACES[build.race], NATIONS[build.nation], JOBS[build.main_job], sub)
    if level > 1:
        for stat in base:
            base[stat] += int((level - 1) * (2 if stat in {"hp", "mp"} else 1))
    return base
