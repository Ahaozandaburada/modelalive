import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export class StableShiftError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "StableShiftError";
  }
}

export interface StablePrompt {
  id: string;
  message: string;
}

export interface PromptFingerprint {
  id: string;
  prompt: string;
  responses: string[];
  digest: string;
}

export interface Fingerprint {
  version: number;
  kind: string;
  model: string;
  endpoint?: string | null;
  created_at: string;
  samples_per_prompt: number;
  prompts: PromptFingerprint[];
}

export interface PromptShift {
  prompt_id: string;
  distance: number;
  baseline_digest: string;
  current_digest: string;
}

export interface StabilityReport {
  model: string;
  stable: boolean;
  mean_distance: number;
  max_distance: number;
  threshold: number;
  baseline_created_at?: string | null;
  prompt_shifts: PromptShift[];
}

function loadPromptsFile(): StablePrompt[] {
  const path = join(dirname(fileURLToPath(import.meta.url)), "..", "stable_prompts.json");
  const data = JSON.parse(readFileSync(path, "utf-8")) as { prompts: StablePrompt[] };
  return data.prompts;
}

export function listStablePrompts(): StablePrompt[] {
  return loadPromptsFile();
}

function trigramDistribution(text: string): Map<string, number> {
  const normalized = text.toLowerCase().split(/\s+/).join(" ");
  const out = new Map<string, number>();
  if (normalized.length < 3) {
    out.set(normalized || "∅", 1);
    return out;
  }
  for (let i = 0; i < normalized.length - 2; i++) {
    const tri = normalized.slice(i, i + 3);
    out.set(tri, (out.get(tri) ?? 0) + 1);
  }
  const total = [...out.values()].reduce((a, b) => a + b, 0);
  for (const [k, v] of out) out.set(k, v / total);
  return out;
}

function distributionDistance(a: Map<string, number>, b: Map<string, number>): number {
  const keys = new Set([...a.keys(), ...b.keys()]);
  let sum = 0;
  for (const k of keys) sum += Math.abs((a.get(k) ?? 0) - (b.get(k) ?? 0));
  return sum / 2;
}

export function responseDistance(left: string, right: string): number {
  if (left === right) return 0;
  return distributionDistance(trigramDistribution(left), trigramDistribution(right));
}

function digestResponses(responses: string[]): string {
  return createHash("sha256").update(responses.join("\n---\n")).digest("hex").slice(0, 16);
}

export function fingerprintFromResponses(
  model: string,
  responsesById: Record<string, string[]>,
  opts: { endpoint?: string | null; samplesPerPrompt?: number } = {},
): Fingerprint {
  const prompts: PromptFingerprint[] = loadPromptsFile().map((spec) => {
    const responses = responsesById[spec.id] ?? [];
    return {
      id: spec.id,
      prompt: spec.message,
      responses: [...responses],
      digest: digestResponses(responses),
    };
  });
  return {
    version: 1,
    kind: "modelalive-stable-fingerprint",
    model,
    endpoint: opts.endpoint ?? null,
    created_at: new Date().toISOString(),
    samples_per_prompt: opts.samplesPerPrompt ?? 1,
    prompts,
  };
}

export function fingerprintFromDict(data: Record<string, unknown>): Fingerprint {
  const prompts = ((data.prompts as Record<string, unknown>[]) ?? []).map((p) => ({
    id: String(p.id),
    prompt: String(p.prompt),
    responses: (p.responses as string[]) ?? [],
    digest: String(p.digest ?? digestResponses((p.responses as string[]) ?? [])),
  }));
  return {
    version: Number(data.version ?? 1),
    kind: String(data.kind ?? "modelalive-stable-fingerprint"),
    model: String(data.model),
    endpoint: (data.endpoint as string | null | undefined) ?? null,
    created_at: String(data.created_at ?? new Date().toISOString()),
    samples_per_prompt: Number(data.samples_per_prompt ?? 1),
    prompts,
  };
}

export function compareFingerprints(
  baseline: Fingerprint,
  current: Fingerprint,
  threshold = 0.25,
): StabilityReport {
  const byId = new Map(current.prompts.map((p) => [p.id, p]));
  const shifts: PromptShift[] = [];
  const distances: number[] = [];

  for (const base of baseline.prompts) {
    const cur = byId.get(base.id);
    if (!cur || !base.responses.length || !cur.responses.length) {
      shifts.push({
        prompt_id: base.id,
        distance: 1,
        baseline_digest: base.digest,
        current_digest: cur?.digest ?? "missing",
      });
      distances.push(1);
      continue;
    }
    let min = 1;
    for (const br of base.responses) {
      for (const cr of cur.responses) {
        min = Math.min(min, responseDistance(br, cr));
      }
    }
    distances.push(min);
    if (min > threshold) {
      shifts.push({
        prompt_id: base.id,
        distance: min,
        baseline_digest: base.digest,
        current_digest: cur.digest,
      });
    }
  }

  const mean = distances.length ? distances.reduce((a, b) => a + b, 0) / distances.length : 1;
  const max = distances.length ? Math.max(...distances) : 1;
  return {
    model: current.model,
    stable: mean <= threshold,
    mean_distance: mean,
    max_distance: max,
    threshold,
    baseline_created_at: baseline.created_at,
    prompt_shifts: shifts,
  };
}

export function assertStable(
  baseline: Fingerprint,
  current: Fingerprint,
  threshold = 0.25,
): StabilityReport {
  const report = compareFingerprints(baseline, current, threshold);
  if (!report.stable) {
    const shifted = report.prompt_shifts.map((s) => s.prompt_id).join(", ") || "aggregate";
    throw new StableShiftError(
      `Behavioral drift detected for ${current.model} (mean ${report.mean_distance.toFixed(3)} > ${threshold}). Shifted: ${shifted}`,
    );
  }
  return report;
}
