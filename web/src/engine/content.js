import { bySlug } from "./utils.js";

export async function loadContentPack(url = "core_content.json") {
  const content = await fetch(url).then((r) => r.json());
  content.mapBySlug = bySlug(content.maps);
  content.mobBySlug = bySlug(content.mobs);
  content.itemBySlug = bySlug(content.items);
  content.nodeBySlug = bySlug(content.gathering);
  return content;
}
