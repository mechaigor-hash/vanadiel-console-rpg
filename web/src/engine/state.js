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

export function saveGame(storage = localStorage) {
  storage.setItem("vanadielWebSave", JSON.stringify(serializableState()));
}

export function loadGame(storage = localStorage) {
  const raw = storage.getItem("vanadielWebSave");
  if (!raw) return false;
  applySave(JSON.parse(raw));
  return true;
}
