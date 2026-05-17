export const state = {
  screen: "world",
  character: null,
  inventory: [],
  equipment: {},
  activeQuests: [],
  completedQuests: [],
  questProgress: {},
  combat: null,
  fishing: null,
};

const LEGACY_SAVE_KEY = "vanadielWebSave";
const SLOT_PREFIX = "vanadielWebSave:";
const DEFAULT_SLOT = "autosave";

export function serializableState() {
  return {
    version: 1,
    exportedAt: new Date().toISOString(),
    character: state.character,
    inventory: state.inventory,
    equipment: state.equipment,
    activeQuests: state.activeQuests,
    completedQuests: state.completedQuests,
    questProgress: state.questProgress,
  };
}

export function applySave(save) {
  state.character = save.character ?? null;
  state.inventory = save.inventory ?? [];
  state.equipment = save.equipment ?? {};
  state.activeQuests = save.activeQuests ?? [];
  state.completedQuests = save.completedQuests ?? [];
  state.questProgress = save.questProgress ?? {};
}

export function saveSlotKey(slot = DEFAULT_SLOT) {
  return `${SLOT_PREFIX}${slot || DEFAULT_SLOT}`;
}

export function saveSlotSummary(slot, save) {
  return {
    slot,
    characterName: save.character?.name ?? "Empty",
    level: save.character?.level ?? 0,
    job: save.character?.mainJob ?? "No job",
    nation: save.character?.nation ?? "No nation",
    currentMap: save.character?.currentMap ?? "unknown",
    exportedAt: save.exportedAt ?? null,
  };
}

export function listSaveSlots(storage = localStorage) {
  const slots = [];
  for (let i = 0; i < storage.length; i += 1) {
    const key = storage.key(i);
    if (!key?.startsWith(SLOT_PREFIX)) continue;
    try {
      const slot = key.slice(SLOT_PREFIX.length);
      slots.push(saveSlotSummary(slot, JSON.parse(storage.getItem(key))));
    } catch {
      // Ignore corrupt slots in the browser save manager.
    }
  }
  if (storage.getItem(LEGACY_SAVE_KEY) && !storage.getItem(saveSlotKey(DEFAULT_SLOT))) {
    try { slots.push(saveSlotSummary(DEFAULT_SLOT, JSON.parse(storage.getItem(LEGACY_SAVE_KEY)))); } catch {}
  }
  return slots.sort((a, b) => (b.exportedAt ?? "").localeCompare(a.exportedAt ?? ""));
}

export function saveGame(slot = DEFAULT_SLOT, storage = localStorage) {
  storage.setItem(saveSlotKey(slot), JSON.stringify(serializableState()));
}

export function loadGame(slot = DEFAULT_SLOT, storage = localStorage) {
  const raw = storage.getItem(saveSlotKey(slot)) ?? (slot === DEFAULT_SLOT ? storage.getItem(LEGACY_SAVE_KEY) : null);
  if (!raw) return false;
  applySave(JSON.parse(raw));
  return true;
}

export function deleteSaveSlot(slot, storage = localStorage) {
  storage.removeItem(saveSlotKey(slot));
  if (slot === DEFAULT_SLOT) storage.removeItem(LEGACY_SAVE_KEY);
}
