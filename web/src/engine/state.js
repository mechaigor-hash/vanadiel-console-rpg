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

export function saveGame(storage = localStorage) {
  storage.setItem("vanadielWebSave", JSON.stringify({ character: state.character, inventory: state.inventory, equipment: state.equipment, activeQuests: state.activeQuests, completedQuests: state.completedQuests, questProgress: state.questProgress }));
}

export function loadGame(storage = localStorage) {
  const raw = storage.getItem("vanadielWebSave");
  if (!raw) return false;
  const save = JSON.parse(raw);
  state.character = save.character;
  state.inventory = save.inventory ?? [];
  state.equipment = save.equipment ?? {};
  state.activeQuests = save.activeQuests ?? [];
  state.completedQuests = save.completedQuests ?? [];
  state.questProgress = save.questProgress ?? {};
  return true;
}
