import { alive } from "./alive.js";
import type { AliveResult } from "./types.js";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const SKIP_DIRS = new Set([
  ".git",
  ".venv",
  "venv",
  "node_modules",
  "__pycache__",
  ".pytest_cache",
  "dist",
  "build",
  ".eggs",
]);

const EXTENSIONS = new Set([
  ".py",
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".json",
  ".yaml",
  ".yml",
  ".toml",
  ".env",
  ".md",
  ".sh",
]);

const PATTERNS: RegExp[] = [
  /['"](claude-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](gpt-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](gemini-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](o[0-9]-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](llama-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](grok-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](deepseek-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](mistral-[a-zA-Z0-9._-]{3,128})['"]/g,
  /['"](qwen[a-zA-Z0-9._-]{0,128})['"]/g,
  /['"](anthropic\.claude-[a-zA-Z0-9._:-]{3,128})['"]/g,
  /['"]((?:anthropic|openai|google|meta-llama|qwen|deepseek|mistral|x-ai)\/[a-zA-Z0-9._:-]{3,128})['"]/g,
  /model\s*[=:]\s*['"]([a-zA-Z0-9][a-zA-Z0-9._:/-]{2,127})['"]/g,
];

export interface ScanFinding {
  path: string;
  line: number;
  model: string;
  status: string;
  replacement?: string | null;
  alive: boolean;
}

export interface ScanReport {
  root: string;
  scannedFiles: number;
  findings: ScanFinding[];
}

function walk(dir: string, files: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const parts = path.split(/[/\\]/);
    if (parts.some((p) => SKIP_DIRS.has(p))) continue;
    const st = statSync(path);
    if (st.isDirectory()) walk(path, files);
    else files.push(path);
  }
  return files;
}

function shouldScan(path: string): boolean {
  if (path.endsWith(".min.js") || path.endsWith(".map")) return false;
  const ext = path.slice(path.lastIndexOf("."));
  return EXTENSIONS.has(ext) || path.endsWith("Dockerfile") || path.endsWith(".env");
}

export function scanPath(root: string, today = new Date()): ScanReport {
  const report: ScanReport = { root, scannedFiles: 0, findings: [] };
  const seen = new Set<string>();

  for (const path of walk(root)) {
    if (!shouldScan(path)) continue;
    let text: string;
    try {
      text = readFileSync(path, "utf-8");
    } catch {
      continue;
    }
    report.scannedFiles += 1;
    const lines = text.split(/\r?\n/);
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]!;
      for (const pattern of PATTERNS) {
        pattern.lastIndex = 0;
        let match: RegExpExecArray | null;
        while ((match = pattern.exec(line)) !== null) {
          const model = match[1]!;
          const key = `${path}:${i + 1}:${model}`;
          if (seen.has(key)) continue;
          seen.add(key);
          let result: AliveResult;
          try {
            result = alive(model, today);
          } catch {
            continue;
          }
          if (result.status === "active") continue;
          report.findings.push({
            path: path.startsWith(root) ? path.slice(root.length + 1) : path,
            line: i + 1,
            model,
            status: result.status,
            replacement: result.replacement,
            alive: result.alive,
          });
        }
      }
    }
  }
  return report;
}
