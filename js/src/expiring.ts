import { alive } from "./alive.js";
import { effectiveStatus, loadRegistry, parseDate } from "./registry.js";
import type { AliveResult } from "./types.js";

export function listExpiring(
  opts: { withinDays?: number; provider?: string; today?: Date } = {},
): AliveResult[] {
  const withinDays = opts.withinDays ?? 30;
  const today = opts.today ?? new Date();
  const registry = loadRegistry();
  const results: AliveResult[] = [];

  for (const [modelId, entry] of Object.entries(registry.models)) {
    if (opts.provider && entry.provider !== opts.provider) continue;
    const status = effectiveStatus(entry, today);
    if (status !== "deprecated" && status !== "retired") continue;
    const retiredAt = parseDate(entry.retired_at);
    if (!retiredAt) continue;
    const ms = retiredAt.getTime() - today.getTime();
    const daysLeft = Math.floor(ms / (1000 * 60 * 60 * 24));
    if (status === "retired" || daysLeft < 0) continue;
    if (daysLeft <= withinDays) {
      results.push(alive(modelId, today));
    }
  }

  return results.sort(
    (a, b) => (a.days_until_retirement ?? 9999) - (b.days_until_retirement ?? 9999),
  );
}
