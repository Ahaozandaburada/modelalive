import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { Registry, RegistryModel } from "./types.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

let _registry: Registry | null = null;

export function loadRegistry(): Registry {
  if (_registry) return _registry;
  const path = join(__dirname, "..", "registry.json");
  _registry = JSON.parse(readFileSync(path, "utf-8")) as Registry;
  return _registry;
}

export function parseDate(value?: string): Date | null {
  if (!value) return null;
  return new Date(`${value}T00:00:00Z`);
}

export function effectiveStatus(entry: RegistryModel, today = new Date()): string {
  const retired = parseDate(entry.retired_at);
  if (retired && retired <= today) return "retired";
  if (entry.status === "legacy") return "deprecated";
  return entry.status;
}

export function resolveAlias(model: string, registry = loadRegistry()): [string, boolean] {
  let current = model;
  const chain = [model];
  for (let i = 0; i < 8; i++) {
    const next = registry.aliases[current];
    if (!next) return [current, chain.length > 1];
    if (chain.includes(next)) break;
    chain.push(next);
    current = next;
  }
  return [current, chain.length > 1];
}

export function daysUntil(retiredAt: string | undefined, today = new Date()): number | null {
  const target = parseDate(retiredAt);
  if (!target) return null;
  const ms = target.getTime() - today.getTime();
  return Math.floor(ms / (1000 * 60 * 60 * 24));
}
