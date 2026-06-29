import { alive } from "./alive.js";
import { normalizeModel } from "./normalize.js";
import {
  defaultStrictUnknown,
  defaultWarnDays,
  defaultWarnDeprecated,
} from "./settings.js";
import type { AliveResult, CheckOptions } from "./types.js";
import {
  ModelDeprecatedError,
  ModelExpiringSoonError,
  ModelRetiredError,
  ModelUnknownError,
} from "./types.js";

const MAX_DEPTH = 12;

export { alive } from "./alive.js";

export function check(model: string, opts: CheckOptions = {}): AliveResult {
  const strictUnknown = opts.strictUnknown ?? defaultStrictUnknown();
  const warnDeprecated = opts.warnDeprecated ?? defaultWarnDeprecated();
  const warnDays = opts.warnDays ?? defaultWarnDays();
  const today = opts.today;

  const result = alive(model, today);
  if (strictUnknown && result.status === "unknown") {
    throw new ModelUnknownError(result);
  }
  if (result.status === "retired") {
    throw new ModelRetiredError(result);
  }
  if (warnDeprecated && result.status === "deprecated") {
    throw new ModelDeprecatedError(result);
  }
  if (
    warnDays != null &&
    result.status === "deprecated" &&
    result.days_until_retirement != null &&
    result.days_until_retirement >= 0 &&
    result.days_until_retirement <= warnDays
  ) {
    throw new ModelExpiringSoonError(result);
  }
  return result;
}

export function checkMany(models: string[], today = new Date()): AliveResult[] {
  return models.map((m) => alive(m, today));
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

export function ensure(model: string, opts: CheckOptions = {}): string {
  const strictUnknown = opts.strictUnknown ?? defaultStrictUnknown();
  const warnDeprecated = opts.warnDeprecated ?? defaultWarnDeprecated();
  const warnDays = opts.warnDays ?? defaultWarnDays();
  const today = opts.today;

  const result = alive(model, today);
  if (strictUnknown && result.status === "unknown") {
    throw new ModelUnknownError(result);
  }
  if (result.status === "retired" && !result.replacement) {
    throw new ModelRetiredError(result);
  }
  if (warnDeprecated && result.status === "deprecated") {
    throw new ModelDeprecatedError(result);
  }
  if (
    warnDays != null &&
    result.status === "deprecated" &&
    result.days_until_retirement != null &&
    result.days_until_retirement >= 0 &&
    result.days_until_retirement <= warnDays
  ) {
    throw new ModelExpiringSoonError(result);
  }
  return resolve(model, today);
}

export function requireAlive(model: string, opts: CheckOptions = {}): string {
  check(model, opts);
  return model;
}

export function gate<T>(
  model: string,
  fn: (safeModel: string) => T,
  opts: CheckOptions = {},
): T {
  return fn(ensure(model, opts));
}

export * from "./types.js";
export { normalizeModel } from "./normalize.js";
export { listExpiring } from "./expiring.js";
export { scanPath } from "./scan.js";
export type { ScanFinding, ScanReport } from "./scan.js";
export {
  defaultStrictUnknown,
  defaultWarnDays,
  defaultWarnDeprecated,
} from "./settings.js";
export {
  assertStable,
  compareFingerprints,
  fingerprintFromDict,
  fingerprintFromResponses,
  listStablePrompts,
  responseDistance,
  StableShiftError,
} from "./stable.js";
export type {
  Fingerprint,
  PromptFingerprint,
  PromptShift,
  StabilityReport,
  StablePrompt,
} from "./stable.js";
