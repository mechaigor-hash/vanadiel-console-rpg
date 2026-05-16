export const STATS = ["hp", "mp", "str", "dex", "vit", "agi", "int", "mnd", "chr"];

export const RACES = {
  Hume: { hp: 30, mp: 18, str: 7, dex: 7, vit: 7, agi: 7, int: 7, mnd: 7, chr: 7 },
  Elvaan: { hp: 34, mp: 15, str: 9, dex: 6, vit: 8, agi: 5, int: 5, mnd: 8, chr: 8 },
  Tarutaru: { hp: 24, mp: 30, str: 5, dex: 7, vit: 6, agi: 8, int: 10, mnd: 8, chr: 7 },
  Mithra: { hp: 31, mp: 17, str: 7, dex: 9, vit: 6, agi: 9, int: 7, mnd: 6, chr: 7 },
  Galka: { hp: 40, mp: 10, str: 9, dex: 7, vit: 10, agi: 6, int: 5, mnd: 6, chr: 6 },
};

export const NATIONS = {
  Bastok: { str: 1, vit: 1, start: "bastok_markets" },
  "San d'Oria": { mnd: 1, chr: 1, start: "southern_sandoria" },
  Windurst: { mp: 3, int: 1, start: "windurst_waters" },
};

export const JOBS = {
  Warrior: { hp: 12, mp: 0, str: 3, dex: 1, vit: 2, agi: 1, int: 0, mnd: 0, chr: 0 },
  Monk: { hp: 16, mp: 0, str: 2, dex: 2, vit: 3, agi: 1, int: 0, mnd: 1, chr: 0 },
  "White Mage": { hp: 6, mp: 14, str: 0, dex: 0, vit: 1, agi: 0, int: 1, mnd: 3, chr: 1 },
  "Black Mage": { hp: 5, mp: 16, str: 0, dex: 0, vit: 0, agi: 1, int: 4, mnd: 1, chr: 0 },
  "Red Mage": { hp: 8, mp: 10, str: 1, dex: 1, vit: 1, agi: 1, int: 2, mnd: 2, chr: 1 },
  Thief: { hp: 8, mp: 0, str: 1, dex: 3, vit: 1, agi: 3, int: 1, mnd: 0, chr: 1 },
};

export const STARTING_GEAR = {
  Warrior: ["Bronze Sword", "Bronze Harness"],
  Monk: ["Cesti", "Kenpogi"],
  "White Mage": ["Ash Staff", "Scroll of Cure"],
  "Black Mage": ["Willow Wand", "Scroll of Stone"],
  "Red Mage": ["Wax Sword", "Scroll of Dia"],
  Thief: ["Bronze Knife", "Bandit's Vest"],
};
