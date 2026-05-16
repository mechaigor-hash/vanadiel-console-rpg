export const bySlug = (rows) => Object.fromEntries(rows.map((row) => [row.slug, row]));

export const slugify = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

export const roll = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

export function weighted(rows) {
  const total = rows.reduce((a, [, w]) => a + w, 0);
  let pick = roll(1, total);
  for (const [slug, weight] of rows) {
    pick -= weight;
    if (pick <= 0) return slug;
  }
  return rows[0][0];
}

export function card(title, body, badges = [], action = "") {
  return `<article class="card"><h3>${title}</h3><p>${body}</p><div class="badges">${badges.map((b) => `<span class="badge">${b}</span>`).join("")}</div>${action}</article>`;
}

export function addStats(stats, ...parts) {
  const total = Object.fromEntries(stats.map((s) => [s, 0]));
  for (const part of parts) for (const stat of stats) total[stat] += part?.[stat] ?? 0;
  return total;
}
