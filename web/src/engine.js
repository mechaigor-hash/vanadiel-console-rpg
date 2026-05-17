import { AssetManager, defaultManifest } from "./engine/assets.js";
import { loadContentPack } from "./engine/content.js";
import { JOBS, NATIONS, RACES, STARTING_GEAR, STATS } from "./engine/constants.js";
import { loadGame, saveGame, state } from "./engine/state.js";
import { addStats, card, roll, slugify, weighted } from "./engine/utils.js";

const els = {
  screen: document.querySelector("#screen"),
  title: document.querySelector("#screenTitle"),
  charName: document.querySelector("#charName"),
  charSummary: document.querySelector("#charSummary"),
  statGrid: document.querySelector("#statGrid"),
  logFeed: document.querySelector("#logFeed"),
};

let content;
let assets;

const addLog = (text) => {
  const div = document.createElement("div");
  div.className = "log-entry";
  div.textContent = text;
  els.logFeed.prepend(div);
};

const setScreen = (screen) => {
  state.screen = screen;
  if (screen !== "gathering") state.fishing = null;
  document.querySelectorAll("[data-screen]").forEach((b) => b.classList.toggle("active", b.dataset.screen === screen));
  render();
};

function makeCharacter(form) {
  const main = form.mainJob.value;
  const sub = form.subJob.value === "None" ? null : form.subJob.value;
  const subStats = sub ? Object.fromEntries(Object.entries(JOBS[sub]).map(([k, v]) => [k, Math.floor(v / 2)])) : {};
  const stats = addStats(STATS, RACES[form.race.value], NATIONS[form.nation.value], JOBS[main], subStats);
  return {
    name: form.name.value || "Adventurer",
    race: form.race.value,
    sex: form.sex.value,
    nation: form.nation.value,
    mainJob: main,
    subJob: sub,
    level: 1,
    exp: 0,
    gil: 0,
    currentMap: NATIONS[form.nation.value].start,
    stats,
    hp: stats.hp,
    mp: stats.mp,
  };
}

function addItem(name, qty = 1) {
  const item = content.items.find((i) => i.name === name || i.slug === name) ?? { slug: slugify(name), name, kind: "misc" };
  const existing = state.inventory.find((i) => i.slug === item.slug);
  if (existing) existing.qty += qty;
  else state.inventory.push({ ...item, qty });
}

function save() {
  saveGame();
  addLog("Game saved to browser local storage.");
  assets.play("ui_confirm");
}

function load() {
  if (!loadGame()) return addLog("No browser save found.");
  addLog("Game loaded.");
  render();
}

function openCreator() {
  const template = document.querySelector("#characterCreatorTemplate");
  const node = template.content.cloneNode(true);
  document.body.append(node);
  const form = document.querySelector("#characterForm");
  fillSelect(form.race, Object.keys(RACES));
  fillSelect(form.sex, ["Male", "Female"]);
  fillSelect(form.nation, Object.keys(NATIONS));
  fillSelect(form.mainJob, Object.keys(JOBS));
  fillSelect(form.subJob, ["None", ...Object.keys(JOBS)]);
  document.querySelector("#cancelCreate").addEventListener("click", () => document.querySelector(".modal-backdrop").remove());
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    state.character = makeCharacter(form);
    state.inventory = [];
    state.equipment = {};
    state.activeQuests = [];
    state.completedQuests = [];
    state.questProgress = {};
    STARTING_GEAR[state.character.mainJob].forEach((item) => addItem(item));
    document.querySelector(".modal-backdrop").remove();
    addLog(`${state.character.name} begins in ${mapName(state.character.currentMap)}.`);
    assets.play("ui_confirm");
    render();
  });
}

function fillSelect(select, values) {
  select.innerHTML = values.map((v) => `<option>${v}</option>`).join("");
}

function mapName(slug) { return content.mapBySlug[slug]?.name ?? slug; }
function currentMap() { return content.mapBySlug[state.character?.currentMap] ?? content.maps[0]; }
function localMobs() { return content.mobs.filter((mob) => mob.map_slug === state.character?.currentMap); }
function localNodes() { return content.gathering.filter((node) => node.map_slug === state.character?.currentMap); }
function localNpcs() { return content.npcs.filter((npc) => npc.map_slug === state.character?.currentMap); }

function renderCharacter() {
  const c = state.character;
  if (!c) {
    els.charName.textContent = "No Character";
    els.charSummary.textContent = "Create a character to begin.";
    els.statGrid.innerHTML = "";
    return;
  }
  els.charName.textContent = c.name;
  els.charSummary.textContent = `Lv${c.level} ${c.race} ${c.mainJob}${c.subJob ? "/" + c.subJob : ""} • ${mapName(c.currentMap)} • ${c.gil ?? 0} gil`;
  els.statGrid.innerHTML = STATS.map((s) => `<div class="stat"><span>${s.toUpperCase()}</span>${c.stats[s]}</div>`).join("");
}

function renderWorld() {
  const map = state.character ? currentMap() : content.maps[0];
  const npcs = localNpcs();
  els.title.textContent = "World";
  els.screen.innerHTML = `
    <div class="hero-art" style="--art: url('assets/images/map-placeholder.svg')"></div>
    <h2>${map.name}</h2><p>${map.region}${map.water_type ? ` • ${map.water_type} water` : ""}</p>
    <div class="card-grid">
      ${card("NPCs here", npcs.length ? npcs.map((n) => n.name).join(", ") : "No NPCs seeded for this map yet.", ["dialogue"], npcs.length ? `<button data-open-npcs>Talk</button>` : "")}
      ${card("Mobs here", localMobs().length ? localMobs().map((m) => `Lv${m.level} ${m.name}`).join(", ") : "No mobs seeded for this map yet.", ["encounters"])}
      ${card("Nodes here", localNodes().length ? localNodes().map((n) => n.kind).join(", ") : "No gathering nodes seeded for this map yet.", ["gathering"])}
    </div>`;
  els.screen.querySelectorAll("[data-open-npcs]").forEach((b) => b.addEventListener("click", () => setScreen("npcs")));
}

function questObjectiveKey(objective) {
  if (objective.type === "defeat") return `defeat:${objective.mob_family}`;
  if (objective.type === "gather") return `gather:${objective.item}`;
  return `${objective.type}:${objective.item ?? objective.mob_family ?? "any"}`;
}

function questProgress(slug, objective) {
  return state.questProgress[slug]?.[questObjectiveKey(objective)] ?? 0;
}

function updateQuestProgress(kind, value, qty = 1) {
  for (const slug of state.activeQuests) {
    if (state.completedQuests.includes(slug)) continue;
    const quest = content.questBySlug[slug];
    let changed = false;
    for (const objective of quest.objectives ?? []) {
      const matchesDefeat = kind === "defeat" && objective.type === "defeat" && objective.mob_family === value;
      const matchesGather = kind === "gather" && objective.type === "gather" && objective.item === value;
      if (!matchesDefeat && !matchesGather) continue;
      state.questProgress[slug] ??= {};
      const key = questObjectiveKey(objective);
      const next = Math.min(objective.count ?? 1, (state.questProgress[slug][key] ?? 0) + qty);
      state.questProgress[slug][key] = next;
      changed = true;
    }
    if (changed && isQuestReady(quest)) addLog(`Quest objective complete: ${quest.title}. Return to the quest NPC.`);
  }
}

function isQuestReady(quest) {
  return (quest.objectives ?? []).every((objective) => questProgress(quest.slug, objective) >= (objective.count ?? 1));
}

function questProgressText(quest) {
  return (quest.objectives ?? []).map((objective) => `${questProgress(quest.slug, objective)}/${objective.count ?? 1}`).join(", ");
}

function completeQuest(slug) {
  const quest = content.questBySlug[slug];
  if (!isQuestReady(quest)) return addLog(`${quest.title} is not ready to complete yet.`);
  state.completedQuests.push(slug);
  state.activeQuests = state.activeQuests.filter((activeSlug) => activeSlug !== slug);
  state.character.gil = (state.character.gil ?? 0) + (quest.rewards?.gil ?? 0);
  for (const [itemSlug, qty] of Object.entries(quest.rewards?.items ?? {})) addItem(itemSlug, qty);
  addLog(`Completed quest: ${quest.title}.`);
  assets.play("ui_confirm");
  if (state.screen === "quests") renderQuestJournal();
  else renderNPCs();
}

function questSummary(quest) {
  const objectiveText = (quest.objectives ?? []).map((objective) => {
    if (objective.type === "defeat") return `Defeat ${objective.count} ${objective.mob_family}`;
    if (objective.type === "gather") return `Gather ${objective.count} ${content.itemBySlug[objective.item]?.name ?? objective.item}`;
    return `${objective.type}: ${objective.count ?? 1}`;
  }).join(", ");
  const rewardBits = [];
  if (quest.rewards?.gil) rewardBits.push(`${quest.rewards.gil} gil`);
  for (const [slug, qty] of Object.entries(quest.rewards?.items ?? {})) rewardBits.push(`${qty} ${content.itemBySlug[slug]?.name ?? slug}`);
  return `${objectiveText || "Speak with locals"}${rewardBits.length ? ` • Rewards: ${rewardBits.join(", ")}` : ""}`;
}

function questCard(quest, status) {
  const active = status === "active";
  const done = status === "complete";
  const ready = active && isQuestReady(quest);
  const startNpc = content.npcBySlug[quest.start_npc_slug];
  const badges = [quest.quest_type ?? "quest", done ? "complete" : ready ? "ready" : active ? "active" : "available"];
  const lines = [
    questSummary(quest),
    startNpc ? `Start: ${startNpc.name} in ${mapName(startNpc.map_slug)}` : "Start NPC unknown",
    active ? `Progress: ${questProgressText(quest)}` : "",
    ready ? "Ready to turn in." : "",
  ].filter(Boolean).join("<br>");
  const action = ready ? `<button data-complete-quest="${quest.slug}">Complete Quest</button>` : "";
  return card(quest.title, lines, badges, action);
}

function renderQuestJournal() {
  els.title.textContent = "Quest Journal";
  if (!state.character) { els.screen.innerHTML = `<p>Create a character to begin tracking quests.</p>`; return; }
  const active = state.activeQuests.map((slug) => content.questBySlug[slug]).filter(Boolean);
  const completed = state.completedQuests.map((slug) => content.questBySlug[slug]).filter(Boolean);
  const available = (content.quests ?? []).filter((quest) => !state.activeQuests.includes(quest.slug) && !state.completedQuests.includes(quest.slug));
  els.screen.innerHTML = `
    <div class="hero-art" style="--art: url('assets/images/map-placeholder.svg')"></div>
    <h2>Active Quests</h2>
    ${active.length ? `<div class="card-grid">${active.map((quest) => questCard(quest, "active")).join("")}</div>` : `<p>No active quests. Talk to local NPCs to accept work.</p>`}
    <h2>Completed Quests</h2>
    ${completed.length ? `<div class="card-grid">${completed.map((quest) => questCard(quest, "complete")).join("")}</div>` : `<p>No completed quests yet.</p>`}
    <h2>Available Leads</h2>
    ${available.length ? `<div class="card-grid">${available.map((quest) => questCard(quest, "available")).join("")}</div>` : `<p>No available quest leads left in this seed slice.</p>`}`;
  els.screen.querySelectorAll("[data-complete-quest]").forEach((b) => b.addEventListener("click", () => completeQuest(b.dataset.completeQuest)));
}

function acceptQuest(slug) {
  if (!state.character) return addLog("Create a character first.");
  if (state.completedQuests.includes(slug)) return addLog("That quest is already complete.");
  if (state.activeQuests.includes(slug)) return addLog("That quest is already in your journal.");
  const quest = content.questBySlug[slug];
  state.activeQuests.push(slug);
  state.questProgress[slug] = {};
  addLog(`Accepted quest: ${quest.title}.`);
  assets.play("ui_confirm");
  if (state.screen === "quests") renderQuestJournal();
  else renderNPCs();
}

function renderNPCs() {
  els.title.textContent = "NPCs";
  const npcs = state.character ? localNpcs() : [];
  if (!npcs.length) { els.screen.innerHTML = `<p>No local NPCs. Travel to a city or outpost.</p>`; return; }
  els.screen.innerHTML = `<div class="hero-art" style="--art: url('assets/images/map-placeholder.svg')"></div><div class="card-grid">${npcs.map((npc) => {
    const quests = content.questsByStartNpc[npc.slug] ?? [];
    const questActions = quests.map((quest) => {
      const active = state.activeQuests.includes(quest.slug);
      const done = state.completedQuests.includes(quest.slug);
      const ready = active && isQuestReady(quest);
      const label = done ? "Complete" : ready ? "Complete Quest" : active ? "In Journal" : "Accept Quest";
      const progress = active ? `<p class="quest-progress">Progress: ${questProgressText(quest)}</p>` : "";
      return `<div class="quest-callout"><strong>${quest.title}</strong><p>${questSummary(quest)}</p>${progress}<button data-quest="${quest.slug}" ${done || (active && !ready) ? "disabled" : ""}>${label}</button></div>`;
    }).join("");
    return card(npc.name, npc.dialogue ?? "They have nothing to say yet.", [mapName(npc.map_slug), quests.length ? "quest" : "dialogue"], questActions || `<button data-talk="${npc.slug}">Talk</button>`);
  }).join("")}</div>`;
  els.screen.querySelectorAll("[data-talk]").forEach((b) => b.addEventListener("click", () => { addLog(`${content.npcBySlug[b.dataset.talk].name}: ${content.npcBySlug[b.dataset.talk].dialogue}`); assets.play("ui_confirm"); }));
  els.screen.querySelectorAll("[data-quest]").forEach((b) => b.addEventListener("click", () => {
    const slug = b.dataset.quest;
    if (state.activeQuests.includes(slug) && isQuestReady(content.questBySlug[slug])) completeQuest(slug);
    else acceptQuest(slug);
  }));
}

function renderTravel() {
  els.title.textContent = "Travel";
  const regions = [...new Set(content.maps.map((m) => m.region))].sort();
  els.screen.innerHTML = regions.map((region) => `<h2>${region}</h2><div class="card-grid">${content.maps.filter((m) => m.region === region).map((m) => card(m.name, m.water_type ? `${m.water_type} water` : "No water", [m.slug], `<button data-travel="${m.slug}">Travel</button>`)).join("")}</div>`).join("");
  els.screen.querySelectorAll("[data-travel]").forEach((btn) => btn.addEventListener("click", () => {
    if (!state.character) return addLog("Create a character first.");
    state.character.currentMap = btn.dataset.travel;
    addLog(`Travelled to ${mapName(btn.dataset.travel)}.`);
    assets.play("ui_confirm");
    render();
  }));
}

function startCombat(mob) {
  state.combat = { mob: structuredClone(mob), hp: mob.stats?.hp ?? 20 + mob.level * 6, mp: mob.stats?.mp ?? 0 };
  addLog(`A ${mob.name} attacks!`);
  renderCombat();
}
function playerDamage() { return Math.max(1, state.character.stats.str + Math.floor(state.character.stats.dex / 2) + gearAttackBonus() + roll(0, 3) - 4); }
function mobDamage() { return Math.max(1, (state.combat.mob.stats?.str ?? 5 + state.combat.mob.level) + roll(0, 3) - Math.floor((state.character.stats.vit + gearDefenseBonus()) / 2)); }
function combatAction(action) {
  if (!state.combat) return;
  if (action === "attack") { const dmg = playerDamage(); state.combat.hp -= dmg; addLog(`You hit ${state.combat.mob.name} for ${dmg}.`); assets.play("combat_hit"); }
  if (action === "cast") {
    if (state.character.mp < 4) addLog("Not enough MP.");
    else { state.character.mp -= 4; const dmg = Math.max(2, Math.floor(state.character.stats.int / 2) + roll(1, 6)); state.combat.hp -= dmg; addLog(`You cast for ${dmg}.`); assets.play("spell_cast"); }
  }
  if (action === "defend") addLog("You brace for impact.");
  if (action === "flee") { if (roll(1, 100) <= 55) { addLog("You escaped."); assets.play("ui_cancel"); state.combat = null; return render(); } addLog("Couldn't escape!"); }
  if (state.combat.hp <= 0) { state.character.exp += state.combat.mob.level * 20; updateQuestProgress("defeat", state.combat.mob.family); addLog(`${state.combat.mob.name} defeated! EXP +${state.combat.mob.level * 20}.`); state.combat = null; return render(); }
  const incoming = action === "defend" ? Math.max(1, Math.floor(mobDamage() / 2)) : mobDamage();
  state.character.hp -= incoming;
  addLog(`${state.combat.mob.name} hits you for ${incoming}.`);
  if (state.character.hp <= 0) { addLog("You were knocked out and restored to 1 HP."); state.character.hp = 1; state.combat = null; }
  render();
}
function renderCombat() {
  els.title.textContent = "Combat";
  if (state.combat) {
    const enemyMax = state.combat.mob.stats?.hp ?? 20 + state.combat.mob.level * 6;
    els.screen.innerHTML = `
      <div class="hero-art" style="--art: url('assets/images/combat-placeholder.svg')"></div>
      <div class="hud-row">
        <div class="hud-box"><strong>${state.character.name}</strong>HP ${state.character.hp}/${state.character.stats.hp} • MP ${state.character.mp}/${state.character.stats.mp}<div class="bar"><span style="--value:${Math.max(1, (state.character.hp / state.character.stats.hp) * 100)}%"></span></div></div>
        <div class="hud-box"><strong>${state.combat.mob.name}</strong>HP ${Math.max(0, state.combat.hp)}/${enemyMax}<div class="bar enemy"><span style="--value:${Math.max(1, (state.combat.hp / enemyMax) * 100)}%"></span></div></div>
      </div>
      <div class="top-actions"><button data-action="attack">Attack</button><button data-action="cast">Cast</button><button data-action="defend">Defend</button><button data-action="flee">Flee</button></div>`;
    els.screen.querySelectorAll("[data-action]").forEach((b) => b.addEventListener("click", () => combatAction(b.dataset.action)));
    return;
  }
  const mobs = state.character ? localMobs() : [];
  els.screen.innerHTML = `<div class="hero-art" style="--art: url('assets/images/combat-placeholder.svg')"></div>` + (mobs.length ? `<div class="card-grid">${mobs.map((m) => card(m.name, `Lv${m.level} ${m.family}${m.job ? " / " + m.job : ""}`, [mapName(m.map_slug)], `<button data-fight="${m.slug}">Fight</button>`)).join("")}</div>` : `<p>No local mobs. Travel to a field zone.</p>`);
  els.screen.querySelectorAll("[data-fight]").forEach((b) => b.addEventListener("click", () => startCombat(content.mobBySlug[b.dataset.fight])));
}

function renderGathering() {
  els.title.textContent = "Gathering";
  if (state.fishing) return renderFishing();
  const nodes = state.character ? localNodes() : [];
  els.screen.innerHTML = `<div class="hero-art" style="--art: url('assets/images/gathering-placeholder.svg')"></div>` + (nodes.length ? `<div class="card-grid">${nodes.map((n) => {
    const isFishing = n.kind.includes("fishing");
    return card(n.slug, `Kind: ${n.kind}`, [mapName(n.map_slug), isFishing ? "reel mini-game" : "quick gather"], `<button data-node="${n.slug}">${isFishing ? "Cast Line" : "Use Node"}</button>`);
  }).join("")}</div>` : `<p>No local gathering nodes. Travel to a zone with fishing/mining.</p>`);
  els.screen.querySelectorAll("[data-node]").forEach((b) => b.addEventListener("click", () => useNode(content.nodeBySlug[b.dataset.node])));
}

function startFishing(node) {
  state.fishing = { node, progress: 0, tension: 38, patience: 8, loot: weighted(node.loot_table.map((x) => [x.item, x.weight])) };
  addLog(`You cast into ${mapName(node.map_slug)}. Watch the line tension.`);
  assets.play("fish_tension");
  renderFishing();
}

function fishingAction(action) {
  const fish = state.fishing;
  if (!fish) return;
  if (action === "reel") { fish.progress += roll(12, 22); fish.tension += roll(12, 20); addLog("You reel hard and the catch draws closer."); }
  if (action === "wait") { fish.progress += roll(4, 10); fish.tension += roll(-5, 8); addLog("You wait for the bite to settle."); }
  if (action === "slacken") { fish.tension -= roll(12, 22); fish.progress -= roll(0, 5); addLog("You slacken the line to save the hook."); }
  fish.tension = Math.max(0, Math.min(100, fish.tension));
  fish.progress = Math.max(0, Math.min(100, fish.progress));
  fish.patience -= 1;
  assets.play("fish_tension");
  if (fish.tension >= 95) { addLog("The line snapped! The fish got away."); state.fishing = null; assets.play("ui_cancel"); return renderGathering(); }
  if (fish.patience <= 0 && fish.progress < 100) { addLog("The bite faded before you could land it."); state.fishing = null; assets.play("ui_cancel"); return renderGathering(); }
  if (fish.progress >= 100) {
    addItem(fish.loot);
    updateQuestProgress("gather", fish.loot);
    addLog(`Landed ${content.itemBySlug[fish.loot]?.name ?? fish.loot}!`);
    state.fishing = null;
    assets.play("fish_catch");
    return renderGathering();
  }
  renderFishing();
}

function renderFishing() {
  const fish = state.fishing;
  els.screen.innerHTML = `
    <div class="hero-art" style="--art: url('assets/images/gathering-placeholder.svg')"></div>
    <div class="hud-row">
      <div class="hud-box"><strong>Catch Progress</strong>${fish.progress}% landed<div class="bar"><span style="--value:${fish.progress}%"></span></div></div>
      <div class="hud-box"><strong>Line Tension</strong>${fish.tension}% strain<div class="bar enemy"><span style="--value:${fish.tension}%"></span></div></div>
      <div class="hud-box"><strong>Patience</strong>${fish.patience} turns before the bite fades</div>
    </div>
    <p>Balance progress against tension. Reel advances fastest, wait steadies the bite, slacken saves a dangerous line.</p>
    <div class="top-actions"><button data-fish="reel">Reel</button><button data-fish="wait">Wait</button><button data-fish="slacken">Slacken</button></div>`;
  els.screen.querySelectorAll("[data-fish]").forEach((b) => b.addEventListener("click", () => fishingAction(b.dataset.fish)));
}

function useNode(node) {
  if (node.kind.includes("fishing")) return startFishing(node);
  const loot = weighted(node.loot_table.map((x) => [x.item, x.weight]));
  addItem(loot);
  updateQuestProgress("gather", loot);
  addLog(`Gathered ${content.itemBySlug[loot]?.name ?? loot}.`);
  assets.play("ui_confirm");
  render();
}

function gearItems() { return state.inventory.filter((item) => ["weapon", "armor"].includes(item.kind) && item.data?.slot); }
function equippedItems() { return Object.values(state.equipment ?? {}).map((slug) => content.itemBySlug[slug]).filter(Boolean); }
function gearAttackBonus() { return equippedItems().reduce((total, item) => total + (item.data?.damage ?? 0), 0); }
function gearDefenseBonus() { return equippedItems().reduce((total, item) => total + (item.data?.defense ?? 0), 0); }
function canEquip(item) { return !item.data?.jobs || item.data.jobs.includes(state.character?.mainJob); }
function equipItem(slug) {
  const item = content.itemBySlug[slug];
  if (!item?.data?.slot) return addLog("That item cannot be equipped.");
  if (!canEquip(item)) return addLog(`${state.character.mainJob} cannot equip ${item.name}.`);
  state.equipment[item.data.slot] = item.slug;
  addLog(`Equipped ${item.name}.`);
  assets.play("ui_confirm");
  renderEquipment();
}
function unequipSlot(slot) {
  const item = content.itemBySlug[state.equipment?.[slot]];
  delete state.equipment[slot];
  addLog(`Unequipped ${item?.name ?? slot}.`);
  assets.play("ui_cancel");
  renderEquipment();
}

function renderEquipment() {
  els.title.textContent = "Equipment";
  if (!state.character) { els.screen.innerHTML = `<p>Create a character to manage equipment.</p>`; return; }
  const slots = ["main", "sub", "head", "body", "hands", "legs", "feet"];
  const equipped = slots.map((slot) => {
    const item = content.itemBySlug[state.equipment?.[slot]];
    return card(slot.toUpperCase(), item ? `${item.name}${item.data?.damage ? ` • DMG +${item.data.damage}` : ""}${item.data?.defense ? ` • DEF +${item.data.defense}` : ""}` : "Empty", [slot], item ? `<button data-unequip="${slot}">Unequip</button>` : "");
  }).join("");
  const available = gearItems().map((item) => card(item.name, `${item.kind} / ${item.data.slot}${item.data.damage ? ` • DMG +${item.data.damage}` : ""}${item.data.defense ? ` • DEF +${item.data.defense}` : ""}`, [canEquip(item) ? "usable" : "wrong job", item.slug], `<button data-equip="${item.slug}" ${canEquip(item) ? "" : "disabled"}>Equip</button>`)).join("");
  els.screen.innerHTML = `
    <div class="hero-art" style="--art: url('assets/images/hero-placeholder.svg')"></div>
    <div class="hud-row">
      <div class="hud-box"><strong>Attack Bonus</strong>+${gearAttackBonus()}</div>
      <div class="hud-box"><strong>Defense Bonus</strong>+${gearDefenseBonus()}</div>
    </div>
    <h2>Equipped</h2><div class="card-grid">${equipped}</div>
    <h2>Available Gear</h2>${available ? `<div class="card-grid">${available}</div>` : `<p>No equippable gear in inventory yet.</p>`}`;
  els.screen.querySelectorAll("[data-equip]").forEach((b) => b.addEventListener("click", () => equipItem(b.dataset.equip)));
  els.screen.querySelectorAll("[data-unequip]").forEach((b) => b.addEventListener("click", () => unequipSlot(b.dataset.unequip)));
}

function renderInventory() {
  els.title.textContent = "Inventory";
  if (!state.inventory.length) { els.screen.innerHTML = "<p>No items yet.</p>"; return; }
  const kinds = [...new Set(state.inventory.map((i) => i.kind))].sort();
  els.screen.innerHTML = kinds.map((k) => `<h2>${k}</h2><div class="card-grid">${state.inventory.filter((i) => i.kind === k).map((i) => card(i.name, `Quantity: ${i.qty}`, [i.slug])).join("")}</div>`).join("");
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
  const routes = { world: renderWorld, travel: renderTravel, npcs: renderNPCs, quests: renderQuestJournal, combat: renderCombat, gathering: renderGathering, inventory: renderInventory, equipment: renderEquipment, content: renderContent };
  (routes[state.screen] ?? renderWorld)();
}

async function boot() {
  content = await loadContentPack();
  assets = new AssetManager(defaultManifest);
  await assets.preload();
  document.querySelector("#newGameBtn").addEventListener("click", openCreator);
  document.querySelector("#saveBtn").addEventListener("click", save);
  document.querySelector("#loadBtn").addEventListener("click", load);
  document.querySelectorAll("[data-screen]").forEach((btn) => btn.addEventListener("click", () => setScreen(btn.dataset.screen)));
  addLog("Web engine loaded. Modular HTML/CSS/JS shell online.");
  render();
}
boot();
