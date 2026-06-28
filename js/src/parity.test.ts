import assert from "node:assert/strict";
import {
  alive,
  check,
  checkMany,
  defaultStrictUnknown,
  ensure,
  gate,
  listExpiring,
  normalizeModel,
  resolve,
  resolveDetail,
  scanPath,
} from "./index.js";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  ModelDeprecatedError,
  ModelRetiredError,
  ModelUnknownError,
} from "./types.js";

// Core lifecycle
assert.equal(alive("claude-sonnet-4-20250514").status, "retired");
assert.equal(resolve("claude-sonnet-4-20250514"), "claude-sonnet-4-6");
assert.equal(ensure("claude-sonnet-4-20250514"), "claude-sonnet-4-6");
assert.equal(alive("claude-sonnet-4-6").status, "active");

const detail = resolveDetail("claude-opus-4-20250514");
assert.equal(detail.resolved, "claude-opus-4-8");
assert.ok(detail.breaking_changes.length >= 1);

assert.equal(normalizeModel("ft:gpt-4o-mini:org:foo:bar"), "gpt-4o-mini");

// Bedrock host entry
const bedrock = alive("anthropic.claude-sonnet-4-6-v1:0");
assert.equal(bedrock.provider, "bedrock");
assert.equal(bedrock.status, "active");

// Azure host entry
const azure = alive("azure/gpt-4o");
assert.equal(azure.provider, "azure");

// OpenRouter crosswalk
assert.equal(resolve("anthropic/claude-sonnet-4-6"), "claude-sonnet-4-6");

const gated = gate("gemini-2.0-flash", (safe) => safe);
assert.equal(gated, "gemini-3.5-flash");

// checkMany
assert.equal(checkMany(["gpt-4o", "claude-sonnet-4-6"]).length, 2);

// listExpiring
const expiring = listExpiring({ withinDays: 365, provider: "anthropic" });
assert.ok(Array.isArray(expiring));

// scanPath
const dir = mkdtempSync(join(tmpdir(), "modelalive-"));
writeFileSync(join(dir, "app.py"), 'MODEL = "claude-sonnet-4-20250514"\n');
const scan = scanPath(dir);
assert.ok(scan.findings.length >= 1);

// Errors
assert.throws(() => check("totally-unknown-model-xyz", { strictUnknown: true }), ModelUnknownError);
assert.throws(() => check("claude-sonnet-4-20250514"), ModelRetiredError);

// env defaults (undefined when unset in test env)
assert.equal(typeof defaultStrictUnknown(), "boolean");

console.log("modelalive js parity: ok");
