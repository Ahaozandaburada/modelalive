import {
  daysUntil,
  effectiveStatus,
  loadRegistry,
  resolveAlias,
} from "./registry.js";
import type { AliveResult } from "./types.js";
import { ModelRetiredError, ModelUnknownError } from "./types.js";

export function alive(model: string, today = new Date()): AliveResult {
  const registry = loadRegistry();
  const queried = model.trim();
  const [canonical, aliased] = resolveAlias(queried, registry);
  const entry = registry.models[canonical];

  if (!entry) {
    return {
      model: canonical,
      queried_model: queried,
      canonical_model: canonical,
      aliased,
      alive: true,
      status: "unknown",
      confidence: "unknown",
      message: "Model not in registry — assumed alive.",
      registry_version: registry.version,
    };
  }

  const status = effectiveStatus(entry, today);
  const sourceKey = entry.source ?? "";
  const sourceMeta = registry.sources[sourceKey];
  const daysLeft = daysUntil(entry.retired_at, today);

  const base: AliveResult = {
    model: canonical,
    queried_model: queried,
    canonical_model: canonical,
    aliased,
    provider: entry.provider,
    deprecated_at: entry.deprecated_at,
    retired_at: entry.retired_at,
    replacement: entry.replacement ?? null,
    breaking_changes: entry.breaking_changes ?? [],
    migrate_url: entry.migrate_url,
    days_until_retirement: daysLeft,
    registry_version: registry.version,
    source_url: sourceMeta?.url,
    source_checked_at: sourceMeta?.checked_at,
    confidence: entry.source ? "verified" : "unknown",
    alive: status !== "retired",
    status: status as AliveResult["status"],
  };

  if (status === "retired") {
    const repl = entry.replacement ? ` Use '${entry.replacement}' instead.` : "";
    base.message = `Model '${canonical}' was retired.${repl}`;
    base.alive = false;
  } else if (status === "deprecated") {
    base.message = `Model '${canonical}' is deprecated.`;
    base.alive = true;
  }

  return base;
}

export function check(
  model: string,
  opts: { strictUnknown?: boolean; today?: Date } = {},
): AliveResult {
  const result = alive(model, opts.today);
  if (opts.strictUnknown && result.status === "unknown") {
    throw new ModelUnknownError(result);
  }
  if (result.status === "retired") {
    throw new ModelRetiredError(result);
  }
  return result;
}

export function resolve(model: string, today = new Date()): string {
  let current = model.trim();
  const visited = new Set<string>();

  for (let i = 0; i < 12; i++) {
    if (visited.has(current)) break;
    visited.add(current);
    const result = alive(current, today);
    if (result.status === "active" || result.status === "unknown") {
      return result.canonical_model ?? current;
    }
    if (!result.replacement) return result.canonical_model ?? current;
    const repl = alive(result.replacement, today);
    if (repl.status === "active") return result.replacement;
    current = result.replacement;
  }
  return current;
}

export function ensure(
  model: string,
  opts: { strictUnknown?: boolean; today?: Date } = {},
): string {
  const result = alive(model, opts.today);
  if (opts.strictUnknown && result.status === "unknown") {
    throw new ModelUnknownError(result);
  }
  if (result.status === "retired" && !result.replacement) {
    throw new ModelRetiredError(result);
  }
  return resolve(model, opts.today);
}

export * from "./types.js";
