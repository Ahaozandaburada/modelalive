import assert from "node:assert/strict";
import {
  alive,
  ensure,
  gate,
  normalizeModel,
  resolve,
  resolveDetail,
} from "./index.js";

assert.equal(alive("claude-sonnet-4-20250514").status, "retired");
assert.equal(resolve("claude-sonnet-4-20250514"), "claude-sonnet-4-6");
assert.equal(ensure("claude-sonnet-4-20250514"), "claude-sonnet-4-6");
assert.equal(alive("claude-sonnet-4-6").status, "active");

const detail = resolveDetail("claude-opus-4-20250514");
assert.equal(detail.resolved, "claude-opus-4-8");
assert.ok(detail.breaking_changes.length >= 1);

assert.equal(normalizeModel("ft:gpt-4o-mini:org:foo:bar"), "gpt-4o-mini");
assert.equal(
  alive("anthropic.claude-sonnet-4-6-v1:0").provider,
  "bedrock",
);

const gated = gate("gemini-2.0-flash", (safe) => safe);
assert.equal(gated, "gemini-3.5-flash");

console.log("modelalive js: ok");
