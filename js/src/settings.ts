/** Environment-driven defaults (parity with Python MODELALIVE_*). */

export function envFlag(name: string, defaultValue = false): boolean {
  const raw = (process.env[name] ?? "").trim().toLowerCase();
  if (!raw) return defaultValue;
  return ["1", "true", "yes", "on"].includes(raw);
}

export function defaultStrictUnknown(): boolean {
  return envFlag("MODELALIVE_STRICT");
}

export function defaultWarnDeprecated(): boolean {
  return envFlag("MODELALIVE_WARN_DEPRECATED");
}

export function defaultWarnDays(): number | undefined {
  const raw = (process.env["MODELALIVE_WARN_DAYS"] ?? "").trim();
  if (!raw) return undefined;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
}
