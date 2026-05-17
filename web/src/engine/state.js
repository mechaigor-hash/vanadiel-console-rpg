export const state = {
  screen: "world",
  character: null,
  inventory: [],
  activeQuests: [],
  completedQuests: [],
  combat: null,
  fishing: null,
};

export function saveGame(storage = localStorage) {
  storage.setItem("vanadielWebSave", JSON.stringify({ character: state.character, inventory: state.inventory, activeQuests: state.activeQuests, completedQuests: state.completedQuests }));
}

export function loadGame(storage = localStorage) {
  const raw = storage.getItem("vanadielWebSave");
  if (!raw) return false;
  const save = JSON.parse(raw);
  state.character = save.character;
  state.inventory = save.inventory ?? [];
  state.activeQuests = save.activeQuests ?? [];
  state.completedQuests = save.completedQuests ?? [];
  return true;
}
