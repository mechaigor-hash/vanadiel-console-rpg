const STATS = ["hp", "mp", "str", "dex", "vit", "agi", "int", "mnd", "chr"];
const RACES = {
  Hume: { hp: 30, mp: 18, str: 7, dex: 7, vit: 7, agi: 7, int: 7, mnd: 7, chr: 7 },
  Elvaan: { hp: 34, mp: 15, str: 9, dex: 6, vit: 8, agi: 5, int: 5, mnd: 8, chr: 8 },
  Tarutaru: { hp: 24, mp: 30, str: 5, dex: 7, vit: 6, agi: 8, int: 10, mnd: 8, chr: 7 },
  Mithra: { hp: 31, mp: 17, str: 7, dex: 9, vit: 6, agi: 9, int: 7, mnd: 6, chr: 7 },
  Galka: { hp: 40, mp: 10, str: 9, dex: 7, vit: 10, agi: 6, int: 5, mnd: 6, chr: 6 },
};
const NATIONS = {
  Bastok: { str: 1, vit: 1, start: "bastok_markets" },
  "San d'Oria": { mnd: 1, chr: 1, start: "southern_sandoria" },
  Windurst: { mp: 3, int: 1, start: "windurst_waters" },
};
const JOBS = {
  Warrior: { hp: 12, mp: 0, str: 3, dex: 1, vit: 2, agi: 1, int: 0, mnd: 0, chr: 0 },
  Monk: { hp: 16, mp: 0, str: 2, dex: 2, vit: 3, agi: 1, int: 0, mnd: 1, chr: 0 },
  "White Mage": { hp: 6, mp: 14, str: 0, dex: 0, vit: 1, agi: 0, int: 1, mnd: 3, chr: 1 },
  "Black Mage": { hp: 5, mp: 16, str: 0, dex: 0, vit: 0, agi: 1, int: 4, mnd: 1, chr: 0 },
  "Red Mage": { hp: 8, mp: 10, str: 1, dex: 1, vit: 1, agi: 1, int: 2, mnd: 2, chr: 1 },
  Thief: { hp: 8, mp: 0, str: 1, dex: 3, vit: 1, agi: 3, int: 1, mnd: 0, chr: 1 },
};
const STARTING_GEAR = {
  Warrior: ["Bronze Sword", "Bronze Harness"], Monk: ["Cesti", "Kenpogi"],
  "White Mage": ["Ash Staff", "Scroll of Cure"], "Black Mage": ["Willow Wand", "Scroll of Stone"],
  "Red Mage": ["Wax Sword", "Scroll of Dia"], Thief: ["Bronze Knife", "Bandit's Vest"],
};

const els = {
  screen: document.querySelector("#screen"), title: document.querySelector("#screenTitle"),
  charName: document.querySelector("#charName"), charSummary: document.querySelector("#charSummary"),
  statGrid: document.querySelector("#statGrid"), logFeed: document.querySelector("#logFeed"),
};

let content;
let state = { screen: "world", character: null, inventory: [], combat: null, fishing: null };

const bySlug = (rows) => Object.fromEntries(rows.map((row) => [row.slug, row]));
const slugify = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
const roll = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const addLog = (text) => {
  const div = document.createElement("div");
  div.className = "log-entry";
  div.textContent = text;
  els.logFeed.prepend(div);
};
const setScreen = (screen) => { state.screen = screen; document.querySelectorAll("[data-screen]").forEach(b => b.classList.toggle("active", b.dataset.screen === screen)); render(); };

function addStats(...parts) {
  const total = Object.fromEntries(STATS.map((s) => [s, 0]));
  for (const part of parts) for (const stat of STATS) total[stat] += part?.[stat] ?? 0;
  return total;
}

function makeCharacter(form) {
  const main = form.mainJob.value;
  const sub = form.subJob.value === "None" ? null : form.subJob.value;
  const subStats = sub ? Object.fromEntries(Object.entries(JOBS[sub]).map(([k, v]) => [k, Math.floor(v / 2)])) : {};
  const stats = addStats(RACES[form.race.value], NATIONS[form.nation.value], JOBS[main], subStats);
  return {
    name: form.name.value || "Adventurer", race: form.race.value, sex: form.sex.value,
    nation: form.nation.value, mainJob: main, subJob: sub, level: 1, exp: 0,
    currentMap: NATIONS[form.nation.value].start, stats, hp: stats.hp, mp: stats.mp,
  };
}

function addItem(name, qty = 1) {
  const item = content.items.find((i) => i.name === name || i.slug === name) ?? { slug: slugify(name), name, kind: "misc" };
  const existing = state.inventory.find((i) => i.slug === item.slug);
  if (existing) existing.qty += qty;
  else state.inventory.push({ ...item, qty });
}

function save() {
  localStorage.setItem("vanadielWebSave", JSON.stringify({ character: state.character, inventory: state.inventory }));
  addLog("Game saved to browser local storage.");
}
function load() {
  const raw = localStorage.getItem("vanadielWebSave");
  if (!raw) return addLog("No browser save found.");
  const save = JSON.parse(raw);
  state.character = save.character; state.inventory = save.inventory ?? [];
  addLog("Game loaded."); render();
}

function openCreator() {
  const template = document.querySelector("#characterCreatorTemplate");
  const node = template.content.cloneNode(true);
  document.body.append(node);
  const form = document.querySelector("#characterForm");
  fillSelect(form.race, Object.keys(RACES)); fillSelect(form.sex, ["Male", "Female"]);
  fillSelect(form.nation, Object.keys(NATIONS)); fillSelect(form.mainJob, Object.keys(JOBS)); fillSelect(form.subJob, ["None", ...Object.keys(JOBS)]);
  document.querySelector("#cancelCreate").addEventListener("click", () => document.querySelector(".modal-backdrop").remove());
  form.addEventListener("submit", (event) => {
    event.preventDefault(); state.character = makeCharacter(form); state.inventory = [];
    STARTING_GEAR[state.character.mainJob].forEach((item) => addItem(item));
    document.querySelector(".modal-backdrop").remove(); addLog(`${state.character.name} begins in ${mapName(state.character.currentMap)}.`); render();
  });
}
function fillSelect(select, values) { select.innerHTML = values.map((v) => `<option>${v}</option>`).join(""); }

function mapName(slug) { return content.mapBySlug[slug]?.name ?? slug; }
function currentMap() { return content.mapBySlug[state.character?.currentMap] ?? content.maps[0]; }
function localMobs() { return content.mobs.filter((mob) => mob.map_slug === state.character?.currentMap); }
function localNodes() { return content.gathering.filter((node) => node.map_slug === state.character?.currentMap); }

function renderCharacter() {
  const c = state.character;
  if (!c) { els.charName.textContent = "No Character"; els.charSummary.textContent = "Create a character to begin."; els.statGrid.innerHTML = ""; return; }
  els.charName.textContent = c.name;
  els.charSummary.textContent = `Lv${c.level} ${c.race} ${c.mainJob}${c.subJob ? "/" + c.subJob : ""} • ${mapName(c.currentMap)}`;
  els.statGrid.innerHTML = STATS.map((s) => `<div class="stat"><span>${s.toUpperCase()}</span>${c.stats[s]}</div>`).join("");
}

function card(title, body, badges = [], action = "") {
  return `<article class="card"><h3>${title}</h3><p>${body}</p><div class="badges">${badges.map(b => `<span class="badge">${b}</span>`).join("")}</div>${action}</article>`;
}

function renderWorld() {
  const map = state.character ? currentMap() : content.maps[0];
  const npcs = content.npcs.filter((n) => n.map_slug === map.slug);
  els.title.textContent = "World";
  els.screen.innerHTML = `
    <h2>${map.name}</h2><p>${map.region}${map.water_type ? ` • ${map.water_type} water` : ""}</p>
    <div class="card-grid">
      ${card("NPCs here", npcs.length ? npcs.map(n => n.name).join(", ") : "No NPCs seeded for this map yet.", ["dialogue"])}
      ${card("Mobs here", localMobs().length ? localMobs().map(m => `Lv${m.level} ${m.name}`).join(", ") : "No mobs seeded for this map yet.", ["encounters"])}
      ${card("Nodes here", localNodes().length ? localNodes().map(n => n.kind).join(", ") : "No gathering nodes seeded for this map yet.", ["gathering"])}
    </div>`;
}

function renderTravel() {
  els.title.textContent = "Travel";
  const regions = [...new Set(content.maps.map((m) => m.region))].sort();
  els.screen.innerHTML = regions.map((region) => `<h2>${region}</h2><div class="card-grid">${content.maps.filter(m => m.region === region).map(m => card(m.name, m.water_type ? `${m.water_type} water` : "No water", [m.slug], `<button data-travel="${m.slug}">Travel</button>`)).join("")}</div>`).join("");
  els.screen.querySelectorAll("[data-travel]").forEach((btn) => btn.addEventListener("click", () => { if (!state.character) return addLog("Create a character first."); state.character.currentMap = btn.dataset.travel; addLog(`Travelled to ${mapName(btn.dataset.travel)}.`); render(); }));
}

function startCombat(mob) { state.combat = { mob: structuredClone(mob), hp: mob.stats?.hp ?? 20 + mob.level * 6, mp: mob.stats?.mp ?? 0 }; addLog(`A ${mob.name} attacks!`); renderCombat(); }
function playerDamage() { return Math.max(1, state.character.stats.str + Math.floor(state.character.stats.dex / 2) + roll(0, 3) - 4); }
function mobDamage() { return Math.max(1, (state.combat.mob.stats?.str ?? 5 + state.combat.mob.level) + roll(0, 3) - Math.floor(state.character.stats.vit / 2)); }
function combatAction(action) {
  if (!state.combat) return;
  if (action === "attack") { const dmg = playerDamage(); state.combat.hp -= dmg; addLog(`You hit ${state.combat.mob.name} for ${dmg}.`); }
  if (action === "cast") { if (state.character.mp < 4) addLog("Not enough MP."); else { state.character.mp -= 4; const dmg = Math.max(2, Math.floor(state.character.stats.int / 2) + roll(1, 6)); state.combat.hp -= dmg; addLog(`You cast for ${dmg}.`); } }
  if (action === "defend") addLog("You brace for impact.");
  if (action === "flee") { if (roll(1, 100) <= 55) { addLog("You escaped."); state.combat = null; return render(); } addLog("Couldn't escape!"); }
  if (state.combat.hp <= 0) { state.character.exp += state.combat.mob.level * 20; addLog(`${state.combat.mob.name} defeated! EXP +${state.combat.mob.level * 20}.`); state.combat = null; return render(); }
  const incoming = action === "defend" ? Math.max(1, Math.floor(mobDamage() / 2)) : mobDamage(); state.character.hp -= incoming; addLog(`${state.combat.mob.name} hits you for ${incoming}.`);
  if (state.character.hp <= 0) { addLog("You were knocked out and restored to 1 HP."); state.character.hp = 1; state.combat = null; }
  render();
}
function renderCombat() {
  els.title.textContent = "Combat";
  if (state.combat) {
    els.screen.innerHTML = `<h2>${state.combat.mob.name}</h2><p>Enemy HP ${Math.max(0, state.combat.hp)} • Your HP ${state.character.hp} MP ${state.character.mp}</p><div class="top-actions"><button data-action="attack">Attack</button><button data-action="cast">Cast</button><button data-action="defend">Defend</button><button data-action="flee">Flee</button></div>`;
    els.screen.querySelectorAll("[data-action]").forEach(b => b.addEventListener("click", () => combatAction(b.dataset.action)));
    return;
  }
  const mobs = state.character ? localMobs() : [];
  els.screen.innerHTML = mobs.length ? `<div class="card-grid">${mobs.map(m => card(m.name, `Lv${m.level} ${m.family}${m.job ? " / " + m.job : ""}`, [mapName(m.map_slug)], `<button data-fight="${m.slug}">Fight</button>`)).join("")}</div>` : `<p>No local mobs. Travel to a field zone.</p>`;
  els.screen.querySelectorAll("[data-fight]").forEach(b => b.addEventListener("click", () => startCombat(content.mobBySlug[b.dataset.fight])));
}

function renderGathering() {
  els.title.textContent = "Gathering";
  const nodes = state.character ? localNodes() : [];
  els.screen.innerHTML = nodes.length ? `<div class="card-grid">${nodes.map(n => card(n.slug, `Kind: ${n.kind}`, [mapName(n.map_slug)], `<button data-node="${n.slug}">Use Node</button>`)).join("")}</div>` : `<p>No local gathering nodes. Travel to a zone with fishing/mining.</p>`;
  els.screen.querySelectorAll("[data-node]").forEach(b => b.addEventListener("click", () => useNode(content.nodeBySlug[b.dataset.node])));
}
function useNode(node) {
  const loot = weighted(node.loot_table.map((x) => [x.item, x.weight]));
  addItem(loot); addLog(`${node.kind.includes("fishing") ? "Caught" : "Gathered"} ${content.itemBySlug[loot]?.name ?? loot}.`); render();
}
function weighted(rows) { const total = rows.reduce((a, [, w]) => a + w, 0); let pick = roll(1, total); for (const [slug, weight] of rows) { pick -= weight; if (pick <= 0) return slug; } return rows[0][0]; }

function renderInventory() {
  els.title.textContent = "Inventory";
  if (!state.inventory.length) { els.screen.innerHTML = "<p>No items yet.</p>"; return; }
  const kinds = [...new Set(state.inventory.map((i) => i.kind))].sort();
  els.screen.innerHTML = kinds.map(k => `<h2>${k}</h2><div class="card-grid">${state.inventory.filter(i => i.kind === k).map(i => card(i.name, `Quantity: ${i.qty}`, [i.slug])).join("")}</div>`).join("");
}

function renderContent() {
  els.title.textContent = "Database";
  els.screen.innerHTML = `<div class="card-grid">
    ${card("Maps", `${content.maps.length} seeded locations`, ["75 era", "WotG"])}
    ${card("NPCs", `${content.npcs.length} seeded NPCs`, ["dialogue"])}
    ${card("Mobs", `${content.mobs.length} seeded mobs`, ["levels", "jobs"])}
    ${card("Items", `${content.items.length} seeded items`, ["loot", "gear"])}
  </div>`;
}

function render() {
  renderCharacter();
  if (!state.character && state.screen !== "content") els.screen.innerHTML = `<p>Create a character to begin.</p>`;
  const routes = { world: renderWorld, travel: renderTravel, combat: renderCombat, gathering: renderGathering, inventory: renderInventory, content: renderContent };
  (routes[state.screen] ?? renderWorld)();
}

async function boot() {
  content = await fetch("core_content.json").then((r) => r.json());
  content.mapBySlug = bySlug(content.maps); content.mobBySlug = bySlug(content.mobs); content.itemBySlug = bySlug(content.items); content.nodeBySlug = bySlug(content.gathering);
  document.querySelector("#newGameBtn").addEventListener("click", openCreator);
  document.querySelector("#saveBtn").addEventListener("click", save);
  document.querySelector("#loadBtn").addEventListener("click", load);
  document.querySelectorAll("[data-screen]").forEach((btn) => btn.addEventListener("click", () => setScreen(btn.dataset.screen)));
  addLog("Web engine loaded. HTML/CSS/JS shell online."); render();
}
boot();
