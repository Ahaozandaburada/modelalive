import {
  daysUntil,
  effectiveStatus,
  loadRegistry,
  resolveAlias,
} from "./registry.js";
import { normalizeModel } from "./normalize.js";
import type { AliveResult } from "./types.js";
import { ModelRetiredError, ModelUnknownError } from "./types.js";

const MAX_DEPTH = 12;

export function alive(model: string, today = new Date()): AliveResult {
  const registry = loadRegistry();
  const queried = normalizeModel(model);
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
  return resolveDetail(model, today).resolved;
}

export interface ResolveDetail {
  queried_model: string;
  resolved: string;
  chain: string[];
  breaking_changes: string[];
}

export function resolveDetail(model: string, today = new Date()): ResolveDetail {
  let current = normalizeModel(model);
  const visited = new Set<string>();
  const chain: string[] = [];
  const breakingChanges: string[] = [];

  for (let i = 0; i < MAX_DEPTH; i++) {
    if (visited.has(current)) break;
    visited.add(current);
    chain.push(current);

    const result = alive(current, today);
    for (const change of result.breaking_changes ?? []) {
      if (!breakingChanges.includes(change)) breakingChanges.push(change);
    }

    if (result.status === "active" || result.status === "unknown") {
      return {
        queried_model: model,
        resolved: result.canonical_model ?? current,
        chain,
        breaking_changes: breakingChanges,
      };
    }
    if (!result.replacement) {
      return {
        queried_model: model,
        resolved: result.canonical_model ?? current,
        chain,
        breaking_changes: breakingChanges,
      };
    }

    const repl = alive(result.replacement, today);
    if (repl.status === "active") {
      for (const change of repl.breaking_changes ?? []) {
        if (!breakingChanges.includes(change)) breakingChanges.push(change);
      }
      return {
        queried_model: model,
        resolved: result.replacement,
        chain: [...chain, result.replacement],
        breaking_changes: breakingChanges,
      };
    }
    current = result.replacement;
  }

  return {
    queried_model: model,
    resolved: current,
    chain,
    breaking_changes: breakingChanges,
  };
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

export function gate<T>(
  model: string,
  fn: (safeModel: string) => T,
  opts: { strictUnknown?: boolean; today?: Date } = {},
): T {
  return fn(ensure(model, opts));
}

export * from "./types.js";
export { normalizeModel } from "./normalize.js";
