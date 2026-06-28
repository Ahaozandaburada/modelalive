import assert from "node:assert/strict";
import { alive, ensure, resolve } from "./index.js";

assert.equal(alive("claude-sonnet-4-20250514").status, "retired");
assert.equal(resolve("claude-sonnet-4-20250514"), "claude-sonnet-4-6");
assert.equal(ensure("claude-sonnet-4-20250514"), "claude-sonnet-4-6");
assert.equal(alive("claude-sonnet-4-6").status, "active");
console.log("modelalive js: ok");
