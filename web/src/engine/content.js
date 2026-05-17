import { bySlug } from "./utils.js";

export async function loadContentPack(url = "core_content.json") {
  const content = await fetch(url).then((r) => r.json());
  content.mapBySlug = bySlug(content.maps);
  content.mobBySlug = bySlug(content.mobs);
  content.npcBySlug = bySlug(content.npcs);
  content.itemBySlug = bySlug(content.items);
  content.questBySlug = bySlug(content.quests ?? []);
  content.questsByStartNpc = (content.quests ?? []).reduce((rows, quest) => {
    rows[quest.start_npc_slug] ??= [];
    rows[quest.start_npc_slug].push(quest);
    return rows;
  }, {});
  content.nodeBySlug = bySlug(content.gathering);
  return content;
}
